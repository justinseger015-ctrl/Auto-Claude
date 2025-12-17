/**
 * QA Integration Service for unified QA loop handling.
 *
 * Provides framework-aware QA operations including:
 * - BMAD TEA (Test Engineering Architect) workflows
 * - Native Auto Claude QA reviewer/fixer loop
 *
 * Epic 5: TEA + QA Loop Integration (Stories 5-1 to 5-5)
 */

import path from 'path';
import { existsSync, readFileSync } from 'fs';
import type { Project, Task } from '../shared/types';
import { isBMADProject } from './framework-router';

/**
 * QA operation types supported by the integration.
 */
export type QAOperation =
  | 'review'          // Run QA review
  | 'fix'             // Fix QA issues
  | 'test_design'     // Design test plan (BMAD TEA)
  | 'test_automate'   // Automate tests (BMAD TEA)
  | 'test_trace'      // Trace requirements to tests (BMAD TEA)
  | 'atdd'            // Acceptance TDD (BMAD TEA)
  | 'nfr_check';      // Non-functional requirements check (BMAD TEA)

/**
 * QA command configuration.
 */
export interface QACommand {
  /** The command to execute */
  command: string;
  /** Arguments for the command */
  args: string[];
  /** Working directory */
  cwd: string;
  /** Environment variables */
  env?: Record<string, string>;
  /** Description of the operation */
  description: string;
}

/**
 * QA report from the QA process.
 */
export interface QAReport {
  /** Whether the QA passed */
  passed: boolean;
  /** Issues found during QA */
  issues: QAIssue[];
  /** Summary of the QA run */
  summary: string;
  /** Timestamp of the report */
  timestamp: Date;
  /** Framework that generated the report */
  framework: 'bmad' | 'native';
}

/**
 * Individual QA issue.
 */
export interface QAIssue {
  /** Unique identifier */
  id: string;
  /** Severity level */
  severity: 'critical' | 'major' | 'minor' | 'info';
  /** Issue type */
  type: 'test_failure' | 'coverage_gap' | 'code_quality' | 'acceptance_criteria' | 'other';
  /** Description of the issue */
  description: string;
  /** File path related to the issue */
  file?: string;
  /** Line number in the file */
  line?: number;
  /** Suggested fix */
  suggestion?: string;
}

/**
 * BMAD TEA workflow mappings.
 */
const BMAD_TEA_WORKFLOWS: Record<QAOperation, string> = {
  review: 'testarch-test-review',
  fix: 'code-review',  // BMAD uses code-review for fixing
  test_design: 'testarch-test-design',
  test_automate: 'testarch-automate',
  test_trace: 'testarch-trace',
  atdd: 'testarch-atdd',
  nfr_check: 'testarch-nfr',
};

/**
 * Get QA command for the specified operation and framework.
 */
export function getQACommand(
  project: Project,
  operation: QAOperation,
  task?: Task
): QACommand {
  if (isBMADProject(project)) {
    return getBMADQACommand(project, operation, task);
  }
  return getNativeQACommand(project, operation, task);
}

/**
 * Get BMAD TEA QA command.
 */
function getBMADQACommand(
  project: Project,
  operation: QAOperation,
  task?: Task
): QACommand {
  const workflow = BMAD_TEA_WORKFLOWS[operation];
  const bmadOutputPath = path.join(project.path, '_bmad-output');

  const args = ['--print', `/bmad:bmm:workflows:${workflow}`];

  // Add task context if available
  if (task) {
    args.push('--input', JSON.stringify({
      story_key: task.specId,
      project_path: project.path,
    }));
  }

  const descriptions: Record<QAOperation, string> = {
    review: 'Running TEA test quality review',
    fix: 'Running code review to fix issues',
    test_design: 'Designing test plan with TEA',
    test_automate: 'Automating tests with TEA',
    test_trace: 'Generating requirements traceability matrix',
    atdd: 'Running acceptance test-driven development',
    nfr_check: 'Checking non-functional requirements',
  };

  return {
    command: 'claude',
    args,
    cwd: project.path,
    env: {
      BMAD_PROJECT_PATH: project.path,
      BMAD_OUTPUT_PATH: bmadOutputPath,
    },
    description: descriptions[operation],
  };
}

