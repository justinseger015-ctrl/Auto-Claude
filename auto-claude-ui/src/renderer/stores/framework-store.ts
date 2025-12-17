/**
 * Framework Store
 *
 * Manages the selected planning framework state with localStorage persistence.
 * The framework determines how tasks are organized and displayed:
 * - 'bmad': BMAD Method with Epics, Stories, and sprint planning
 * - 'native': Auto Claude Native with Phases and Subtasks
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { PlanningFramework } from '../../shared/types';

interface FrameworkState {
  /**
   * Currently selected planning framework.
   * Defaults to 'bmad' (recommended).
   */
  selectedFramework: PlanningFramework;

  /**
   * Set the planning framework.
   * This will persist to localStorage and trigger UI updates.
   */
  setFramework: (framework: PlanningFramework) => void;
}

/**
 * Framework store with localStorage persistence.
 * Persists the selected framework across app restarts.
 */
export const useFrameworkStore = create<FrameworkState>()(
  persist(
    (set) => ({
      selectedFramework: 'bmad', // Default to BMAD (recommended)
      setFramework: (framework) => set({ selectedFramework: framework }),
    }),
    {
      name: 'auto-claude-framework', // localStorage key
    }
  )
);

/**
 * Get the current framework value synchronously.
 * Useful for non-React contexts.
 */
export function getSelectedFramework(): PlanningFramework {
  return useFrameworkStore.getState().selectedFramework;
}

/**
 * Set the framework value synchronously.
 * Useful for non-React contexts.
 */
export function setFramework(framework: PlanningFramework): void {
  useFrameworkStore.getState().setFramework(framework);
}
