# 视频生成流水线 DAG 架构设计

## 概述

本文档定义 YaeTeaching 项目视频生成流水线的 DAG（有向无环图）架构，整合教案、语音、PPT、视频合成服务。

**设计目标**：
- 支持并行/串行组合执行
- 每阶段任务可独立触发和监控
- 完善的错误处理和重试机制
- 资源估算和并发控制

---

## DAG 流程图

### Phase 2 视频生成流水线

```
                    ┌─────────────────────┐
                    │   start_pipeline    │
                    │   (初始化任务状态)   │
                    └─────────────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │   generate_lesson   │
                    │      (LLM 调用)     │
                    │    DeepSeek/OpenAI  │
                    └─────────────────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
             ▼                               ▼
    ┌─────────────────────┐       ┌─────────────────────┐
    │    generate_tts     │       │    generate_ppt     │
    │     (ChatTTS)       │       │    (python-pptx)    │
    │   按章节分段合成     │       │    多模板生成        │
    └─────────────────────┘       └─────────────────────┘
             │                               │
             └───────────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │   generate_video    │
                    │    (ffmpeg 合成)    │
                    │  音频+PPT+动画合成   │
                    └─────────────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │   final_package     │
                    │     (打包下载)      │
                    │  教案/音频/PPT/视频  │
                    └─────────────────────┘
```

### DAG 任务依赖关系

| 任务 | 依赖 | 执行模式 | 并发约束 |
|------|------|----------|----------|
| start_pipeline | 无 | 同步初始化 | 无 |
| generate_lesson | start_pipeline | 串行（LLM 单请求） | rate_limit=10/m |
| generate_tts | generate_lesson | 并行执行 | rate_limit=5/m |
| generate_ppt | generate_lesson | 并行执行 | 无限制 |
| generate_video | generate_tts + generate_ppt | 串行（资源密集） | rate_limit=2/m |
| final_package | generate_video | 串行（IO） | 无限制 |

---

## Celery Canvas 任务编排

### 核心设计

使用 Celery Canvas 的 `chain`、`group`、`chord` 实现 DAG：

```python
from celery import chain, group, chord

# 定义任务签名
lesson_sig = generate_lesson_task.s(job_id, request_data)
tts_sig = generate_tts_task.s(job_id)
ppt_sig = generate_ppt_task.s(job_id)
video_sig = generate_video_task.s(job_id)
package_sig = final_package_task.s(job_id)

# 构建 DAG 流程
# chord: 并行执行 group 后执行 callback
pipeline = chain(
    lesson_sig,
    chord(
        header=group([tts_sig, ppt_sig]),  # 并行执行
        body=video_sig                      # 完成后执行
    ),
    package_sig
)

# 触发执行
pipeline.apply_async()
```

### 任务签名设计

每个任务使用签名（signature）支持独立触发：

```python
# 独立触发单个任务（用于重试/增量生成）
generate_lesson_task.apply_async(args=[job_id, request_data])

# 独立触发 PPT（lesson 已存在）
generate_ppt_task.apply_async(args=[job_id, lesson_json])

# 独立触发视频合成（tts + ppt 已存在）
generate_video_task.apply_async(args=[job_id, audio_files, ppt_path])
```

---

## 任务定义规范

### 任务装饰器配置

```python
@shared_task(
    bind=True,
    autoretry_for=(Exception,),      # 自动重试的异常类型
    max_retries=3,                   # 最大重试次数
    retry_backoff=True,              # 指数退避
    retry_backoff_max=60,            # 最大退避时间 60s
    retry_jitter=True,               # 随机抖动避免雪崩
    rate_limit='10/m',               # 速率限制
    time_limit=3600,                 # 硬超时 1h
    soft_time_limit=3000,            # 软超时 50min
    acks_late=True,                  # 任务完成后确认
    reject_on_worker_lost=True,      # worker 丢失时拒绝
)
def generate_lesson_task(self, job_id: str, request_data: dict):
    # 任务实现...
```

### 各任务配置参数