/**
 * Get Native Auto Claude QA command.
 */
function getNativeQACommand(
  project: Project,
  operation: QAOperation,
  task?: Task
): QACommand {
  const autoBuildPath = project.autoBuildPath || path.join(project.path, '.auto-claude');

  // Native framework only supports review and fix operations
  const supportedOps: QAOperation[] = ['review', 'fix'];

  if (!supportedOps.includes(operation)) {
    // Return a no-op for unsupported operations
    return {
      command: 'echo',
      args: [`Operation '${operation}' not supported in native framework`],
      cwd: project.path,
      description: `Unsupported operation: ${operation}`,
    };
  }

  const args: string[] = [];

  if (task) {
    args.push('--spec', task.specId);
  }

  if (operation === 'review') {
    args.push('--qa');
  } else if (operation === 'fix') {
    args.push('--qa', '--fix');
  }

  return {
    command: 'python',
    args: ['run.py', ...args],
    cwd: project.path,
    env: {
      AUTO_BUILD_PATH: autoBuildPath,
    },
    description: operation === 'review' ? 'Running QA review' : 'Running QA fixer',
  };
}

/**
 * Parse QA report from file.
 */
export function parseQAReport(project: Project, taskId: string): QAReport | null {
  if (isBMADProject(project)) {
    return parseBMADQAReport(project, taskId);
  }
  return parseNativeQAReport(project, taskId);
}

/**
 * Parse BMAD TEA QA report.
 */
function parseBMADQAReport(project: Project, taskId: string): QAReport | null {
  const reportPath = path.join(
    project.path,
    '_bmad-output',
    'stories',
    taskId,
    'test-review.md'
  );

  if (!existsSync(reportPath)) {
    return null;
  }

  try {
    const content = readFileSync(reportPath, 'utf-8');
    return parseTEAReportContent(content);
  } catch {
    return null;
  }
}

/**
 * Parse Native QA report.
 */
function parseNativeQAReport(project: Project, taskId: string): QAReport | null {
  const autoBuildPath = project.autoBuildPath || '.auto-claude';
  const basePath = path.isAbsolute(autoBuildPath)
    ? autoBuildPath
    : path.join(project.path, autoBuildPath);
  const reportPath = path.join(basePath, 'specs', taskId, 'qa_report.md');

  if (!existsSync(reportPath)) {
    return null;
  }

  try {
    const content = readFileSync(reportPath, 'utf-8');
    return parseNativeReportContent(content);
  } catch {
    return null;
  }
}

/**
 * Parse TEA report content.
 */
function parseTEAReportContent(content: string): QAReport {
  const issues: QAIssue[] = [];
  let passed = true;

  // Look for issue patterns in the report
  const issueMatches = content.matchAll(/(?:FAIL|WARN|ERROR|ISSUE):\s*(.+?)(?=\n(?:FAIL|WARN|ERROR|ISSUE|$))/gis);

  for (const match of issueMatches) {
    const issueText = match[1].trim();
    const severity = determineSeverity(match[0]);
    passed = severity === 'critical' || severity === 'major' ? false : passed;

    issues.push({
      id: `tea-${issues.length + 1}`,
      severity,
      type: determineIssueType(issueText),
      description: issueText,
    });
  }

  // Check for explicit pass/fail
  if (content.toLowerCase().includes('all tests passed') || content.toLowerCase().includes('qa passed')) {
    passed = true;
  }
  if (content.toLowerCase().includes('tests failed') || content.toLowerCase().includes('qa failed')) {
    passed = false;
  }

  return {
    passed,
    issues,
    summary: extractSummary(content),
    timestamp: new Date(),
    framework: 'bmad',
  };
}

/**
 * Parse Native report content.
 */
