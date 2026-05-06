"""Celery configuration with task routing."""
from celery import Celery
from config.settings import settings

celery_app = Celery(
    "yaeteaching",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,  # Process one task at a time

    # Worker settings
    worker_max_tasks_per_child=100,  # Prevent memory leaks

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Task routing by queue
    task_routes={
        'celery.tasks.generate_lesson_task': {
            'queue': 'llm',
            'rate_limit': '10/m',
        },
        'celery.tasks.generate_tts_task': {
            'queue': 'tts',
            'rate_limit': '5/m',
        },
        'celery.tasks.generate_ppt_task': {
            'queue': 'default',
        },
        'celery.tasks.generate_video_task': {
            'queue': 'video',
            'rate_limit': '2/m',
        },
        'celery.tasks.final_package_task': {
            'queue': 'default',
        },
        'celery.tasks.error_handler': {
            'queue': 'default',
        },
    },

    # Task default queue
    task_default_queue='default',

    # Priority settings
    task_queue_priority={
        'llm': 3,      # High priority
        'tts': 2,      # Medium priority
        'video': 1,    # Low priority (resource intensive)
        'default': 0,  # Base priority
    },
)


def get_worker_startup_info():
    """Get recommended worker startup commands."""
    return """
Recommended Worker Startup Commands:

# LLM queue (low concurrency, rate-limited)
celery -A celery.tasks worker -Q llm --concurrency=2 --loglevel=info -n llm_worker@%h

# TTS queue (medium concurrency)
celery -A celery.tasks worker -Q tts --concurrency=4 --loglevel=info -n tts_worker@%h

# Video queue (low concurrency, resource intensive)
celery -A celery.tasks worker -Q video --concurrency=2 --loglevel=info -n video_worker@%h

# Default queue (PPT, packaging, error handling)
celery -A celery.tasks worker -Q default --concurrency=8 --loglevel=info -n default_worker@%h

# Flower monitoring (optional)
celery -A celery.tasks flower --port=5555
"""