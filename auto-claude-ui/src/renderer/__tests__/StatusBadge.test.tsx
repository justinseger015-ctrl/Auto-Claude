/**
 * Tests for StatusBadge component.
 *
 * Story 3.3: Unified Status Badge Mapping (AC: all)
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { StatusBadge } from '../components/ui/StatusBadge';
import { UnifiedStatus } from '../../shared/types';

describe('StatusBadge', () => {
  describe('color scheme mapping', () => {
    it.each([
      [UnifiedStatus.PENDING, 'gray'],
      [UnifiedStatus.IN_PROGRESS, 'blue'],
      [UnifiedStatus.REVIEW, 'yellow'],
      [UnifiedStatus.BLOCKED, 'red'],
      [UnifiedStatus.COMPLETED, 'green'],
      [UnifiedStatus.FAILED, 'red'],
    ])('renders %s status with %s color scheme', (status, colorName) => {
      const { container } = render(<StatusBadge status={status} />);
      const badge = container.firstChild as HTMLElement;

      // Check badge contains expected color class
      expect(badge.className).toContain(colorName);
    });
  });

  describe('status labels', () => {
    it('shows "Pending" for PENDING status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.PENDING} />);
      expect(container.textContent).toContain('Pending');
    });

    it('shows "In Progress" for IN_PROGRESS status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.IN_PROGRESS} />);
      expect(container.textContent).toContain('In Progress');
    });

    it('shows "Review" for REVIEW status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.REVIEW} />);
      expect(container.textContent).toContain('Review');
    });

    it('shows "Blocked" for BLOCKED status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.BLOCKED} />);
      expect(container.textContent).toContain('Blocked');
    });

    it('shows "Completed" for COMPLETED status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.COMPLETED} />);
      expect(container.textContent).toContain('Completed');
    });

    it('shows "Failed" for FAILED status', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.FAILED} />);
      expect(container.textContent).toContain('Failed');
    });
  });

  describe('icon visibility', () => {
    it('shows icon by default', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.COMPLETED} />);
      const svg = container.querySelector('svg');
      expect(svg).not.toBeNull();
    });

    it('hides icon when showIcon is false', () => {
      const { container } = render(
        <StatusBadge status={UnifiedStatus.COMPLETED} showIcon={false} />
      );
      const svg = container.querySelector('svg');
      expect(svg).toBeNull();
    });
  });

  describe('label visibility', () => {
    it('shows label by default', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.COMPLETED} />);
      expect(container.textContent).toContain('Completed');
    });

    it('hides label when showLabel is false', () => {
      const { container } = render(
        <StatusBadge status={UnifiedStatus.COMPLETED} showLabel={false} />
      );
      expect(container.textContent).not.toContain('Completed');
    });
  });

  describe('size variants', () => {
    it('renders small size', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.PENDING} size="sm" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain('text-xs');
    });

    it('renders medium size (default)', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.PENDING} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain('text-sm');
    });

    it('renders large size', () => {
      const { container } = render(<StatusBadge status={UnifiedStatus.PENDING} size="lg" />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain('text-base');
    });
  });

  describe('unknown status handling', () => {
    it('handles unknown status gracefully', () => {
      const { container } = render(<StatusBadge status={'invalid-status' as UnifiedStatus} />);
      expect(container.textContent).toContain('Unknown');
    });

    it('uses gray styling for unknown status', () => {
      const { container } = render(<StatusBadge status={'invalid-status' as UnifiedStatus} />);
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain('gray');
    });
  });

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <StatusBadge status={UnifiedStatus.PENDING} className="custom-class" />
      );
      const badge = container.firstChild as HTMLElement;
      expect(badge.className).toContain('custom-class');
    });
  });
});
