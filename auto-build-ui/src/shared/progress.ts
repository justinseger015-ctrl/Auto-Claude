/**
 * Shared progress calculation utilities
 * Used by both main and renderer processes
 */
import type { Chunk, ChunkStatus } from './types';

/**
 * Calculate progress percentage from chunks
 * @param chunks Array of chunks with status
 * @returns Progress percentage (0-100)
 */
export function calculateProgress(chunks: { status: string }[]): number {
  if (chunks.length === 0) return 0;
  const completed = chunks.filter((c) => c.status === 'completed').length;
  return Math.round((completed / chunks.length) * 100);
}

/**
 * Count chunks by status
 * @param chunks Array of chunks
 * @returns Object with counts per status
 */
export function countChunksByStatus(chunks: Chunk[]): Record<ChunkStatus, number> {
  return {
    pending: chunks.filter((c) => c.status === 'pending').length,
    in_progress: chunks.filter((c) => c.status === 'in_progress').length,
    completed: chunks.filter((c) => c.status === 'completed').length,
    failed: chunks.filter((c) => c.status === 'failed').length
  };
}

/**
 * Determine overall status from chunk statuses
 * @param chunks Array of chunks
 * @returns Overall status string
 */
export function determineOverallStatus(
  chunks: { status: string }[]
): 'not_started' | 'in_progress' | 'completed' | 'failed' {
  if (chunks.length === 0) return 'not_started';

  const hasCompleted = chunks.some((c) => c.status === 'completed');
  const hasFailed = chunks.some((c) => c.status === 'failed');
  const hasInProgress = chunks.some((c) => c.status === 'in_progress');
  const allCompleted = chunks.every((c) => c.status === 'completed');
  const allPending = chunks.every((c) => c.status === 'pending');

  if (allCompleted) return 'completed';
  if (hasFailed) return 'failed';
  if (hasInProgress || hasCompleted) return 'in_progress';
  if (allPending) return 'not_started';

  return 'in_progress';
}

/**
 * Format progress as display string
 * @param completed Number of completed chunks
 * @param total Total number of chunks
 * @returns Formatted string like "3/5 chunks"
 */
export function formatProgressString(completed: number, total: number): string {
  if (total === 0) return 'No chunks';
  return `${completed}/${total} chunks`;
}

/**
 * Calculate estimated remaining time based on progress
 * @param startTime Start time of the task
 * @param progress Current progress percentage (0-100)
 * @returns Estimated remaining time in milliseconds, or null if cannot estimate
 */
export function estimateRemainingTime(
  startTime: Date,
  progress: number
): number | null {
  if (progress <= 0 || progress >= 100) return null;

  const elapsed = Date.now() - startTime.getTime();
  const estimatedTotal = (elapsed / progress) * 100;
  const remaining = estimatedTotal - elapsed;

  return Math.max(0, Math.round(remaining));
}