| 任务 | max_retries | retry_backoff | rate_limit | time_limit |
|------|-------------|---------------|------------|------------|
| generate_lesson | 3 | True (2^n s) | 10/m | 300s |
| generate_tts | 3 | True (2^n s) | 5/m | 600s |
| generate_ppt | 2 | True | 无限制 | 120s |
| generate_video | 3 | True (2^n s) | 2/m | 1800s |
| final_package | 2 | True | 无限制 | 60s |

---

## 错误处理机制

### 错误分类与策略

| 错误类型 | 处理策略 | 重试 | 通知 |
|----------|----------|------|------|
| API 调用失败 (LLM/TTS) | 自动重试 + 降级 | 最多 3 次 | WebSocket 推送 |
| 资源不足 (OOM/CPU) | 任务拒绝 + 等待 | 不重试 | 状态 paused |
| 数据格式错误 | 任务失败 + 日志 | 不重试 | 错误详情 |
| 网络超时 | 自动重试 | 最多 3 次 | 进度更新 |
| Worker 丢失 | 任务重新入队 | 自动 | 状态 pending |

### 错误回调设计

```python
@shared_task(bind=True)
def error_handler(self, request, exc, traceback):
    """全局错误处理回调."""
    job_id = request.args[0]

    # 记录错误详情
    error_info = {
        'task_name': request.name,
        'exception': str(exc),
        'traceback': traceback,
        'timestamp': datetime.utcnow().isoformat()
    }

    # 更新任务状态
    _update_progress_sync(
        job_id,
        ProductType.lesson,  # 根据任务类型动态获取
        TaskStatus.failed,
        progress=0,
        error=f"{exc.__class__.__name__}: {str(exc)}"
    )

    # WebSocket 推送错误
    from app.websocket import broadcast_error
    broadcast_error(job_id, error_info)

    # 可选：发送到错误队列供人工处理
    log_error_task.apply_async(args=[job_id, error_info])

# 使用错误回调
pipeline.apply_async(link_error=error_handler.s())
```

### 服务降级策略

```python
def generate_lesson_task(self, job_id, request_data):
    try:
        # 优先 DeepSeek
        response = _call_deepseek(prompt)
    except DeepSeekAPIError:
        # 降级到 OpenAI
        self.update_state(state='RETRY', meta={'reason': 'DeepSeek failed, fallback to OpenAI'})
        response = _call_openai(prompt)
    except OpenAIAPIError:
        # 最终降级到模板
        self.update_state(state='FALLBACK', meta={'reason': 'All LLM failed, using template'})
        response = _generate_template(request_data)

    return response
```

---

## 并发控制策略

### Worker 配置

```python
# celery/config.py 更新
celery_app.conf.update(
    # Worker 并发
    worker_concurrency=4,              # 4 个并发进程
    worker_prefetch_multiplier=1,      # 每次只取 1 个任务

    # 任务路由
    task_routes={
        'celery.tasks.generate_lesson_task': {'queue': 'llm'},
        'celery.tasks.generate_tts_task': {'queue': 'tts'},
        'celery.tasks.generate_video_task': {'queue': 'video'},
    },

    # 资源限制
    worker_max_tasks_per_child=100,    # 防止内存泄漏
)
```

### 启动多个 Worker

```bash
# LLM 任务队列（低并发）
celery -A celery.tasks worker -Q llm --concurrency=2 --loglevel=info -n llm_worker@%h

# TTS 任务队列（中并发）
celery -A celery.tasks worker -Q tts --concurrency=4 --loglevel=info -n tts_worker@%h

# 视频合成队列（低并发，资源密集）
celery -A celery.tasks worker -Q video --concurrency=2 --loglevel=info -n video_worker@%h

# 默认队列（PPT、打包等）
celery -A celery.tasks worker -Q default --concurrency=8 --loglevel=info -n default_worker@%h
```

---

## 资源估算

### 单任务资源消耗

