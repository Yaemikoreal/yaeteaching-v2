// 任务状态类型
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// 产物类型
export type ProductType = 'lesson' | 'tts' | 'ppt' | 'video';

// 单个任务进度
export interface TaskProgress {
  type: ProductType;
  status: TaskStatus;
  progress: number; // 0-100
  message?: string;
  error?: string;
  downloadUrl?: string;
}

// 任务整体状态
export interface JobStatus {
  jobId: string;
  status: TaskStatus;
  tasks: TaskProgress[];
  createdAt: string;
  updatedAt: string;
}

// WebSocket 进度推送消息
export interface ProgressMessage {
  jobId: string;
  taskType: ProductType;
  status: TaskStatus;
  progress: number;
  message?: string;
  error?: string;
  downloadUrl?: string;
}

// 生成请求参数
export interface GenerateRequest {
  subject: string;
  grade: string;
  duration: number;
  topic: string;
  style?: string;
}

// 生成响应
export interface GenerateResponse {
  jobId: string;
  message: string;
}

// 教案版本类型
export interface LessonVersion {
  version: number;
  lessonJson: object;
  createdAt: string;
  description?: string;
}

// 教案版本列表响应
export interface LessonVersionsResponse {
  jobId: string;
  versions: LessonVersion[];
  currentVersion: number;
  maxVersions: number;
}

// 保存教案请求
export interface SaveLessonRequest {
  jobId: string;
  lessonJson: object;
  description?: string;
}

// 重新生成请求
export interface RegenerateRequest {
  jobId: string;
  sections: number[];
}

// 章节重新生成状态
export interface SectionRegenerationStatus {
  sectionId: number;
  title: string;
  status: TaskStatus;
  progress: number;
  error?: string;
}