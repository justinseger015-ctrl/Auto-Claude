/**
 * Framework Router Service for intelligent task routing.
 *
 * Routes task operations to the appropriate execution path based on
 * the project's planning framework setting (BMAD vs Native).
 *
 * Epic 4: Intelligent Task Routing (Stories 4-1, 4-2, 4-3, 4-4)
 */

import path from 'path';
import { existsSync } from 'fs';
import type { Project, PlanningFramework, Task } from '../shared/types';

/**
 * Route configuration for different task operations.
 */
export interface TaskRoute {
  /** The command to execute */
  command: string;
  /** Arguments to pass to the command */
  args: string[];
  /** Working directory for the command */
  cwd: string;
  /** Environment variables to set */
  env?: Record<string, string>;
}

/**
 * Task operation types that can be routed.
 */
export type TaskOperation =
  | 'create_spec'
  | 'execute'
  | 'review'
  | 'qa_check'
  | 'merge'
  | 'discard';

/**
 * BMAD-specific workflow commands mapped to task operations.
 */
const BMAD_WORKFLOW_MAP: Record<TaskOperation, string> = {
  create_spec: 'create-story',       // /bmad:bmm:workflows:create-story
  execute: 'dev-story',              // /bmad:bmm:workflows:dev-story
  review: 'code-review',             // /bmad:bmm:workflows:code-review
  qa_check: 'testarch-test-review',  // /bmad:bmm:workflows:testarch-test-review
  merge: 'sprint-status',            // Update status
  discard: 'sprint-status',          // Update status
};

/**
 * Native execution commands mapped to task operations.
 */
const NATIVE_COMMAND_MAP: Record<TaskOperation, string> = {
  create_spec: 'spec_runner.py',
  execute: 'run.py',
  review: 'run.py',
  qa_check: 'run.py',
  merge: 'run.py',
  discard: 'run.py',
};

/**
 * Determines the appropriate route for a task operation based on
 * the project's framework setting.
 *
 * @param project - The project containing framework settings
 * @param task - The task to route (optional, for context)
 * @param operation - The type of operation to perform
 * @returns The route configuration for the operation
 */
export function getTaskRoute(
  project: Project,
  operation: TaskOperation,
  task?: Task
): TaskRoute {
  const framework = project.settings.framework || 'native';

  if (framework === 'bmad') {
    return getBMADRoute(project, operation, task);
  }

  return getNativeRoute(project, operation, task);
}

/**
 * Gets the route for BMAD framework tasks.
 */
function getBMADRoute(
  project: Project,
  operation: TaskOperation,
  task?: Task
): TaskRoute {
  const workflow = BMAD_WORKFLOW_MAP[operation];
  const bmadOutputPath = path.join(project.path, '_bmad-output');

  // Base command uses claude CLI with the BMAD workflow
  const command = 'claude';
  const args = ['--print', `/${BMAD_WORKFLOW_MAP[operation]}`];

  // Add task-specific context
  if (task && operation === 'execute') {
    // For story execution, pass the story key
    args.push('--input', JSON.stringify({
      story_key: task.specId,
      project_path: project.path,
    }));
  }

  return {
    command,
    args,
    cwd: project.path,
    env: {
      BMAD_PROJECT_PATH: project.path,
      BMAD_OUTPUT_PATH: bmadOutputPath,
    },
  };
}

/**
 * Gets the route for Native (Auto Claude) framework tasks.
 */
function getNativeRoute(
  project: Project,
  operation: TaskOperation,
  task?: Task
): TaskRoute {
  const autoBuildPath = project.autoBuildPath || path.join(project.path, '.auto-claude');
  const scriptName = NATIVE_COMMAND_MAP[operation];

  // Determine if we should use the bundled auto-claude or a local one
  const localAutoClaude = path.join(project.path, 'auto-claude');
  const hasLocalAutoClaude = existsSync(localAutoClaude);

  const scriptPath = hasLocalAutoClaude
    ? path.join(localAutoClaude, scriptName)
    : scriptName; // Will be resolved by python env

  const args: string[] = [];

  // Add operation-specific arguments
  switch (operation) {
    case 'create_spec':
      if (task) {
        args.push('--task', task.description || task.title);
        if (task.metadata?.complexity) {
          args.push('--complexity', task.metadata.complexity);
        }
      }
      break;
    case 'execute':
      if (task) {
        args.push('--spec', task.specId);
      }
      break;
    case 'review':
      if (task) {
        args.push('--spec', task.specId, '--review');
      }
      break;
    case 'qa_check':
      if (task) {
        args.push('--spec', task.specId, '--qa');
      }
      break;
    case 'merge':
      if (task) {
        args.push('--spec', task.specId, '--merge');
      }
      break;
    case 'discard':
      if (task) {
        args.push('--spec', task.specId, '--discard');
      }
      break;
  }

  return {
    command: 'python',
    args: [scriptPath, ...args],
    cwd: project.path,
    env: {
      AUTO_BUILD_PATH: autoBuildPath,
    },
  };
}

