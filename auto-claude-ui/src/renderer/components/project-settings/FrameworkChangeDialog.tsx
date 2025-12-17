/**
 * FrameworkChangeDialog Component
 *
 * Confirmation dialog shown when user attempts to change the planning framework.
 * Warns about implications and requires explicit confirmation.
 */

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog';
import type { PlanningFramework } from '../../../shared/types';

interface FrameworkChangeDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** The new framework being switched to */
  newFramework: PlanningFramework;
  /** Callback when user confirms the change */
  onConfirm: () => void;
}

/**
 * Alert dialog for confirming framework changes.
 * Shows implications of changing the planning methodology.
 */
export function FrameworkChangeDialog({
  open,
  onOpenChange,
  newFramework,
  onConfirm,
}: FrameworkChangeDialogProps) {
  const frameworkName = newFramework === 'bmad' ? 'BMAD Method' : 'Auto Claude Native';

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Change Planning Framework?</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div>
              <p>
                You are about to switch to <strong>{frameworkName}</strong>.
              </p>
              <p className="mt-3">This will:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Update how tasks are displayed (terminology changes)</li>
                <li>Preserve all existing task data</li>
                <li>Refresh the UI with new labels and organization</li>
              </ul>
              <p className="mt-3 text-sm">
                No data will be lost. You can switch back at any time.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>
            Switch to {frameworkName}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
