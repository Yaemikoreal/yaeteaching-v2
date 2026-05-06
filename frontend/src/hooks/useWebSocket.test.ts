import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    // Mock close
  }

  static reset() {
    MockWebSocket.instances = [];
  }
}

// Setup WebSocket mock
vi.stubGlobal('WebSocket', MockWebSocket);

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.reset();
    vi.clearAllMocks();
  });

  it('should return initial state when jobId is null', () => {
    const { result } = renderHook(() => useWebSocket({ jobId: null }));

    expect(result.current.status).toBeNull();
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should create WebSocket connection when jobId is provided', () => {
    renderHook(() => useWebSocket({ jobId: 'test-job-123' }));

    expect(MockWebSocket.instances.length).toBe(1);
    expect(MockWebSocket.instances[0].url).toBe(
      'ws://localhost:8000/ws/job/test-job-123'
    );
  });

  it('should update isConnected when WebSocket opens', () => {
    const { result } = renderHook(() => useWebSocket({ jobId: 'test-job-123' }));

    act(() => {
      MockWebSocket.instances[0].onopen?.();
    });

    expect(result.current.isConnected).toBe(true);
  });

  it('should handle WebSocket error', () => {
    const onError = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({ jobId: 'test-job-123', onError })
    );

    act(() => {
      MockWebSocket.instances[0].onerror?.();
    });

    expect(result.current.error).toBe('WebSocket connection error');
    expect(onError).toHaveBeenCalledWith('WebSocket connection error');
  });

  it('should update status on progress message', () => {
    const onProgress = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({ jobId: 'test-job-123', onProgress })
    );

    // Open connection first
    act(() => {
      MockWebSocket.instances[0].onopen?.();
    });

    // Send progress message
    act(() => {
      MockWebSocket.instances[0].onmessage?.({
        data: JSON.stringify({
          jobId: 'test-job-123',
          taskType: 'lesson',
          status: 'in_progress',
          progress: 50,
          message: 'Generating lesson...',
        }),
      });
    });

    expect(onProgress).toHaveBeenCalled();
    expect(result.current.status?.tasks[0].status).toBe('in_progress');
    expect(result.current.status?.tasks[0].progress).toBe(50);
  });

  it('should close WebSocket when jobId changes', () => {
    const { rerender } = renderHook(
      ({ jobId }) => useWebSocket({ jobId }),
      { initialProps: { jobId: 'job-1' } }
    );

    expect(MockWebSocket.instances.length).toBe(1);

    rerender({ jobId: 'job-2' });

    // New connection should be created
    expect(MockWebSocket.instances.length).toBe(2);
  });
});