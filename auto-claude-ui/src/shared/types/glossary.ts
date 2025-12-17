/**
 * Glossary Type Definitions
 *
 * Framework-specific terminology for UI components.
 * Provides dynamic labels based on selected planning framework.
 *
 * IMPORTANT: Apply glossary translations in UI layer only, not data layer.
 */

import type { PlanningFramework } from './project';

/**
 * Glossary interface defining framework-specific terminology.
 * Used by UI components to display correct labels dynamically.
 */
export interface Glossary {
  /** High-level grouping: "Epic" (BMAD) or "Phase" (Native) */
  workUnit: string;
  /** Primary work item: "Story" (BMAD) or "Subtask" (Native) */
  task: string;
  /** Verification point: "Task" (BMAD) or "Verification" (Native) */
  checkpoint: string;
  /** Planning phase name: "Solutioning" (BMAD) or "Spec Creation" (Native) */
  planningPhase: string;
  /** Plural form of workUnit */
  workUnits: string;
  /** Plural form of task */
  tasks: string;
  /** Plural form of checkpoint */
  checkpoints: string;
}

/**
 * BMAD Method glossary.
 * Structured methodology with Epics, Stories, and Tasks.
 */
export const BMAD_GLOSSARY: Glossary = {
  workUnit: 'Epic',
  task: 'Story',
  checkpoint: 'Task',
  planningPhase: 'Solutioning',
  workUnits: 'Epics',
  tasks: 'Stories',
  checkpoints: 'Tasks',
};

/**
 * Auto Claude Native glossary.
 * Lightweight approach with Phases, Subtasks, and Verifications.
 */
export const NATIVE_GLOSSARY: Glossary = {
  workUnit: 'Phase',
  task: 'Subtask',
  checkpoint: 'Verification',
  planningPhase: 'Spec Creation',
  workUnits: 'Phases',
  tasks: 'Subtasks',
  checkpoints: 'Verifications',
};

/**
 * Get the glossary for a given framework.
 * @param framework - The planning framework ('bmad' or 'native')
 * @returns The corresponding glossary object
 */
export function getGlossary(framework: PlanningFramework): Glossary {
  return framework === 'bmad' ? BMAD_GLOSSARY : NATIVE_GLOSSARY;
}
