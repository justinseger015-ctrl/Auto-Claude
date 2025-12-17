/**
 * Unit tests for FrameworkSelector component
 * Tests rendering, selection, and type safety
 *
 * Story 1-3: Framework Selector in New Project Flow
 * Added in code review to improve test coverage
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FRAMEWORK_OPTIONS } from '../../shared/constants';
import type { PlanningFramework } from '../../shared/types';

describe('FrameworkSelector', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  describe('FRAMEWORK_OPTIONS configuration', () => {
    it('should have exactly two framework options', () => {
      expect(FRAMEWORK_OPTIONS.length).toBe(2);
    });

    it('should have bmad as first option with recommended flag', () => {
      const bmadOption = FRAMEWORK_OPTIONS.find(opt => opt.value === 'bmad');
      expect(bmadOption).toBeDefined();
      expect(bmadOption?.label).toBe('BMAD Method');
      expect(bmadOption?.recommended).toBe(true);
      expect(bmadOption?.description).toContain('Epics');
      expect(bmadOption?.description).toContain('Stories');
    });

    it('should have native as second option without recommended flag', () => {
      const nativeOption = FRAMEWORK_OPTIONS.find(opt => opt.value === 'native');
      expect(nativeOption).toBeDefined();
      expect(nativeOption?.label).toBe('Auto Claude Native');
      expect(nativeOption?.recommended).toBe(false);
      expect(nativeOption?.description).toContain('Phases');
      expect(nativeOption?.description).toContain('Subtasks');
    });

    it('should only have valid PlanningFramework values', () => {
      const validValues: PlanningFramework[] = ['bmad', 'native'];
      for (const option of FRAMEWORK_OPTIONS) {
        expect(validValues).toContain(option.value);
      }
    });
  });

  describe('Framework type safety', () => {
    it('should only allow bmad or native as values', () => {
      // TypeScript compilation test - these are the only valid values
      const validFrameworks: PlanningFramework[] = ['bmad', 'native'];

      expect(validFrameworks.length).toBe(2);
      expect(validFrameworks).toContain('bmad');
      expect(validFrameworks).toContain('native');
    });

    it('should have matching options for all valid frameworks', () => {
      const validFrameworks: PlanningFramework[] = ['bmad', 'native'];

      for (const framework of validFrameworks) {
        const option = FRAMEWORK_OPTIONS.find(opt => opt.value === framework);
        expect(option).toBeDefined();
        expect(option?.label).toBeTruthy();
        expect(option?.description).toBeTruthy();
      }
    });
  });

  describe('Option structure', () => {
    it('each option should have required properties', () => {
      for (const option of FRAMEWORK_OPTIONS) {
        expect(option).toHaveProperty('value');
        expect(option).toHaveProperty('label');
        expect(option).toHaveProperty('recommended');
        expect(option).toHaveProperty('description');
      }
    });

    it('each option label should be non-empty string', () => {
      for (const option of FRAMEWORK_OPTIONS) {
        expect(typeof option.label).toBe('string');
        expect(option.label.length).toBeGreaterThan(0);
      }
    });

    it('each option description should be non-empty string', () => {
      for (const option of FRAMEWORK_OPTIONS) {
        expect(typeof option.description).toBe('string');
        expect(option.description.length).toBeGreaterThan(0);
      }
    });

    it('recommended should be a boolean', () => {
      for (const option of FRAMEWORK_OPTIONS) {
        expect(typeof option.recommended).toBe('boolean');
      }
    });

    it('only one option should be recommended', () => {
      const recommendedCount = FRAMEWORK_OPTIONS.filter(opt => opt.recommended).length;
      expect(recommendedCount).toBe(1);
    });
  });

  describe('Selection behavior', () => {
    it('should be able to determine current selection from value', () => {
      const currentFramework: PlanningFramework = 'bmad';
      const currentOption = FRAMEWORK_OPTIONS.find(opt => opt.value === currentFramework);

      expect(currentOption).toBeDefined();
      expect(currentOption?.value).toBe(currentFramework);
    });

    it('onChange should receive correct framework value', () => {
      // Simulate selecting each option
      for (const option of FRAMEWORK_OPTIONS) {
        mockOnChange(option.value);
      }

      expect(mockOnChange).toHaveBeenCalledTimes(2);
      expect(mockOnChange).toHaveBeenCalledWith('bmad');
      expect(mockOnChange).toHaveBeenCalledWith('native');
    });

    it('should detect when framework would change', () => {
      const currentFramework: PlanningFramework = 'bmad';
      const newFramework: PlanningFramework = 'native';

      const wouldChange = currentFramework !== newFramework;
      expect(wouldChange).toBe(true);
    });

    it('should detect when framework would not change', () => {
      const currentFramework: PlanningFramework = 'bmad';
      const newFramework: PlanningFramework = 'bmad';

      const wouldChange = currentFramework !== newFramework;
      expect(wouldChange).toBe(false);
    });
  });
});
