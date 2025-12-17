/**
 * Status color mappings for UnifiedStatus.
 *
 * Provides consistent visual styling for task statuses across all views.
 *
 * Story 3.3: Unified Status Badge Mapping (AC: #1)
 */

import { UnifiedStatus } from '../types/status';

/**
 * Color configuration for each status.
 */
export interface StatusColorConfig {
  /** Background color class */
  bg: string;
  /** Text color class */
  text: string;
  /** Border color class */
  border: string;
}

/**
 * Status color mappings matching the design spec:
 * - PENDING → gray
 * - IN_PROGRESS → blue
 * - REVIEW → yellow
 * - BLOCKED → red
 * - COMPLETED → green
 * - FAILED → red with error styling
 */
export const STATUS_COLORS: Record<UnifiedStatus, StatusColorConfig> = {
  [UnifiedStatus.PENDING]: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-300 dark:border-gray-600',
  },
  [UnifiedStatus.IN_PROGRESS]: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-300 dark:border-blue-700',
  },
  [UnifiedStatus.REVIEW]: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    text: 'text-yellow-700 dark:text-yellow-400',
    border: 'border-yellow-300 dark:border-yellow-700',
  },
  [UnifiedStatus.BLOCKED]: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-300 dark:border-red-700',
  },
  [UnifiedStatus.COMPLETED]: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-700 dark:text-green-400',
    border: 'border-green-300 dark:border-green-700',
  },
  [UnifiedStatus.FAILED]: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-400',
    border: 'border-red-300 dark:border-red-700',
  },
};

/**
 * Human-readable labels for each status.
 */
export const STATUS_LABELS: Record<UnifiedStatus, string> = {
  [UnifiedStatus.PENDING]: 'Pending',
  [UnifiedStatus.IN_PROGRESS]: 'In Progress',
  [UnifiedStatus.REVIEW]: 'Review',
  [UnifiedStatus.BLOCKED]: 'Blocked',
  [UnifiedStatus.COMPLETED]: 'Completed',
  [UnifiedStatus.FAILED]: 'Failed',
};

/**
 * Get color configuration for a status, with fallback for unknown values.
 */
export function getStatusColors(status: UnifiedStatus | string): StatusColorConfig {
  if (status in STATUS_COLORS) {
    return STATUS_COLORS[status as UnifiedStatus];
  }
  // Fallback to PENDING style for unknown statuses
  return STATUS_COLORS[UnifiedStatus.PENDING];
}

/**
 * Get label for a status, with fallback for unknown values.
 */
export function getStatusLabel(status: UnifiedStatus | string): string {
  if (status in STATUS_LABELS) {
    return STATUS_LABELS[status as UnifiedStatus];
  }
  return 'Unknown';
}
