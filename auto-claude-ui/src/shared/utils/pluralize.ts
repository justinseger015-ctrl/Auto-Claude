/**
 * Pluralization utility for glossary terms.
 *
 * Handles both regular and irregular plurals for framework-specific
 * terminology used in the UI.
 *
 * Story 3.1: Glossary-Driven Board Column Headers (AC: #1)
 */

// Irregular plural mappings for glossary terms
const IRREGULAR_PLURALS: Record<string, string> = {
  Story: 'Stories',
  Subtask: 'Subtasks',
  Epic: 'Epics',
  Phase: 'Phases',
  Task: 'Tasks',
  Verification: 'Verifications',
};

/**
 * Pluralize a word based on count.
 *
 * @param word - The singular form of the word
 * @param count - The count to determine pluralization
 * @returns The appropriately pluralized word
 *
 * @example
 * pluralize('Story', 1)  // 'Story'
 * pluralize('Story', 2)  // 'Stories'
 * pluralize('Task', 0)   // 'Tasks'
 */
export function pluralize(word: string, count: number): string {
  if (count === 1) return word;

  // Check for known irregular plurals
  if (word in IRREGULAR_PLURALS) {
    return IRREGULAR_PLURALS[word];
  }

  // Handle words ending in 'y' preceded by consonant
  if (word.endsWith('y') && !/[aeiou]y$/i.test(word)) {
    return word.slice(0, -1) + 'ies';
  }

  // Handle words ending in 's', 'x', 'z', 'ch', 'sh'
  if (/[sxz]$|[cs]h$/i.test(word)) {
    return word + 'es';
  }

  // Default: add 's'
  return word + 's';
}

/**
 * Format a count with the appropriate plural form.
 *
 * @param count - The count
 * @param singular - The singular form of the word
 * @returns Formatted string like "1 Story" or "5 Stories"
 *
 * @example
 * formatCount(1, 'Story')  // '1 Story'
 * formatCount(5, 'Story')  // '5 Stories'
 */
export function formatCount(count: number, singular: string): string {
  return `${count} ${pluralize(singular, count)}`;
}
