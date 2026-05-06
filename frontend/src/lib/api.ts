import type {
  GenerateRequest,
  GenerateResponse,
  JobStatus,
  HistoryListParams,
  HistoryListResponse,
  HistoryItem,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

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

// 历史记录 API
export async function getHistoryList(
  params: HistoryListParams = {}
): Promise<HistoryListResponse> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.limit) queryParams.set('limit', params.limit.toString());
  if (params.search) queryParams.set('search', params.search);
  if (params.startDate) queryParams.set('startDate', params.startDate);
  if (params.endDate) queryParams.set('endDate', params.endDate);
  if (params.starred) queryParams.set('starred', 'true');

  const response = await fetch(
    `${API_BASE_URL}/api/history?${queryParams.toString()}`
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to get history list');
  }

  return response.json();
}

export async function getHistoryDetail(historyId: string): Promise<HistoryItem> {
  const response = await fetch(`${API_BASE_URL}/api/history/${historyId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to get history detail');
  }

  return response.json();
}

export async function deleteHistory(historyId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/history/${historyId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to delete history');
  }
}

export async function toggleStar(historyId: string): Promise<HistoryItem> {
  const response = await fetch(
    `${API_BASE_URL}/api/history/${historyId}/star`,
    {
      method: 'POST',
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to toggle star');
  }

  return response.json();
}