/**
 * GlossaryContext
 *
 * React context for providing framework-specific terminology to UI components.
 * Automatically updates when the selected framework changes.
 *
 * Usage:
 * ```tsx
 * import { useGlossary } from '@/contexts/GlossaryContext';
 *
 * function MyComponent() {
 *   const glossary = useGlossary();
 *   return <h2>{glossary.tasks}</h2>;  // "Stories" or "Subtasks"
 * }
 * ```
 */

import { createContext, useContext, useMemo, type ReactNode } from 'react';
import { useFrameworkStore } from '../stores/framework-store';
import { getGlossary, type Glossary } from '../../shared/types/glossary';

/**
 * Context for glossary values.
 * Initialized as null to detect usage outside provider.
 */
const GlossaryContext = createContext<Glossary | null>(null);

interface GlossaryProviderProps {
  children: ReactNode;
}

/**
 * GlossaryProvider component.
 * Wraps the app to provide framework-specific terminology to all components.
 *
 * The glossary automatically updates when the framework store changes.
 * Memoized to prevent unnecessary re-renders.
 */
export function GlossaryProvider({ children }: GlossaryProviderProps) {
  const selectedFramework = useFrameworkStore((state) => state.selectedFramework);

  // Memoize the glossary object to prevent unnecessary re-renders
  const glossary = useMemo(
    () => getGlossary(selectedFramework),
    [selectedFramework]
  );

  return (
    <GlossaryContext.Provider value={glossary}>
      {children}
    </GlossaryContext.Provider>
  );
}

/**
 * Hook to access the current glossary.
 * Must be used within a GlossaryProvider.
 *
 * @returns The current glossary based on selected framework
 * @throws Error if used outside of GlossaryProvider
 *
 * @example
 * ```tsx
 * function TaskList() {
 *   const glossary = useGlossary();
 *   return (
 *     <div>
 *       <h2>{glossary.workUnits}</h2>
 *       <p>Showing all {glossary.tasks}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useGlossary(): Glossary {
  const context = useContext(GlossaryContext);
  if (!context) {
    throw new Error('useGlossary must be used within a GlossaryProvider');
  }
  return context;
}

/**
 * Hook to safely access the glossary, returning null if not in provider.
 * Useful for optional glossary usage or components that may render outside provider.
 *
 * @returns The current glossary or null if outside provider
 */
export function useGlossarySafe(): Glossary | null {
  return useContext(GlossaryContext);
}
