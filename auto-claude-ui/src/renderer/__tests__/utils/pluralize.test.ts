/**
 * Tests for pluralization utility.
 *
 * Story 3.1: Glossary-Driven Board Column Headers (AC: #1)
 */
import { describe, it, expect } from 'vitest';
import { pluralize, formatCount } from '../../../shared/utils/pluralize';

describe('pluralize', () => {
  describe('with count of 1', () => {
    it('returns singular form', () => {
      expect(pluralize('Story', 1)).toBe('Story');
      expect(pluralize('Task', 1)).toBe('Task');
      expect(pluralize('Subtask', 1)).toBe('Subtask');
    });
  });

  describe('with count of 0 or > 1', () => {
    it('returns plural form for 0', () => {
      expect(pluralize('Story', 0)).toBe('Stories');
      expect(pluralize('Task', 0)).toBe('Tasks');
    });

    it('returns plural form for > 1', () => {
      expect(pluralize('Story', 2)).toBe('Stories');
      expect(pluralize('Task', 5)).toBe('Tasks');
      expect(pluralize('Subtask', 10)).toBe('Subtasks');
    });
  });

  describe('known irregular plurals', () => {
    it('handles Story -> Stories', () => {
      expect(pluralize('Story', 2)).toBe('Stories');
    });

    it('handles Subtask -> Subtasks', () => {
      expect(pluralize('Subtask', 2)).toBe('Subtasks');
    });

    it('handles Epic -> Epics', () => {
      expect(pluralize('Epic', 2)).toBe('Epics');
    });

    it('handles Phase -> Phases', () => {
      expect(pluralize('Phase', 2)).toBe('Phases');
    });

    it('handles Task -> Tasks', () => {
      expect(pluralize('Task', 2)).toBe('Tasks');
    });

    it('handles Verification -> Verifications', () => {
      expect(pluralize('Verification', 2)).toBe('Verifications');
    });
  });

  describe('regular pluralization rules', () => {
    it('handles words ending in consonant + y', () => {
      expect(pluralize('Category', 2)).toBe('Categories');
    });

    it('handles words ending in vowel + y', () => {
      expect(pluralize('Day', 2)).toBe('Days');
    });

    it('handles words ending in s, x, z', () => {
      expect(pluralize('Box', 2)).toBe('Boxes');
      expect(pluralize('Bus', 2)).toBe('Buses');
    });

    it('handles words ending in ch, sh', () => {
      expect(pluralize('Match', 2)).toBe('Matches');
      expect(pluralize('Wish', 2)).toBe('Wishes');
    });

    it('adds s for regular words', () => {
      expect(pluralize('Item', 2)).toBe('Items');
      expect(pluralize('Feature', 2)).toBe('Features');
    });
  });
});

describe('formatCount', () => {
  it('formats singular correctly', () => {
    expect(formatCount(1, 'Story')).toBe('1 Story');
    expect(formatCount(1, 'Task')).toBe('1 Task');
  });

  it('formats plural correctly', () => {
    expect(formatCount(0, 'Story')).toBe('0 Stories');
    expect(formatCount(5, 'Story')).toBe('5 Stories');
    expect(formatCount(3, 'Task')).toBe('3 Tasks');
  });

  it('handles BMAD terminology', () => {
    expect(formatCount(2, 'Story')).toBe('2 Stories');
    expect(formatCount(4, 'Epic')).toBe('4 Epics');
    expect(formatCount(3, 'Task')).toBe('3 Tasks');
  });

  it('handles Native terminology', () => {
    expect(formatCount(2, 'Subtask')).toBe('2 Subtasks');
    expect(formatCount(4, 'Phase')).toBe('4 Phases');
    expect(formatCount(3, 'Verification')).toBe('3 Verifications');
  });
});
