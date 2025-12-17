/**
 * FrameworkSelector Component
 *
 * Allows users to select their preferred planning framework.
 * Used in onboarding wizard and project settings.
 *
 * Features:
 * - Radio button group with BMAD and Native options
 * - BMAD pre-selected with "(Recommended)" label
 * - Brief description text for each option
 * - Accessible: keyboard navigation, focus states
 */

import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Label } from '../ui/label';
import { FRAMEWORK_OPTIONS } from '../../../shared/constants';
import type { PlanningFramework } from '../../../shared/types';

interface FrameworkSelectorProps {
  /** Currently selected framework */
  value: PlanningFramework;
  /** Callback when framework changes */
  onChange: (framework: PlanningFramework) => void;
  /** Optional className for styling */
  className?: string;
}

/**
 * Framework selector component with radio buttons.
 * Displays available planning frameworks with descriptions.
 */
export function FrameworkSelector({
  value,
  onChange,
  className = '',
}: FrameworkSelectorProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      <h3 className="text-lg font-medium">Select Planning Framework</h3>
      <p className="text-sm text-muted-foreground">
        Choose how you want to organize and track your development tasks.
      </p>

      <RadioGroup
        value={value}
        onValueChange={(val) => onChange(val as PlanningFramework)}
        className="space-y-3"
      >
        {FRAMEWORK_OPTIONS.map((option) => (
          <label
            key={option.value}
            htmlFor={`framework-${option.value}`}
            className="flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-muted transition-colors"
          >
            <RadioGroupItem
              value={option.value}
              id={`framework-${option.value}`}
              className="mt-1"
            />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Label
                  htmlFor={`framework-${option.value}`}
                  className="font-medium cursor-pointer"
                >
                  {option.label}
                </Label>
                {option.recommended && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                    Recommended
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {option.description}
              </p>
            </div>
          </label>
        ))}
      </RadioGroup>
    </div>
  );
}
