import type { GenerateRequest, GenerateResponse, JobStatus, LoginRequest, RegisterRequest, AuthResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// 认证相关 API
export async function login(params: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || '登录失败');
  }

  return response.json();
}

export async function register(params: RegisterRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || '注册失败');
  }

  return response.json();
}

export async function generateLessonPlan(
  params: GenerateRequest
): Promise<GenerateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to generate lesson plan');
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE_URL}/api/job/${jobId}/status`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to get job status');
  }

  return response.json();
}

export function getDownloadUrl(
  type: 'lesson' | 'tts' | 'ppt' | 'video',
  jobId: string
): string {
  return `${API_BASE_URL}/api/download/${type}/${jobId}`;
}