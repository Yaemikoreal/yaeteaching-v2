'use client';

import { useEffect, useRef, useReducer, useCallback } from 'react';
import type { JobStatus, ProgressMessage, TaskProgress } from '@/types';

interface UseWebSocketOptions {
  jobId: string | null;
  onProgress?: (message: ProgressMessage) => void;
  onComplete?: (status: JobStatus) => void;
  onError?: (error: string) => void;
}

interface UseWebSocketReturn {
  status: JobStatus | null;
  isConnected: boolean;
  error: string | null;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || '';

const INITIAL_TASKS: TaskProgress[] = [
  { type: 'lesson', status: 'pending', progress: 0 },
  { type: 'tts', status: 'pending', progress: 0 },
  { type: 'ppt', status: 'pending', progress: 0 },
  { type: 'video', status: 'pending', progress: 0 },
];

function createInitialStatus(jobId: string): JobStatus {
  return {
    jobId,
    status: 'pending',
    tasks: INITIAL_TASKS,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

type State = {
  status: JobStatus | null;
  isConnected: boolean;
  error: string | null;
};

type Action =
  | { type: 'CONNECTED'; jobId: string }
  | { type: 'DISCONNECTED' }
  | { type: 'ERROR'; error: string }
  | { type: 'PROGRESS'; message: ProgressMessage }
  | { type: 'RESET' };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'CONNECTED':
      return {
        ...state,
        isConnected: true,
        error: null,
        status: createInitialStatus(action.jobId),
      };
    case 'DISCONNECTED':
      return {
        ...state,
        isConnected: false,
      };
    case 'ERROR':
      return {
        ...state,
        error: action.error,
      };
    case 'PROGRESS':
      if (!state.status) {
        const tasks = INITIAL_TASKS.map((t) =>
          t.type === action.message.taskType
            ? {
                ...t,
                status: action.message.status,
                progress: action.message.progress,
                message: action.message.message,
                error: action.message.error,
                downloadUrl: action.message.downloadUrl,
              }
            : t
        );
        return {
          ...state,
          status: {
            jobId: action.message.jobId,
            status: action.message.status,
            tasks,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        };
      }
      const newTasks = state.status.tasks.map((task) =>
        task.type === action.message.taskType
          ? {
              ...task,
              status: action.message.status,
              progress: action.message.progress,
              message: action.message.message,
              error: action.message.error,
              downloadUrl: action.message.downloadUrl,
            }
          : task
      );
      return {
        ...state,
        status: {
          ...state.status,
          tasks: newTasks,
          updatedAt: new Date().toISOString(),
        },
      };
    case 'RESET':
      return {
        status: null,
        isConnected: false,
        error: null,
      };
    default:
      return state;
  }
}

export function useWebSocket({
  jobId,
  onProgress,
  onComplete,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [state, dispatch] = useReducer(reducer, {
    status: null,
    isConnected: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  // Use ref to track current tasks for completion check without triggering re-render
  const tasksRef = useRef<TaskProgress[]>(INITIAL_TASKS);
  // Store callbacks in refs to avoid dependency changes
  const onProgressRef = useRef(onProgress);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  // Update refs when callbacks change
  useEffect(() => {
    onProgressRef.current = onProgress;
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onProgress, onComplete, onError]);

  useEffect(() => {
    if (!jobId || !WS_BASE_URL) {
      wsRef.current?.close();
      wsRef.current = null;
      dispatch({ type: 'RESET' });
      return;
    }

    // Clear previous connection
    wsRef.current?.close();

    const wsUrl = `${WS_BASE_URL}/ws/job/${jobId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      dispatch({ type: 'CONNECTED', jobId });
    };

    ws.onmessage = (event) => {
      try {
        const message: ProgressMessage = JSON.parse(event.data);

        if (message.jobId !== jobId) return;

        onProgressRef.current?.(message);
        dispatch({ type: 'PROGRESS', message });

        // Update tasks ref for completion check
        tasksRef.current = tasksRef.current.map((task) =>
          task.type === message.taskType
            ? {
                ...task,
                status: message.status,
                progress: message.progress,
                message: message.message,
                error: message.error,
                downloadUrl: message.downloadUrl,
              }
            : task
        );

        // Check if all tasks are completed using ref instead of state
        if (message.status === 'completed') {
          const allCompleted = tasksRef.current.every(
            (t) => t.status === 'completed' || t.status === 'failed'
          );
          if (allCompleted) {
            onCompleteRef.current?.({
              jobId: message.jobId,
              status: 'completed',
              tasks: tasksRef.current,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            });
          }
        }

        if (message.status === 'failed' && message.error) {
          onErrorRef.current?.(message.error);
        }
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };

    ws.onerror = () => {
      dispatch({ type: 'ERROR', error: 'WebSocket connection error' });
      onErrorRef.current?.('WebSocket connection error');
    };

    ws.onclose = () => {
      dispatch({ type: 'DISCONNECTED' });
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [jobId]); // Only re-run when jobId changes

  return {
    status: state.status,
    isConnected: state.isConnected,
    error: state.error,
  };
}