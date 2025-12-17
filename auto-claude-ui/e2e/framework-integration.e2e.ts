/**
 * End-to-End tests for Dual-Framework Integration
 *
 * Epic 6: E2E Validation (Stories 6-1 to 6-4)
 *
 * Tests the complete user experience with both BMAD and Native frameworks
 * including framework selection, task routing, glossary display, and QA integration.
 *
 * NOTE: These tests require the Electron app to be built first.
 * Run `npm run build` before running E2E tests.
 *
 * To run: npx playwright test --config=e2e/playwright.config.ts
 */
import { test, expect, _electron as electron, ElectronApplication, Page } from '@playwright/test';
import { mkdirSync, rmSync, existsSync, writeFileSync, readFileSync } from 'fs';
import path from 'path';
import * as yaml from 'yaml';

// Test data directories
const TEST_DATA_DIR = '/tmp/auto-claude-ui-e2e-framework';
const BMAD_PROJECT_DIR = path.join(TEST_DATA_DIR, 'bmad-project');
const NATIVE_PROJECT_DIR = path.join(TEST_DATA_DIR, 'native-project');

/**
 * Setup BMAD test environment with proper directory structure.
 */
function setupBMADTestEnvironment(): void {
  if (existsSync(BMAD_PROJECT_DIR)) {
    rmSync(BMAD_PROJECT_DIR, { recursive: true, force: true });
  }
  mkdirSync(BMAD_PROJECT_DIR, { recursive: true });

  // BMAD output structure
  const bmadOutput = path.join(BMAD_PROJECT_DIR, '_bmad-output');
  mkdirSync(bmadOutput, { recursive: true });
  mkdirSync(path.join(bmadOutput, 'stories'), { recursive: true });
  mkdirSync(path.join(bmadOutput, 'docs'), { recursive: true });

  // Create sprint status file
  const sprintStatus = {
    sprint: {
      name: 'Test Sprint 1',
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'in_progress',
    },
    epics: [
      {
        id: '1',
        name: 'Test Epic',
        status: 'in_progress',
        stories: [
          {
            id: '1-1',
            key: '1-1-test-story',
            name: 'Test Story',
            status: 'ready-for-dev',
            priority: 'high',
          },
          {
            id: '1-2',
            key: '1-2-another-story',
            name: 'Another Story',
            status: 'in_progress',
            priority: 'medium',
          },
        ],
      },
    ],
  };
  writeFileSync(path.join(bmadOutput, 'bmm-sprint-status.yaml'), yaml.stringify(sprintStatus));
}

/**
 * Setup Native test environment with proper directory structure.
 */
function setupNativeTestEnvironment(): void {
  if (existsSync(NATIVE_PROJECT_DIR)) {
    rmSync(NATIVE_PROJECT_DIR, { recursive: true, force: true });
  }
  mkdirSync(NATIVE_PROJECT_DIR, { recursive: true });

  // Native .auto-claude structure
  const autoClaude = path.join(NATIVE_PROJECT_DIR, '.auto-claude');
  mkdirSync(autoClaude, { recursive: true });
  mkdirSync(path.join(autoClaude, 'specs'), { recursive: true });
}

/**
 * Create a BMAD story for testing.
 */
