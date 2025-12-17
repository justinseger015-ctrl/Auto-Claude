/**
 * StatusBadge component for displaying unified status with consistent styling.
 *
 * Provides visual status indicators with appropriate colors and icons
 * for all UnifiedStatus values across both BMAD and Native frameworks.
 *
 * Story 3.3: Unified Status Badge Mapping (AC: #1, #2)
 */

import {
  CheckCircle,
  XCircle,
  Clock,
  PauseCircle,
  Circle,
  AlertCircle,
  type LucideIcon,
} from 'lucide-react';
import { UnifiedStatus } from '../../../shared/types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  getStatusColors,
  getStatusLabel,
} from '../../../shared/constants';
import { cn } from '../../lib/utils';

/**
 * Icon mapping for each status.
 */
const STATUS_ICONS: Record<UnifiedStatus, LucideIcon> = {
  [UnifiedStatus.PENDING]: Circle,
  [UnifiedStatus.IN_PROGRESS]: Clock,
  [UnifiedStatus.REVIEW]: AlertCircle,
  [UnifiedStatus.BLOCKED]: PauseCircle,
  [UnifiedStatus.COMPLETED]: CheckCircle,
  [UnifiedStatus.FAILED]: XCircle,
};

/**
 * Get the appropriate icon for a status.
 */
function getStatusIcon(status: UnifiedStatus | string): LucideIcon {
  if (status in STATUS_ICONS) {
    return STATUS_ICONS[status as UnifiedStatus];
  }
  // Fallback to Circle for unknown statuses
  return Circle;
}

export interface StatusBadgeProps {
  /** The status to display */
  status: UnifiedStatus | string;
  /** Whether to show the icon (default: true) */
  showIcon?: boolean;
  /** Whether to show the label text (default: true) */
  showLabel?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
}

/**
 * StatusBadge displays a unified status with appropriate color and icon.
 *
 * @example
 * ```tsx
 * <StatusBadge status={UnifiedStatus.IN_PROGRESS} />
 * <StatusBadge status={UnifiedStatus.COMPLETED} size="lg" />
 * <StatusBadge status={UnifiedStatus.FAILED} showIcon={true} showLabel={false} />
 * ```
 */
export function StatusBadge({
  status,
  showIcon = true,
  showLabel = true,
  size = 'md',
  className,
}: StatusBadgeProps) {
  const colors = getStatusColors(status);
  const Icon = getStatusIcon(status);
  const label = getStatusLabel(status);

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border font-medium',
        colors.bg,
        colors.text,
        colors.border,
        sizeClasses[size],
        className
      )}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      {showLabel && <span>{label}</span>}
    </span>
  );
}

export default StatusBadge;
