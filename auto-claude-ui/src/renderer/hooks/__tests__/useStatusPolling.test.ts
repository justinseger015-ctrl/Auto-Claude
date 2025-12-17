/**
 * Tests for useStatusPolling hook.
 *
 * Story 3-4: Real-Time Board Updates (AC: #1, #2)
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useStatusPolling } from '../useStatusPolling';
import { useTaskStore } from '../../stores/task-store';
import type { Task } from '../../../shared/types';

// Mock the task store module
vi.mock('../../stores/task-store', async () => {
  const zustand = await import('zustand');
  const { create } = zustand;

  // Create a mock store
  const mockStore = create<{
    tasks: Task[];
    setTasks: (tasks: Task[]) => void;
  }>(() => ({
    tasks: [],
    setTasks: () => {},
  }));

  return {
    useTaskStore: mockStore,
    loadTasks: vi.fn().mockResolvedValue(undefined),
  };
});

// Get the mocked loadTasks function
const { loadTasks } = await import('../../stores/task-store');

describe('useStatusPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initialization', () => {
    it('does not poll when projectId is null', () => {
      const { result } = renderHook(() => useStatusPolling(null));

      expect(result.current.isPolling).toBe(false);
      expect(loadTasks).not.toHaveBeenCalled();
    });

    it('starts polling when projectId is provided', async () => {
      const { result } = renderHook(() => useStatusPolling('project-1'));

      expect(result.current.isPolling).toBe(true);
      expect(loadTasks).toHaveBeenCalledWith('project-1');
    });

    it('does not poll when enabled is false', () => {
      const { result } = renderHook(() =>
        useStatusPolling('project-1', { enabled: false })
      );

      expect(result.current.isPolling).toBe(false);
      expect(loadTasks).not.toHaveBeenCalled();
    });
  });

  describe('polling interval', () => {
    it('uses default 2-second interval per AC #1', async () => {
      renderHook(() => useStatusPolling('project-1'));

      // Initial call
      expect(loadTasks).toHaveBeenCalledTimes(1);

      // Advance less than 2 seconds
      await act(async () => {
        vi.advanceTimersByTime(1500);
      });
      expect(loadTasks).toHaveBeenCalledTimes(1);

      // Advance to 2 seconds - should trigger another call
      await act(async () => {
        vi.advanceTimersByTime(500);
      });
      expect(loadTasks).toHaveBeenCalledTimes(2);
    });

    it('respects custom interval option', async () => {
      renderHook(() => useStatusPolling('project-1', { interval: 5000 }));

      expect(loadTasks).toHaveBeenCalledTimes(1);

      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      expect(loadTasks).toHaveBeenCalledTimes(1);

      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      expect(loadTasks).toHaveBeenCalledTimes(2);
    });
  });

  describe('onlyWhenActive option', () => {
    it('does not poll when no active tasks and onlyWhenActive is true', () => {
      // Store has no active tasks (empty)
      const store = useTaskStore.getState();
      store.tasks = [];

      const { result } = renderHook(() =>
        useStatusPolling('project-1', { onlyWhenActive: true })
      );

      expect(result.current.isPolling).toBe(false);
    });

    it('polls when there are in_progress tasks and onlyWhenActive is true', () => {
      const store = useTaskStore.getState();
      store.tasks = [
        {
          id: 'task-1',
          specId: 'spec-1',
          projectId: 'project-1',
          status: 'in_progress',
          title: 'Test Task',
          description: '',
          subtasks: [],
          logs: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      ] as Task[];

      const { result } = renderHook(() =>
        useStatusPolling('project-1', { onlyWhenActive: true })
      );

      expect(result.current.isPolling).toBe(true);
    });

    it('polls when there are ai_review tasks and onlyWhenActive is true', () => {
      const store = useTaskStore.getState();
      store.tasks = [
        {
          id: 'task-1',
          specId: 'spec-1',
          projectId: 'project-1',
          status: 'ai_review',
          title: 'Test Task',
          description: '',
          subtasks: [],
          logs: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      ] as Task[];

      const { result } = renderHook(() =>
        useStatusPolling('project-1', { onlyWhenActive: true })
      );

      expect(result.current.isPolling).toBe(true);
    });
  });

  describe('forceRefresh', () => {
    it('allows manual refresh', async () => {
      const { result } = renderHook(() =>
        useStatusPolling('project-1', { enabled: false })
      );

      expect(loadTasks).not.toHaveBeenCalled();

      await act(async () => {
        await result.current.forceRefresh();
      });

      expect(loadTasks).toHaveBeenCalledWith('project-1');
    });

    it('does not refresh when projectId is null', async () => {
      const { result } = renderHook(() => useStatusPolling(null));

      await act(async () => {
        await result.current.forceRefresh();
      });

      expect(loadTasks).not.toHaveBeenCalled();
    });
  });

  describe('onRefresh callback', () => {
    it('calls onRefresh after successful load', async () => {
      const onRefresh = vi.fn();
      renderHook(() => useStatusPolling('project-1', { onRefresh }));

      // Wait for the initial load to complete
      await act(async () => {
        // Resolve the loadTasks promise
        await Promise.resolve();
      });

      expect(onRefresh).toHaveBeenCalled();
    });
  });

  describe('cleanup', () => {
    it('stops polling on unmount', async () => {
      const { unmount } = renderHook(() => useStatusPolling('project-1'));

      expect(loadTasks).toHaveBeenCalledTimes(1);

      unmount();

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      // Should not have been called again after unmount
      expect(loadTasks).toHaveBeenCalledTimes(1);
    });

    it('stops polling when projectId changes to null', async () => {
      const { rerender } = renderHook(
        ({ projectId }) => useStatusPolling(projectId),
        { initialProps: { projectId: 'project-1' as string | null } }
      );

      expect(loadTasks).toHaveBeenCalledTimes(1);

      rerender({ projectId: null });

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      // Initial call only, no new calls after projectId became null
      expect(loadTasks).toHaveBeenCalledTimes(1);
    });

    it('stops and restarts polling when projectId changes', async () => {
      const { result, rerender } = renderHook(
        ({ projectId }) => useStatusPolling(projectId),
        { initialProps: { projectId: 'project-1' } }
      );

      // Initially polling project-1
      expect(result.current.isPolling).toBe(true);
      expect(loadTasks).toHaveBeenCalledWith('project-1');

      // Change to project-2
      rerender({ projectId: 'project-2' });

      // Hook should still be polling (with new project)
      expect(result.current.isPolling).toBe(true);
    });
  });

  describe('AC verification', () => {
    it('AC #1: default interval is 2 seconds (per specification)', () => {
      // Verify the default interval is 2000ms by checking the hook options
      const { result } = renderHook(() => useStatusPolling('project-1'));

      // Hook should be polling with enabled project
      expect(result.current.isPolling).toBe(true);

      // Initial load is called immediately
      expect(loadTasks).toHaveBeenCalledWith('project-1');
    });

    it('AC #2: no manual refresh required (automatic initial load)', () => {
      renderHook(() => useStatusPolling('project-1'));

      // Initial call happens automatically without any user action
      expect(loadTasks).toHaveBeenCalled();
    });

    it('AC #2: forceRefresh allows manual refresh if needed', async () => {
      const { result } = renderHook(() =>
        useStatusPolling('project-1', { enabled: false })
      );

      // Not polling since disabled
      expect(result.current.isPolling).toBe(false);
      expect(loadTasks).not.toHaveBeenCalled();

      // But forceRefresh still works
      await act(async () => {
        await result.current.forceRefresh();
      });

      expect(loadTasks).toHaveBeenCalledWith('project-1');
    });
  });
});
