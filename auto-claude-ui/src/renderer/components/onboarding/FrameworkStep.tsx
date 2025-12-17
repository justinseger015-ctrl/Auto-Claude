/**
 * FrameworkStep Component
 *
 * Onboarding wizard step for selecting the planning framework.
 * Allows users to choose between BMAD Method and Auto Claude Native.
 *
 * This step appears after the welcome step and before authentication.
 */

import { useCallback } from 'react';
import { Layers } from 'lucide-react';
import { Button } from '../ui/button';
import { FrameworkSelector } from './FrameworkSelector';
import { useFrameworkStore } from '../../stores/framework-store';

interface FrameworkStepProps {
  /** Navigate to next wizard step */
  onNext: () => void;
  /** Navigate to previous wizard step */
  onBack: () => void;
  /** Skip the entire wizard */
  onSkip: () => void;
}

/**
 * Onboarding step for framework selection.
 * The selected framework is persisted to the framework store.
 */
export function FrameworkStep({ onNext, onBack, onSkip }: FrameworkStepProps) {
  const { selectedFramework, setFramework } = useFrameworkStore();

  const handleNext = useCallback(() => {
    // Framework is already persisted via the store
    onNext();
  }, [onNext]);

  return (
    <div className="max-w-2xl mx-auto py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Layers className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Choose Your Planning Framework</h2>
        <p className="text-muted-foreground">
          Select how you want Auto Claude to organize your development workflow.
          You can change this later in project settings.
        </p>
      </div>

      {/* Framework Selector */}
      <div className="mb-8">
        <FrameworkSelector
          value={selectedFramework}
          onChange={setFramework}
        />
      </div>

      {/* Info Box */}
      <div className="p-4 bg-muted rounded-lg mb-8">
        <h4 className="font-medium mb-2">What&apos;s the difference?</h4>
        <ul className="text-sm text-muted-foreground space-y-2">
          <li>
            <strong>BMAD Method</strong> uses Epics and Stories for comprehensive
            project planning with sprint cycles and detailed acceptance criteria.
          </li>
          <li>
            <strong>Auto Claude Native</strong> uses Phases and Subtasks for a
            streamlined approach ideal for quick iterations and prototyping.
          </li>
        </ul>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={onSkip}>
            Skip Setup
          </Button>
          <Button onClick={handleNext}>
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
