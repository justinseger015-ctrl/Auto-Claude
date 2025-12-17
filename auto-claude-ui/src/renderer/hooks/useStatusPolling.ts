/**
 * Real-time status polling hook for task board updates.
 *
 * Provides automatic polling of task status with configurable intervals.
 * Updates occur within 2 seconds when task status changes (per AC #1).
 *
 * Story 3-4: Real-Time Board Updates (AC: #1, #2)
 */

import { useEffect, useRef, useCallback } from 'react';
import { useTaskStore, loadTasks } from '../stores/task-store';

export interface UseStatusPollingOptions {
  /** Polling interval in milliseconds (default: 2000ms per AC #1) */
  interval?: number;
  /** Whether polling is enabled (default: true) */
  enabled?: boolean;
  /** Only poll when there are active (in_progress) tasks */
  onlyWhenActive?: boolean;
  /** Callback when tasks are refreshed */
  onRefresh?: () => void;
}

/**
 * Hook for polling task status updates in real-time.
 *
 * @example
 * ```tsx
 * // Basic usage - polls every 2 seconds
 * useStatusPolling(projectId);
 *
 * // With options
 * useStatusPolling(projectId, {
 *   interval: 1000,
 *   onlyWhenActive: true,
 *   onRefresh: () => console.log('Tasks refreshed')
 * });
 * ```
 */
export function useStatusPolling(
  projectId: string | null,
  options: UseStatusPollingOptions = {}
): {
  isPolling: boolean;
  lastPollTime: Date | null;
  forceRefresh: () => Promise<void>;
} {
  const {
    interval = 2000,
    enabled = true,
    onlyWhenActive = false,
    onRefresh,
  } = options;

  const tasks = useTaskStore((state) => state.tasks);
  const isLoadingRef = useRef(false);
  const lastPollTimeRef = useRef<Date | null>(null);
  const intervalIdRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Check if there are any active tasks
  const hasActiveTasks = tasks.some(
    (task) => task.status === 'in_progress' || task.status === 'ai_review'
  );

  // Determine if polling should be active
  const shouldPoll = Boolean(enabled && projectId && (!onlyWhenActive || hasActiveTasks));

  // Force refresh function
  const forceRefresh = useCallback(async () => {
    if (!projectId || isLoadingRef.current) return;

    isLoadingRef.current = true;
    try {
      await loadTasks(projectId);
      lastPollTimeRef.current = new Date();
      onRefresh?.();
    } finally {
      isLoadingRef.current = false;
    }
  }, [projectId, onRefresh]);

  // Set up polling interval
  useEffect(() => {
    if (!shouldPoll) {
      // Clear any existing interval
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
      return;
    }

    // Do an initial load
    forceRefresh();

    // Set up interval
    intervalIdRef.current = setInterval(() => {
      forceRefresh();
    }, interval);

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [shouldPoll, interval, forceRefresh]);

  return {
    isPolling: shouldPoll,
    lastPollTime: lastPollTimeRef.current,
    forceRefresh,
  };
}

export default useStatusPolling;