| 任务 | CPU | 内存 | 网络 | 存储 | 预估耗时 |
|------|-----|------|------|------|----------|
| generate_lesson | 低 | 100MB | API调用 | 无 | 10-30s |
| generate_tts | 中 | 500MB | API调用 | 音频文件 | 60-180s |
| generate_ppt | 低 | 100MB | 无 | PPT文件 | 5-15s |
| generate_video | 高 | 2GB | 无 | 视频文件 | 300-600s |
| final_package | 低 | 100MB | 无 | ZIP包 | 5-10s |

### 并发容量规划

基于 4 Worker 配置：

| 队列 | Worker 数 | 并发限制 | 吞吐量（估算） |
|------|-----------|----------|----------------|
| llm | 2 | 10/m | 20 请求/分钟 |
| tts | 4 | 5/m | 20 请求/分钟 |
| video | 2 | 2/m | 4 请求/分钟 |

---

## 监控与可观测性

### Flower 监控

```bash
# 启动 Flower 监控
celery -A celery.tasks flower --port=5555

# 访问 http://localhost:5555
```

### 关键指标

| 指标 | 类型 | 采集方式 | 告警阈值 |
|------|------|----------|----------|
| task_success_rate | 成功率 | Flower | < 90% |
| task_avg_latency | 平均延迟 | Flower | > 60s |
| queue_length | 队列长度 | Redis | > 50 |
| worker_status | Worker 状态 | Flower | offline |

### 日志规范

```python
import structlog

logger = structlog.get_logger()

@shared_task(bind=True)
def generate_lesson_task(self, job_id, request_data):
    logger.info(
        "task_started",
        task_id=self.request.id,
        job_id=job_id,
        task_name="generate_lesson"
    )

    try:
        result = _generate(request_data)
        logger.info(
            "task_completed",
            task_id=self.request.id,
            job_id=job_id,
            duration=result.get('duration')
        )
        return result
    except Exception as e:
        logger.error(
            "task_failed",
            task_id=self.request.id,
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise
```

---

## API 扩展设计

### 新增端点支持独立任务触发

```python
# app/router.py 新增

@app.post("/api/job/{job_id}/trigger/{task_type}")
async def trigger_single_task(job_id: str, task_type: ProductType):
    """独立触发单个任务（用于重试或增量生成）."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # 根据任务类型触发
    if task_type == ProductType.lesson:
        generate_lesson_task.apply_async(args=[job_id, job.request_data])
    elif task_type == ProductType.tts:
        lesson_json = job.lesson_json  # 从存储获取
        generate_tts_task.apply_async(args=[job_id, lesson_json])
    elif task_type == ProductType.ppt:
        lesson_json = job.lesson_json
        generate_ppt_task.apply_async(args=[job_id, lesson_json])
    elif task_type == ProductType.video:
        # 需要确保 TTS + PPT 已完成
        generate_video_task.apply_async(args=[job_id])

    return {"status": "triggered", "task_type": task_type}
```

---

## 实现优先级

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | DAG 流程改造 | 使用 chord/group/chain |
| P0 | 错误处理机制 | autoretry + error_handler |
| P1 | 任务路由配置 | 多队列 Worker |
| P1 | 资源估算文档 | 容量规划参考 |
| P2 | Flower 监控 | 生产环境部署 |
| P2 | 独立任务触发 API | 增量生成支持 |

---

## 附录：Celery Canvas 语法参考

### chain（串行）

```python
chain(task1.s(), task2.s(), task3.s())
# task1 → task2 → task3
```

### group（并行）

```python
group(task1.s(), task2.s(), task3.s())
# task1, task2, task3 同时执行
```

### chord（并行 + 回调）

```python
chord(
    header=group([task1.s(), task2.s()]),
    body=callback.s()
)
# task1, task2 并行执行，完成后执行 callback
```

### signature（签名）

```python
# 创建任务签名（延迟执行）
sig = task.s(args)
sig.apply_async()  # 立即执行
sig.apply_async(countdown=10)  # 10秒后执行
```

---

**文档版本**: v1.0
**创建日期**: 2026-05-06
**作者**: 白厄