function parseNativeReportContent(content: string): QAReport {
  const issues: QAIssue[] = [];
  let passed = true;

  // Native reports have a specific format
  // Look for acceptance criteria failures
  const acMatches = content.matchAll(/(?:AC|Acceptance Criteria)\s*#?(\d+)[:\s]+(?:FAIL|FAILED)/gi);
  for (const match of acMatches) {
    passed = false;
    issues.push({
      id: `native-ac-${match[1]}`,
      severity: 'major',
      type: 'acceptance_criteria',
      description: `Acceptance Criteria #${match[1]} failed`,
    });
  }

  // Look for test failures
  const testMatches = content.matchAll(/(?:Test|FAIL):\s*(.+?)(?=\n|$)/gi);
  for (const match of testMatches) {
    if (match[1].toLowerCase().includes('fail')) {
      passed = false;
      issues.push({
        id: `native-test-${issues.length + 1}`,
        severity: 'major',
        type: 'test_failure',
        description: match[1].trim(),
      });
    }
  }

  // Check for explicit status
  if (content.toLowerCase().includes('qa status: passed') || content.toLowerCase().includes('all criteria met')) {
    passed = true;
  }
  if (content.toLowerCase().includes('qa status: failed') || content.toLowerCase().includes('criteria not met')) {
    passed = false;
  }

  return {
    passed,
    issues,
    summary: extractSummary(content),
    timestamp: new Date(),
    framework: 'native',
  };
}

/**
 * Determine severity from issue marker.
 */
function determineSeverity(marker: string): QAIssue['severity'] {
  const upper = marker.toUpperCase();
  if (upper.includes('ERROR') || upper.includes('FAIL')) return 'critical';
  if (upper.includes('WARN')) return 'major';
  if (upper.includes('INFO')) return 'info';
  return 'minor';
}

/**
 * Determine issue type from description.
 */
function determineIssueType(description: string): QAIssue['type'] {
  const lower = description.toLowerCase();
  if (lower.includes('test') && (lower.includes('fail') || lower.includes('error'))) {
    return 'test_failure';
  }
  if (lower.includes('coverage') || lower.includes('untested')) {
    return 'coverage_gap';
  }
  if (lower.includes('quality') || lower.includes('lint') || lower.includes('style')) {
    return 'code_quality';
  }
  if (lower.includes('acceptance') || lower.includes('criteria') || lower.includes('requirement')) {
    return 'acceptance_criteria';
  }
  return 'other';
}

/**
 * Extract summary from report content.
 */
function extractSummary(content: string): string {
  // Look for summary section
  const summaryMatch = content.match(/(?:Summary|Overview|Conclusion)[\s:]+(.+?)(?=\n\n|$)/is);
  if (summaryMatch) {
    return summaryMatch[1].trim().substring(0, 500);
  }

  // Fall back to first paragraph
  const firstPara = content.split('\n\n')[0];
  return firstPara.substring(0, 500);
}

/**
 * Check if a QA operation is available for the given framework.
 */
export function isQAOperationAvailable(
  project: Project,
  operation: QAOperation
): boolean {
  if (isBMADProject(project)) {
    // BMAD TEA supports all operations
    return true;
  }

  // Native only supports review and fix
  return operation === 'review' || operation === 'fix';
}

/**
 * Get all available QA operations for a project.
 */
export function getAvailableQAOperations(project: Project): QAOperation[] {
  if (isBMADProject(project)) {
    return ['review', 'fix', 'test_design', 'test_automate', 'test_trace', 'atdd', 'nfr_check'];
  }
  return ['review', 'fix'];
}

/**
 * Get QA operation description.
 */
export function getQAOperationDescription(operation: QAOperation): string {
  const descriptions: Record<QAOperation, string> = {
    review: 'Run quality assurance review',
    fix: 'Fix issues found during QA',
    test_design: 'Design test plan for the implementation',
    test_automate: 'Generate automated tests',
    test_trace: 'Generate requirements traceability matrix',
    atdd: 'Run acceptance test-driven development',
    nfr_check: 'Check non-functional requirements',
  };
  return descriptions[operation];
}

export default {
  getQACommand,
  parseQAReport,
  isQAOperationAvailable,
  getAvailableQAOperations,
  getQAOperationDescription,
};
