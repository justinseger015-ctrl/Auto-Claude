/**
 * FrameworkSettings Component
 *
 * Project settings section for changing the planning framework.
 * Shows current framework with option to change it.
 *
 * Story 1-4: Framework Setting in Project Settings
 * Updated: Added immediate IPC persistence on framework change
 */

import { useState, useCallback } from 'react';
import { Layers, ArrowRight } from 'lucide-react';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { FrameworkChangeDialog } from './FrameworkChangeDialog';
import { useFrameworkStore } from '../../stores/framework-store';
import { FRAMEWORK_OPTIONS } from '../../../shared/constants';
import { updateProjectSettings } from '../../stores/project-store';
import type { PlanningFramework, ProjectSettings, Project } from '../../../shared/types';

interface FrameworkSettingsProps {
  /** The project being configured */
  project: Project;
  /** Current project settings */
  settings: ProjectSettings;
  /** Callback to update settings */
  setSettings: React.Dispatch<React.SetStateAction<ProjectSettings>>;
}

/**
 * Framework settings section for project configuration.
 * Allows changing between BMAD and Native frameworks.
 */
export function FrameworkSettings({
  project,
  settings,
  setSettings,
}: FrameworkSettingsProps) {
  const { selectedFramework, setFramework } = useFrameworkStore();
  const [pendingFramework, setPendingFramework] = useState<PlanningFramework | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Use settings.framework if available, otherwise fall back to store
  const currentFramework = settings.framework || selectedFramework;
  const currentOption = FRAMEWORK_OPTIONS.find(opt => opt.value === currentFramework);

  const handleFrameworkSelect = useCallback((value: PlanningFramework) => {
    if (value !== currentFramework) {
      // Show confirmation dialog before changing
      setPendingFramework(value);
      setShowConfirmDialog(true);
    }
  }, [currentFramework]);

  const handleConfirmChange = useCallback(async () => {
    if (pendingFramework) {
      setIsSaving(true);
      try {
        // 1. Update the Zustand store (for immediate UI feedback)
        setFramework(pendingFramework);

        // 2. Update local state
        setSettings(prev => ({ ...prev, framework: pendingFramework }));

        // 3. Persist to backend immediately (Story 1-4 Task 5: IPC handler)
        const success = await updateProjectSettings(project.id, { framework: pendingFramework });
        if (!success) {
          console.error('[FrameworkSettings] Failed to persist framework change to backend');
        }
      } catch (error) {
        console.error('[FrameworkSettings] Error saving framework change:', error);
      } finally {
        setIsSaving(false);
        setShowConfirmDialog(false);
        setPendingFramework(null);
      }
    }
  }, [pendingFramework, setFramework, setSettings, project.id]);

  const handleCancelChange = useCallback(() => {
    setShowConfirmDialog(false);
    setPendingFramework(null);
  }, []);

  return (
    <div className="space-y-6">
      {/* Current Framework Display */}
      <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Layers className="h-5 w-5 text-primary" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium">Current Framework</h4>
          <p className="text-sm text-muted-foreground mt-1">
            {currentOption?.label || 'Unknown'}
            {currentOption?.recommended && (
              <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                Recommended
              </span>
            )}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            {currentOption?.description}
          </p>
        </div>
      </div>

      {/* Framework Selection */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Change Framework</Label>
        <p className="text-sm text-muted-foreground">
          Select a different planning framework. A confirmation will be required.
        </p>

        <RadioGroup
          value={currentFramework}
          onValueChange={(value) => handleFrameworkSelect(value as PlanningFramework)}
          className="space-y-2"
        >
          {FRAMEWORK_OPTIONS.map((option) => (
            <label
              key={option.value}
              htmlFor={`settings-framework-${option.value}`}
              className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                currentFramework === option.value
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-muted'
              }`}
            >
              <RadioGroupItem
                value={option.value}
                id={`settings-framework-${option.value}`}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{option.label}</span>
                  {option.recommended && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                      Recommended
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {option.description}
                </p>
              </div>
              {currentFramework !== option.value && (
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              )}
            </label>
          ))}
        </RadioGroup>
      </div>

      {/* Confirmation Dialog */}
      {pendingFramework && (
        <FrameworkChangeDialog
          open={showConfirmDialog}
          onOpenChange={handleCancelChange}
          newFramework={pendingFramework}
          onConfirm={handleConfirmChange}
        />
      )}
    </div>
  );
}