/**
 * Determines if a project uses the BMAD framework.
 */
export function isBMADProject(project: Project): boolean {
  return project.settings.framework === 'bmad';
}

/**
 * Determines if a project uses the Native framework.
 */
export function isNativeProject(project: Project): boolean {
  return project.settings.framework === 'native' || !project.settings.framework;
}

/**
 * Gets the path to the task artifacts based on framework.
 *
 * - BMAD: _bmad-output/stories/{story-key}/
 * - Native: .auto-claude/specs/{spec-id}/
 */
export function getTaskArtifactPath(project: Project, taskId: string): string {
  if (isBMADProject(project)) {
    return path.join(project.path, '_bmad-output', 'stories', taskId);
  }

  // autoBuildPath may be absolute or relative
  const autoBuildPath = project.autoBuildPath || '.auto-claude';
  const basePath = path.isAbsolute(autoBuildPath)
    ? autoBuildPath
    : path.join(project.path, autoBuildPath);
  return path.join(basePath, 'specs', taskId);
}

/**
 * Gets the status file path based on framework.
 *
 * - BMAD: _bmad-output/bmm-sprint-status.yaml
 * - Native: .auto-claude/specs/{spec-id}/implementation_plan.json
 */
export function getStatusFilePath(project: Project, taskId?: string): string {
  if (isBMADProject(project)) {
    return path.join(project.path, '_bmad-output', 'bmm-sprint-status.yaml');
  }

  if (taskId) {
    // autoBuildPath may be absolute or relative
    const autoBuildPath = project.autoBuildPath || '.auto-claude';
    const basePath = path.isAbsolute(autoBuildPath)
      ? autoBuildPath
      : path.join(project.path, autoBuildPath);
    return path.join(basePath, 'specs', taskId, 'implementation_plan.json');
  }

  // No global status file for native
  return '';
}

/**
 * Maps a task status to the appropriate update route.
 */
export function getStatusUpdateRoute(
  project: Project,
  taskId: string,
  newStatus: string
): TaskRoute {
  if (isBMADProject(project)) {
    // BMAD uses the sprint status file
    return {
      command: 'claude',
      args: [
        '--print',
        '/bmad:bmm:workflows:sprint-status',
        '--input',
        JSON.stringify({ update: { [taskId]: newStatus } }),
      ],
      cwd: project.path,
    };
  }

  // Native updates are handled via JSON file updates
  return {
    command: 'python',
    args: ['-c', `
import json
path = '${getStatusFilePath(project, taskId)}'
with open(path, 'r') as f:
    data = json.load(f)
data['status'] = '${newStatus}'
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
`],
    cwd: project.path,
  };
}

/**
 * Validates that the project has the required files for its framework.
 */
export function validateProjectFramework(project: Project): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (isBMADProject(project)) {
    // Check for BMAD output directory
    const bmadOutputPath = path.join(project.path, '_bmad-output');
    if (!existsSync(bmadOutputPath)) {
      errors.push('BMAD output directory (_bmad-output) not found. Run BMAD init workflow first.');
    }

    // Check for sprint status file
    const sprintStatusPath = path.join(bmadOutputPath, 'bmm-sprint-status.yaml');
    if (!existsSync(sprintStatusPath)) {
      errors.push('Sprint status file (bmm-sprint-status.yaml) not found.');
    }
  } else {
    // Check for auto-claude directory
    const autoBuildPath = project.autoBuildPath || path.join(project.path, '.auto-claude');
    if (!existsSync(autoBuildPath)) {
      errors.push('Auto Claude directory not found. Initialize the project first.');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export default {
  getTaskRoute,
  getBMADRoute: (project: Project, operation: TaskOperation, task?: Task) =>
    getBMADRoute(project, operation, task),
  getNativeRoute: (project: Project, operation: TaskOperation, task?: Task) =>
    getNativeRoute(project, operation, task),
  isBMADProject,
  isNativeProject,
  getTaskArtifactPath,
  getStatusFilePath,
  getStatusUpdateRoute,
  validateProjectFramework,
};
