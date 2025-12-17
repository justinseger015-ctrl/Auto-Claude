/**
 * Unified status types for framework-agnostic task tracking.
 *
 * These status values are used across both BMAD Method and Native frameworks,
 * providing a consistent interface for the UI regardless of the underlying
 * planning methodology.
 *
 * Story 3.3: Unified Status Badge Mapping (AC: #1)
 */

/**
 * Unified status enum for tasks across all frameworks.
 *
 * Status Mapping:
 * | UnifiedStatus | BMAD Status          | Native Status              |
 * |---------------|----------------------|----------------------------|
 * | PENDING       | backlog, ready       | pending                    |
 * | IN_PROGRESS   | in-progress          | in_progress                |
 * | REVIEW        | review               | ai_review, human_review    |
 * | BLOCKED       | blocked              | -                          |
 * | COMPLETED     | done                 | done                       |
 * | FAILED        | -                    | failed                     |
 */
export enum UnifiedStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  BLOCKED = 'blocked',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Check if a value is a valid UnifiedStatus.
 */
export function isUnifiedStatus(value: unknown): value is UnifiedStatus {
  return Object.values(UnifiedStatus).includes(value as UnifiedStatus);
}