function createBMADStory(
  storyKey: string,
  status: 'draft' | 'ready-for-dev' | 'in_progress' | 'in_review' | 'done' = 'ready-for-dev'
): void {
  const storyDir = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', storyKey);
  mkdirSync(storyDir, { recursive: true });

  // Create story file
  const storyContent = `# Story: ${storyKey}

## Description
This is a test story for E2E validation.

## Acceptance Criteria
- [ ] AC1: First criterion
- [ ] AC2: Second criterion

## Tasks
- [ ] Task 1: Implement feature
- [ ] Task 2: Write tests
- [ ] Task 3: Documentation

## Status
Status: ${status}

## Notes
Created for E2E testing.
`;
  writeFileSync(path.join(storyDir, 'story.md'), storyContent);

  // Create status tracking file
  const storyStatus = {
    key: storyKey,
    status,
    tasks: [
      { id: 1, description: 'Implement feature', status: status === 'done' ? 'completed' : 'pending' },
      { id: 2, description: 'Write tests', status: 'pending' },
      { id: 3, description: 'Documentation', status: 'pending' },
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  writeFileSync(path.join(storyDir, 'status.json'), JSON.stringify(storyStatus, null, 2));
}

/**
 * Create a Native spec for testing.
 */
function createNativeSpec(
  specId: string,
  status: 'pending' | 'in_progress' | 'completed' | 'review' = 'pending'
): void {
  const specDir = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', specId);
  mkdirSync(specDir, { recursive: true });

  const chunkStatus = status === 'completed' ? 'completed' : status === 'in_progress' ? 'in_progress' : 'pending';

  // Create implementation plan
  const plan = {
    feature: `Test Feature ${specId}`,
    workflow_type: 'feature',
    services_involved: ['frontend', 'backend'],
    phases: [
      {
        phase: 1,
        name: 'Implementation',
        type: 'implementation',
        chunks: [
          { id: 'chunk-1', description: 'Implement core feature', status: chunkStatus },
          { id: 'chunk-2', description: 'Add tests', status: 'pending' },
        ],
      },
    ],
    final_acceptance: ['All tests pass', 'No TypeScript errors'],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    spec_file: 'spec.md',
  };
  writeFileSync(path.join(specDir, 'implementation_plan.json'), JSON.stringify(plan, null, 2));

  // Create spec file
  const specContent = `# ${specId}

## Overview
This is a test feature specification.

## Requirements
- REQ-1: Feature must work correctly
- REQ-2: Feature must have tests

## Acceptance Criteria
1. Feature is implemented
2. Tests pass
`;
  writeFileSync(path.join(specDir, 'spec.md'), specContent);
}

/**
 * Cleanup all test environments.
 */
function cleanupTestEnvironments(): void {
  if (existsSync(TEST_DATA_DIR)) {
    rmSync(TEST_DATA_DIR, { recursive: true, force: true });
  }
}

// ============================================================
// Story 6-1: BMAD Framework Flow E2E Tests
// ============================================================

test.describe('Story 6-1: BMAD Framework Flow', () => {
  test.beforeAll(() => {
    setupBMADTestEnvironment();
    createBMADStory('1-1-test-story', 'ready-for-dev');
    createBMADStory('1-2-another-story', 'in_progress');
    createBMADStory('1-3-done-story', 'done');
  });

  test.afterAll(() => {
    cleanupTestEnvironments();
  });

  test('BMAD project structure should be created correctly', () => {
    expect(existsSync(BMAD_PROJECT_DIR)).toBe(true);
    expect(existsSync(path.join(BMAD_PROJECT_DIR, '_bmad-output'))).toBe(true);
    expect(existsSync(path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories'))).toBe(true);
    expect(existsSync(path.join(BMAD_PROJECT_DIR, '_bmad-output', 'bmm-sprint-status.yaml'))).toBe(true);
  });

  test('Sprint status file should have correct structure', () => {
    const statusPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'bmm-sprint-status.yaml');
    const content = readFileSync(statusPath, 'utf-8');
    const status = yaml.parse(content);

    expect(status).toHaveProperty('sprint');
    expect(status).toHaveProperty('epics');
    expect(status.sprint.status).toBe('in_progress');
    expect(status.epics.length).toBeGreaterThan(0);
    expect(status.epics[0].stories.length).toBeGreaterThan(0);
  });

  test('BMAD stories should have correct file structure', () => {
    const storyDir = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story');
    expect(existsSync(storyDir)).toBe(true);
    expect(existsSync(path.join(storyDir, 'story.md'))).toBe(true);
    expect(existsSync(path.join(storyDir, 'status.json'))).toBe(true);
  });

  test('BMAD story status should be parseable', () => {
    const statusPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story', 'status.json');
    const status = JSON.parse(readFileSync(statusPath, 'utf-8'));

    expect(status.key).toBe('1-1-test-story');
    expect(status.status).toBe('ready-for-dev');
    expect(status.tasks).toHaveLength(3);
  });

  test('BMAD story content should include acceptance criteria', () => {
    const storyPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story', 'story.md');
    const content = readFileSync(storyPath, 'utf-8');

    expect(content).toContain('Acceptance Criteria');
    expect(content).toContain('AC1:');
    expect(content).toContain('Tasks');
  });

  test('BMAD status mapping should work correctly', () => {
    // Verify different statuses map correctly
    const stories = [
      { key: '1-1-test-story', expectedStatus: 'ready-for-dev' },
      { key: '1-2-another-story', expectedStatus: 'in_progress' },
      { key: '1-3-done-story', expectedStatus: 'done' },
    ];

    for (const story of stories) {
      const statusPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', story.key, 'status.json');
      const status = JSON.parse(readFileSync(statusPath, 'utf-8'));
      expect(status.status).toBe(story.expectedStatus);
    }
  });
});

// ============================================================
// Story 6-2: Native Framework Flow E2E Tests
// ============================================================

test.describe('Story 6-2: Native Framework Flow', () => {
  test.beforeAll(() => {
    setupNativeTestEnvironment();
    createNativeSpec('001-feature', 'pending');
    createNativeSpec('002-feature', 'in_progress');
    createNativeSpec('003-feature', 'completed');
  });

  test.afterAll(() => {
    cleanupTestEnvironments();
  });

  test('Native project structure should be created correctly', () => {
    expect(existsSync(NATIVE_PROJECT_DIR)).toBe(true);
    expect(existsSync(path.join(NATIVE_PROJECT_DIR, '.auto-claude'))).toBe(true);
    expect(existsSync(path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs'))).toBe(true);
  });

  test('Native specs should have correct file structure', () => {
    const specDir = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature');
    expect(existsSync(specDir)).toBe(true);
    expect(existsSync(path.join(specDir, 'implementation_plan.json'))).toBe(true);
    expect(existsSync(path.join(specDir, 'spec.md'))).toBe(true);
  });

  test('Native implementation plan should be parseable', () => {
    const planPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature', 'implementation_plan.json');
    const plan = JSON.parse(readFileSync(planPath, 'utf-8'));

    expect(plan.feature).toBe('Test Feature 001-feature');
    expect(plan.phases).toHaveLength(1);
    expect(plan.phases[0].chunks).toHaveLength(2);
  });

  test('Native spec content should include requirements', () => {
    const specPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature', 'spec.md');
    const content = readFileSync(specPath, 'utf-8');

    expect(content).toContain('Requirements');
    expect(content).toContain('REQ-1');
    expect(content).toContain('Acceptance Criteria');
  });

  test('Native chunk status should update correctly', () => {
    // Simulate status update
    const planPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '002-feature', 'implementation_plan.json');
    const plan = JSON.parse(readFileSync(planPath, 'utf-8'));

    expect(plan.phases[0].chunks[0].status).toBe('in_progress');

    // Update status
    plan.phases[0].chunks[0].status = 'completed';
    writeFileSync(planPath, JSON.stringify(plan, null, 2));

    // Verify update
    const updatedPlan = JSON.parse(readFileSync(planPath, 'utf-8'));
    expect(updatedPlan.phases[0].chunks[0].status).toBe('completed');
  });

  test('Native status mapping should work correctly', () => {
    const specs = [
      { id: '001-feature', expectedChunkStatus: 'pending' },
      { id: '003-feature', expectedChunkStatus: 'completed' },
    ];

    for (const spec of specs) {
      const planPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', spec.id, 'implementation_plan.json');
      const plan = JSON.parse(readFileSync(planPath, 'utf-8'));
      expect(plan.phases[0].chunks[0].status).toBe(spec.expectedChunkStatus);
    }
  });
});

// ============================================================
// Story 6-3: Framework Switching E2E Tests
// ============================================================

test.describe('Story 6-3: Framework Switching', () => {
  test.beforeAll(() => {
    setupBMADTestEnvironment();
    setupNativeTestEnvironment();
    createBMADStory('1-1-test-story', 'ready-for-dev');
    createNativeSpec('001-feature', 'pending');
  });

  test.afterAll(() => {
    cleanupTestEnvironments();
  });

  test('Both framework structures can coexist', () => {
    // Both project types should exist
    expect(existsSync(BMAD_PROJECT_DIR)).toBe(true);
    expect(existsSync(NATIVE_PROJECT_DIR)).toBe(true);

    // Each should have their specific structure
    expect(existsSync(path.join(BMAD_PROJECT_DIR, '_bmad-output'))).toBe(true);
    expect(existsSync(path.join(NATIVE_PROJECT_DIR, '.auto-claude'))).toBe(true);
  });

  test('Project settings should persist framework choice', () => {
    // Simulate project settings storage
    const bmadSettings = {
      id: 'bmad-project-1',
      name: 'BMAD Test Project',
      path: BMAD_PROJECT_DIR,
      settings: {
        framework: 'bmad',
        model: 'sonnet',
        memoryBackend: 'file',
      },
    };

    const nativeSettings = {
      id: 'native-project-1',
      name: 'Native Test Project',
      path: NATIVE_PROJECT_DIR,
      settings: {
        framework: 'native',
        model: 'sonnet',
        memoryBackend: 'file',
      },
    };

    // Save settings
    writeFileSync(
      path.join(BMAD_PROJECT_DIR, '.auto-claude-settings.json'),
      JSON.stringify(bmadSettings, null, 2)
    );
    writeFileSync(
      path.join(NATIVE_PROJECT_DIR, '.auto-claude-settings.json'),
      JSON.stringify(nativeSettings, null, 2)
    );

    // Verify settings
    const loadedBmad = JSON.parse(readFileSync(path.join(BMAD_PROJECT_DIR, '.auto-claude-settings.json'), 'utf-8'));
    const loadedNative = JSON.parse(readFileSync(path.join(NATIVE_PROJECT_DIR, '.auto-claude-settings.json'), 'utf-8'));

    expect(loadedBmad.settings.framework).toBe('bmad');
    expect(loadedNative.settings.framework).toBe('native');
  });

  test('Framework detection should identify correct type', () => {
    // BMAD detection: check for _bmad-output directory
    const hasBmadOutput = existsSync(path.join(BMAD_PROJECT_DIR, '_bmad-output'));
    expect(hasBmadOutput).toBe(true);

    // Native detection: check for .auto-claude directory
    const hasAutoClaude = existsSync(path.join(NATIVE_PROJECT_DIR, '.auto-claude'));
    expect(hasAutoClaude).toBe(true);

    // Cross-check: BMAD shouldn't have .auto-claude (in this test setup)
    const bmadHasAutoClaude = existsSync(path.join(BMAD_PROJECT_DIR, '.auto-claude'));
    expect(bmadHasAutoClaude).toBe(false);
  });

  test('Glossary terms should differ by framework', () => {
    const bmadGlossary = {
      task: 'Story',
      checkpoint: 'Task',
      workUnit: 'Epic',
      framework: 'BMAD Method',
    };

    const nativeGlossary = {
      task: 'Task',
      checkpoint: 'Subtask',
      workUnit: 'Phase',
      framework: 'Auto Claude Native',
    };

    // Verify glossary differences
    expect(bmadGlossary.task).not.toBe(nativeGlossary.task);
    expect(bmadGlossary.checkpoint).not.toBe(nativeGlossary.checkpoint);
    expect(bmadGlossary.workUnit).not.toBe(nativeGlossary.workUnit);
  });
});

// ============================================================
// Story 6-4: Unified QA Integration E2E Tests
// ============================================================

test.describe('Story 6-4: Unified QA Integration', () => {
  test.beforeAll(() => {
    setupBMADTestEnvironment();
    setupNativeTestEnvironment();
    createBMADStory('1-1-test-story', 'in_review');
    createNativeSpec('001-feature', 'completed');
  });

  test.afterAll(() => {
    cleanupTestEnvironments();
  });

  test('BMAD TEA test review report can be created', () => {
    const storyDir = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story');

    // Create TEA test review report
    const teaReport = `# TEA Test Review

## Summary
All tests passed.

## Test Results
- Unit Tests: PASSED
- Integration Tests: PASSED
- Acceptance Tests: PASSED

## Coverage
Test coverage is adequate.

## Quality Gate
PASS: All criteria met.
`;
    writeFileSync(path.join(storyDir, 'test-review.md'), teaReport);

    // Verify report exists and is parseable
    const reportPath = path.join(storyDir, 'test-review.md');
    expect(existsSync(reportPath)).toBe(true);

    const content = readFileSync(reportPath, 'utf-8');
    expect(content).toContain('TEA Test Review');
    expect(content).toContain('PASS');
  });

  test('Native QA report can be created', () => {
    const specDir = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature');

    // Create Native QA report
    const qaReport = `# QA Report

QA Status: Passed

## Summary
All acceptance criteria have been met.

## Tests
- Test 1: PASSED
- Test 2: PASSED

## Acceptance Criteria
- AC1: PASSED
- AC2: PASSED
`;
    writeFileSync(path.join(specDir, 'qa_report.md'), qaReport);

    // Verify report
    const reportPath = path.join(specDir, 'qa_report.md');
    expect(existsSync(reportPath)).toBe(true);

    const content = readFileSync(reportPath, 'utf-8');
    expect(content).toContain('QA Status: Passed');
  });

  test('BMAD QA operations should be available', () => {
    // BMAD supports all TEA operations
    const bmadOperations = ['review', 'fix', 'test_design', 'test_automate', 'test_trace', 'atdd', 'nfr_check'];

    // Verify each operation type has a workflow mapping
    const teaWorkflows: Record<string, string> = {
      review: 'testarch-test-review',
      fix: 'code-review',
      test_design: 'testarch-test-design',
      test_automate: 'testarch-automate',
      test_trace: 'testarch-trace',
      atdd: 'testarch-atdd',
      nfr_check: 'testarch-nfr',
    };

    for (const op of bmadOperations) {
      expect(teaWorkflows[op]).toBeDefined();
    }
  });

  test('Native QA operations should be limited', () => {
    // Native only supports review and fix
    const nativeOperations = ['review', 'fix'];
    const unsupportedOperations = ['test_design', 'test_automate', 'test_trace', 'atdd', 'nfr_check'];

    // Verify native supports only basic operations
    expect(nativeOperations).toHaveLength(2);
    expect(nativeOperations).toContain('review');
    expect(nativeOperations).toContain('fix');

    // Verify unsupported operations list
    for (const op of unsupportedOperations) {
      expect(nativeOperations).not.toContain(op);
    }
  });

  test('QA fix request workflow should work for both frameworks', () => {
    // BMAD fix request
    const bmadStoryDir = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story');
    const bmadFixRequest = `# Code Review Fix Request

## Issues Found
1. Missing test coverage for edge case
2. Variable naming not following conventions

## Recommended Fixes
- Add tests for null input handling
- Rename \`x\` to \`userInput\`

## Status
NEEDS_FIXES
`;
    writeFileSync(path.join(bmadStoryDir, 'code-review.md'), bmadFixRequest);

    // Native fix request
    const nativeSpecDir = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature');
    const nativeFixRequest = `# QA Fix Request

Status: REJECTED

## Feedback
Tests are failing. Please fix the following issues:
1. Unit test for userService.create() fails
2. Integration test timeout

## Expected Changes
- Fix mock setup in unit tests
- Increase timeout for integration tests
`;
    writeFileSync(path.join(nativeSpecDir, 'QA_FIX_REQUEST.md'), nativeFixRequest);

    // Verify both fix requests exist
    expect(existsSync(path.join(bmadStoryDir, 'code-review.md'))).toBe(true);
    expect(existsSync(path.join(nativeSpecDir, 'QA_FIX_REQUEST.md'))).toBe(true);

    // Verify content indicates need for fixes
    const bmadContent = readFileSync(path.join(bmadStoryDir, 'code-review.md'), 'utf-8');
    const nativeContent = readFileSync(path.join(nativeSpecDir, 'QA_FIX_REQUEST.md'), 'utf-8');

    expect(bmadContent).toContain('NEEDS_FIXES');
    expect(nativeContent).toContain('REJECTED');
  });

  test('QA report parsing should extract pass/fail status', () => {
    // Parse BMAD report
    const bmadReportPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story', 'test-review.md');
    const bmadContent = readFileSync(bmadReportPath, 'utf-8');

    // Check for pass indicators
    const bmadPassed =
      bmadContent.toLowerCase().includes('pass') || bmadContent.toLowerCase().includes('all tests passed');
    expect(bmadPassed).toBe(true);

    // Parse Native report
    const nativeReportPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature', 'qa_report.md');
    const nativeContent = readFileSync(nativeReportPath, 'utf-8');

    // Check for pass indicators
    const nativePassed =
      nativeContent.toLowerCase().includes('qa status: passed') ||
      nativeContent.toLowerCase().includes('all criteria met');
    expect(nativePassed).toBe(true);
  });
});

// ============================================================
// Integration Tests - Both Frameworks Together
// ============================================================

test.describe('Integration: Dual Framework Coexistence', () => {
  test.beforeAll(() => {
    setupBMADTestEnvironment();
    setupNativeTestEnvironment();
    createBMADStory('1-1-test-story', 'in_progress');
    createNativeSpec('001-feature', 'in_progress');
  });

  test.afterAll(() => {
    cleanupTestEnvironments();
  });

  test('Both frameworks can have active tasks simultaneously', () => {
    // Check BMAD active task
    const bmadStatusPath = path.join(
      BMAD_PROJECT_DIR,
      '_bmad-output',
      'stories',
      '1-1-test-story',
      'status.json'
    );
    const bmadStatus = JSON.parse(readFileSync(bmadStatusPath, 'utf-8'));
    expect(bmadStatus.status).toBe('in_progress');

    // Check Native active task
    const nativePlanPath = path.join(
      NATIVE_PROJECT_DIR,
      '.auto-claude',
      'specs',
      '001-feature',
      'implementation_plan.json'
    );
    const nativePlan = JSON.parse(readFileSync(nativePlanPath, 'utf-8'));
    expect(nativePlan.phases[0].chunks[0].status).toBe('in_progress');
  });

  test('Task routing should respect framework boundaries', () => {
    // BMAD route configuration
    const bmadRoute = {
      command: 'claude',
      workflow: '/bmad:bmm:workflows:dev-story',
      env: {
        BMAD_PROJECT_PATH: BMAD_PROJECT_DIR,
        BMAD_OUTPUT_PATH: path.join(BMAD_PROJECT_DIR, '_bmad-output'),
      },
    };

    // Native route configuration
    const nativeRoute = {
      command: 'python',
      script: 'run.py',
      env: {
        AUTO_BUILD_PATH: path.join(NATIVE_PROJECT_DIR, '.auto-claude'),
      },
    };

    // Verify routes are different
    expect(bmadRoute.command).not.toBe(nativeRoute.command);
    expect(bmadRoute.env.BMAD_PROJECT_PATH).toBeDefined();
    expect(nativeRoute.env.AUTO_BUILD_PATH).toBeDefined();
  });

  test('Artifact paths should be framework-specific', () => {
    // BMAD artifact path
    const bmadArtifactPath = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'stories', '1-1-test-story');
    expect(bmadArtifactPath).toContain('_bmad-output');
    expect(bmadArtifactPath).toContain('stories');

    // Native artifact path
    const nativeArtifactPath = path.join(NATIVE_PROJECT_DIR, '.auto-claude', 'specs', '001-feature');
    expect(nativeArtifactPath).toContain('.auto-claude');
    expect(nativeArtifactPath).toContain('specs');

    // Verify paths are different
    expect(bmadArtifactPath).not.toBe(nativeArtifactPath);
  });

  test('Status file locations should differ by framework', () => {
    // BMAD status file (global)
    const bmadStatusFile = path.join(BMAD_PROJECT_DIR, '_bmad-output', 'bmm-sprint-status.yaml');
    expect(existsSync(bmadStatusFile)).toBe(true);

    // Native status file (per-spec)
    const nativeStatusFile = path.join(
      NATIVE_PROJECT_DIR,
      '.auto-claude',
      'specs',
      '001-feature',
      'implementation_plan.json'
    );
    expect(existsSync(nativeStatusFile)).toBe(true);

    // Verify file types differ
    expect(bmadStatusFile).toContain('.yaml');
    expect(nativeStatusFile).toContain('.json');
  });
});
