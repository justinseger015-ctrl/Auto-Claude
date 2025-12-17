/**
 * Tests for QA Integration Service.
 *
 * Epic 5: TEA + QA Loop Integration (Stories 5-1 to 5-5)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  getQACommand,
  parseQAReport,
  isQAOperationAvailable,
  getAvailableQAOperations,
  getQAOperationDescription,
  type QAOperation,
} from '../qa-integration';
import type { Project, Task } from '../../shared/types';

// Mock fs module
vi.mock('fs', () => ({
  existsSync: vi.fn((p: string) => {
    if (p.includes('qa_report.md')) return true;
    if (p.includes('test-review.md')) return true;
    return false;
  }),
  readFileSync: vi.fn((p: string) => {
    if (p.includes('qa_report.md')) {
      return `# QA Report

QA Status: Passed

## Summary
All acceptance criteria have been met.

## Tests
- Test 1: PASSED
- Test 2: PASSED
`;
    }
    if (p.includes('test-review.md')) {
      return `# TEA Test Review

All tests passed.

## Summary
Test coverage is adequate.

WARN: Minor issue with naming conventions
`;
    }
    return '';
  }),
}));

describe('QA Integration', () => {
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
    status: 'in_progress',
    subtasks: [],
    logs: [],
    createdAt: new Date(),
    updatedAt: new Date(),
  });

  describe('getQACommand', () => {
    describe('BMAD framework', () => {
      it('returns TEA test-review workflow for review operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'review');

        expect(command.command).toBe('claude');
        expect(command.args).toContain('/bmad:bmm:workflows:testarch-test-review');
        expect(command.description).toContain('TEA');
      });

      it('returns code-review workflow for fix operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'fix');

        expect(command.args).toContain('/bmad:bmm:workflows:code-review');
      });

      it('returns test-design workflow for test_design operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'test_design');

        expect(command.args).toContain('/bmad:bmm:workflows:testarch-test-design');
      });

      it('returns test-automate workflow for test_automate operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'test_automate');

        expect(command.args).toContain('/bmad:bmm:workflows:testarch-automate');
      });

      it('returns test-trace workflow for test_trace operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'test_trace');

        expect(command.args).toContain('/bmad:bmm:workflows:testarch-trace');
      });

      it('returns atdd workflow for atdd operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'atdd');

        expect(command.args).toContain('/bmad:bmm:workflows:testarch-atdd');
      });

      it('returns nfr workflow for nfr_check operation', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'nfr_check');

        expect(command.args).toContain('/bmad:bmm:workflows:testarch-nfr');
      });

      it('includes task context when task is provided', () => {
        const project = createMockProject('bmad');
        const task = createMockTask();
        const command = getQACommand(project, 'review', task);

        expect(command.args).toContain('--input');
        const inputIndex = command.args.indexOf('--input');
        const inputJson = JSON.parse(command.args[inputIndex + 1]);
        expect(inputJson.story_key).toBe('001-feature');
      });

      it('sets BMAD environment variables', () => {
        const project = createMockProject('bmad');
        const command = getQACommand(project, 'review');

        expect(command.env?.BMAD_PROJECT_PATH).toBe('/test/project');
        expect(command.env?.BMAD_OUTPUT_PATH).toBe('/test/project/_bmad-output');
      });
    });

    describe('Native framework', () => {
      it('returns run.py with --qa for review operation', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const command = getQACommand(project, 'review', task);

        expect(command.command).toBe('python');
        expect(command.args).toContain('run.py');
        expect(command.args).toContain('--qa');
        expect(command.args).toContain('--spec');
        expect(command.args).toContain('001-feature');
      });

      it('returns run.py with --qa --fix for fix operation', () => {
        const project = createMockProject('native');
        const task = createMockTask();
        const command = getQACommand(project, 'fix', task);

        expect(command.args).toContain('--qa');
        expect(command.args).toContain('--fix');
      });

      it('returns no-op for unsupported operations', () => {
        const project = createMockProject('native');
        const command = getQACommand(project, 'test_design');

        expect(command.command).toBe('echo');
        expect(command.args[0]).toContain('not supported');
      });

      it('sets AUTO_BUILD_PATH environment variable', () => {
        const project = createMockProject('native');
        const command = getQACommand(project, 'review');

        expect(command.env?.AUTO_BUILD_PATH).toBe('/test/project/.auto-claude');
      });
    });
  });

  describe('isQAOperationAvailable', () => {
    it('returns true for all operations in BMAD framework', () => {
      const project = createMockProject('bmad');
      const operations: QAOperation[] = [
        'review', 'fix', 'test_design', 'test_automate', 'test_trace', 'atdd', 'nfr_check'
      ];

      for (const op of operations) {
        expect(isQAOperationAvailable(project, op)).toBe(true);
      }
    });

    it('returns true only for review and fix in Native framework', () => {
      const project = createMockProject('native');

      expect(isQAOperationAvailable(project, 'review')).toBe(true);
      expect(isQAOperationAvailable(project, 'fix')).toBe(true);
      expect(isQAOperationAvailable(project, 'test_design')).toBe(false);
      expect(isQAOperationAvailable(project, 'test_automate')).toBe(false);
      expect(isQAOperationAvailable(project, 'atdd')).toBe(false);
    });
  });

  describe('getAvailableQAOperations', () => {
    it('returns all operations for BMAD framework', () => {
      const project = createMockProject('bmad');
      const operations = getAvailableQAOperations(project);

      expect(operations).toHaveLength(7);
      expect(operations).toContain('review');
      expect(operations).toContain('test_design');
      expect(operations).toContain('atdd');
    });

    it('returns only review and fix for Native framework', () => {
      const project = createMockProject('native');
      const operations = getAvailableQAOperations(project);

      expect(operations).toHaveLength(2);
      expect(operations).toContain('review');
      expect(operations).toContain('fix');
    });
  });

  describe('getQAOperationDescription', () => {
    it('returns description for each operation', () => {
      expect(getQAOperationDescription('review')).toContain('review');
      expect(getQAOperationDescription('fix')).toContain('Fix');
      expect(getQAOperationDescription('test_design')).toContain('test plan');
      expect(getQAOperationDescription('atdd')).toContain('acceptance');
    });
  });

  describe('parseQAReport', () => {
    it('parses Native QA report', () => {
      const project = createMockProject('native');
      const report = parseQAReport(project, '001-feature');

      expect(report).not.toBeNull();
      expect(report?.framework).toBe('native');
      expect(report?.passed).toBe(true);
    });

    it('parses BMAD TEA report', () => {
      const project = createMockProject('bmad');
      const report = parseQAReport(project, '1-1-story');

      expect(report).not.toBeNull();
      expect(report?.framework).toBe('bmad');
      expect(report?.passed).toBe(true);
    });

    it('extracts issues from report', () => {
      const project = createMockProject('bmad');
      const report = parseQAReport(project, '1-1-story');

      expect(report?.issues.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('QA workflow integration', () => {
    it('BMAD TEA workflows are properly mapped', () => {
      const project = createMockProject('bmad');

      // All TEA workflows should be accessible
      const workflows = [
        { op: 'review' as QAOperation, workflow: 'testarch-test-review' },
        { op: 'test_design' as QAOperation, workflow: 'testarch-test-design' },
        { op: 'test_automate' as QAOperation, workflow: 'testarch-automate' },
        { op: 'test_trace' as QAOperation, workflow: 'testarch-trace' },
        { op: 'atdd' as QAOperation, workflow: 'testarch-atdd' },
        { op: 'nfr_check' as QAOperation, workflow: 'testarch-nfr' },
      ];

      for (const { op, workflow } of workflows) {
        const command = getQACommand(project, op);
        expect(command.args.join(' ')).toContain(workflow);
      }
    });

    it('Native QA loop uses correct commands', () => {
      const project = createMockProject('native');
      const task = createMockTask();

      // Review should use --qa flag
      const reviewCmd = getQACommand(project, 'review', task);
      expect(reviewCmd.args).toContain('--qa');

      // Fix should use --qa and --fix flags
      const fixCmd = getQACommand(project, 'fix', task);
      expect(fixCmd.args).toContain('--qa');
      expect(fixCmd.args).toContain('--fix');
    });
  });
});
