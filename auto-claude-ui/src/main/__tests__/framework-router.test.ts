/**
 * Tests for Framework Router Service.
 *
 * Epic 4: Intelligent Task Routing (Stories 4-1, 4-2, 4-3, 4-4)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import path from 'path';
import {
  getTaskRoute,
  isBMADProject,
  isNativeProject,
  getTaskArtifactPath,
  getStatusFilePath,
  validateProjectFramework,
} from '../framework-router';
import type { Project, Task } from '../../shared/types';

// Mock fs module
vi.mock('fs', () => ({
  existsSync: vi.fn((p: string) => {
    // Default to returning true for most paths
    if (p.includes('_bmad-output')) return true;
    if (p.includes('.auto-claude')) return true;
    if (p.includes('auto-claude')) return false; // No local auto-claude
    return false;
  }),
}));

describe('Framework Router', () => {
  const createMockProject = (framework: 'bmad' | 'native'): Project => ({
    id: 'project-1',
    name: 'Test Project',
    path: '/test/project',
    autoBuildPath: '/test/project/.auto-claude',
    settings: {
      model: 'sonnet',
      memoryBackend: 'file',
      linearSync: false,
      notifications: {
        onTaskComplete: true,
        onTaskFailed: true,
        onReviewNeeded: true,
        sound: false,
      },
      graphitiMcpEnabled: false,
      framework,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
  });

  const createMockTask = (): Task => ({
    id: 'task-1',
    specId: '001-feature',
    projectId: 'project-1',
    title: 'Test Task',
    description: 'A test task',
    status: 'backlog',
    subtasks: [],
    logs: [],
    createdAt: new Date(),
    updatedAt: new Date(),
    metadata: {
      complexity: 'medium',
    },
  });

  describe('isBMADProject', () => {
    it('returns true for BMAD framework', () => {
      const project = createMockProject('bmad');
      expect(isBMADProject(project)).toBe(true);
    });

    it('returns false for Native framework', () => {
      const project = createMockProject('native');
      expect(isBMADProject(project)).toBe(false);
    });
  });

  describe('isNativeProject', () => {
    it('returns true for Native framework', () => {
      const project = createMockProject('native');
      expect(isNativeProject(project)).toBe(true);
    });

    it('returns false for BMAD framework', () => {
      const project = createMockProject('bmad');
      expect(isNativeProject(project)).toBe(false);
    });

    it('returns true when framework is undefined (default)', () => {
      const project = createMockProject('native');
      // @ts-expect-error - Testing undefined case
      project.settings.framework = undefined;
      expect(isNativeProject(project)).toBe(true);
    });
  });

  describe('getTaskRoute', () => {
    describe('BMAD framework', () => {
      it('routes create_spec to create-story workflow', () => {
        const project = createMockProject('bmad');
        const route = getTaskRoute(project, 'create_spec');

        expect(route.command).toBe('claude');
        expect(route.args).toContain('/create-story');
        expect(route.cwd).toBe('/test/project');
      });

      it('routes execute to dev-story workflow', () => {
        const project = createMockProject('bmad');
        const task = createMockTask();
        const route = getTaskRoute(project, 'execute', task);

        expect(route.command).toBe('claude');
        expect(route.args).toContain('/dev-story');
        expect(route.cwd).toBe('/test/project');
      });

      it('routes review to code-review workflow', () => {
        const project = createMockProject('bmad');
        const route = getTaskRoute(project, 'review');

        expect(route.command).toBe('claude');
        expect(route.args).toContain('/code-review');
      });

      it('sets BMAD environment variables', () => {
        const project = createMockProject('bmad');
        const route = getTaskRoute(project, 'execute');

        expect(route.env?.BMAD_PROJECT_PATH).toBe('/test/project');
        expect(route.env?.BMAD_OUTPUT_PATH).toBe('/test/project/_bmad-output');
      });
    });

    describe('Native framework', () => {
      it('routes create_spec to spec_runner.py', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'create_spec', task);

        expect(route.command).toBe('python');
        expect(route.args[0]).toContain('spec_runner.py');
        expect(route.args).toContain('--task');
      });

      it('routes execute to run.py with --spec', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'execute', task);

        expect(route.command).toBe('python');
        expect(route.args).toContain('--spec');
        expect(route.args).toContain('001-feature');
      });

      it('routes review to run.py with --review', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'review', task);

        expect(route.args).toContain('--review');
      });

      it('routes qa_check to run.py with --qa', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'qa_check', task);

        expect(route.args).toContain('--qa');
      });

      it('routes merge to run.py with --merge', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'merge', task);

        expect(route.args).toContain('--merge');
      });

      it('routes discard to run.py with --discard', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const route = getTaskRoute(project, 'discard', task);

        expect(route.args).toContain('--discard');
      });

      it('sets AUTO_BUILD_PATH environment variable', () => {
        const project = createMockProject('native');
        const route = getTaskRoute(project, 'execute');

        expect(route.env?.AUTO_BUILD_PATH).toBe('/test/project/.auto-claude');
      });
    });
  });

  describe('getTaskArtifactPath', () => {
    it('returns BMAD story path for BMAD projects', () => {
      const project = createMockProject('bmad');
      const artifactPath = getTaskArtifactPath(project, '1-1-story');

      expect(artifactPath).toBe(path.join('/test/project', '_bmad-output', 'stories', '1-1-story'));
    });

    it('returns Native spec path for Native projects', () => {
      const project = createMockProject('native');
      const artifactPath = getTaskArtifactPath(project, '001-feature');

      expect(artifactPath).toBe(path.join('/test/project', '.auto-claude', 'specs', '001-feature'));
    });
  });

  describe('getStatusFilePath', () => {
    it('returns sprint status path for BMAD projects', () => {
      const project = createMockProject('bmad');
      const statusPath = getStatusFilePath(project);

      expect(statusPath).toBe(path.join('/test/project', '_bmad-output', 'bmm-sprint-status.yaml'));
    });

    it('returns implementation plan path for Native projects', () => {
      const project = createMockProject('native');
      const statusPath = getStatusFilePath(project, '001-feature');

      expect(statusPath).toBe(
        path.join('/test/project', '.auto-claude', 'specs', '001-feature', 'implementation_plan.json')
      );
    });

    it('returns empty string for Native projects without taskId', () => {
      const project = createMockProject('native');
      const statusPath = getStatusFilePath(project);

      expect(statusPath).toBe('');
    });
  });

  describe('validateProjectFramework', () => {
    it('validates BMAD project with required files', () => {
      const project = createMockProject('bmad');
      const result = validateProjectFramework(project);

      // Mock returns true for _bmad-output paths
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('validates Native project with required files', () => {
      const project = createMockProject('native');
      const result = validateProjectFramework(project);

      // Mock returns true for .auto-claude paths
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe('framework defaults', () => {
    it('defaults to native when framework is not set', () => {
      const project = createMockProject('native');
      // @ts-expect-error - Testing undefined case
      project.settings.framework = undefined;

      const route = getTaskRoute(project, 'execute');

      // Should use native (python) route
      expect(route.command).toBe('python');
    });
  });

  describe('task metadata handling', () => {
    it('includes complexity in native create_spec route', () => {
      const project = createMockProject('native');
      const task = createMockTask();
      task.metadata = { complexity: 'complex' as const };

      const route = getTaskRoute(project, 'create_spec', task);

      expect(route.args).toContain('--complexity');
      expect(route.args).toContain('complex');
    });
  });
});
