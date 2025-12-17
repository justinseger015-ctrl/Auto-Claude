"""TEA test runner for QA loop integration."""

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .models import TestFramework
from .commands import get_test_command

logger = logging.getLogger(__name__)


class TestOutcome(Enum):
    """Test execution outcome."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestCaseResult:
    """Result for a single test case."""
    name: str
    outcome: TestOutcome
    duration: float = 0.0
    error_message: str = ""
    file_path: str = ""
    line_number: int = 0


@dataclass
class TestRunResult:
    """Result of a test run."""
    passed: bool
    total: int
    passed_count: int
    failed_count: int
    error_count: int
    skipped_count: int
    duration: float
    test_cases: list[TestCaseResult] = field(default_factory=list)
    raw_output: str = ""


async def run_tea_tests(
    test_files: list[Path],
    framework: TestFramework,
    project_path: Path,
) -> TestRunResult:
    """Run TEA-generated tests.

    Args:
        test_files: List of test file paths
        framework: Test framework
        project_path: Project root

    Returns:
        TestRunResult with detailed outcomes
    """
    if framework == TestFramework.PYTEST:
        return await run_pytest(test_files, project_path)
    elif framework in (TestFramework.JEST, TestFramework.VITEST):
        return await run_jest(test_files, project_path)
    elif framework == TestFramework.GO_TEST:
        return await run_go_test(test_files, project_path)
    elif framework == TestFramework.CARGO_TEST:
        return await run_cargo_test(test_files, project_path)
    else:
        logger.warning(f"Unsupported framework {framework}, using generic runner")
        return await run_generic(test_files, project_path)


async def run_pytest(test_files: list[Path], project_path: Path) -> TestRunResult:
    """Run pytest and parse results."""
    try:
        # Try with JSON report first
        report_file = project_path / ".pytest_report.json"

        result = subprocess.run(
            ["pytest"] + [str(f) for f in test_files] + [
                "--tb=short",
                "-v",
                f"--json-report-file={report_file}",
            ],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )

        raw_output = result.stdout + result.stderr

        # Try to parse JSON report
        if report_file.exists():
            try:
                with open(report_file) as f:
                    report = json.load(f)
                return parse_pytest_report(report, raw_output)
            except json.JSONDecodeError:
                pass
            finally:
                report_file.unlink(missing_ok=True)

        # Fallback to parsing stdout
        return parse_pytest_stdout(result.stdout, raw_output)

    except subprocess.TimeoutExpired:
        logger.error("Pytest timed out")
        return TestRunResult(
            passed=False,
            total=0,
            passed_count=0,
            failed_count=0,
            error_count=1,
            skipped_count=0,
            duration=300,
            raw_output="Test execution timed out",
        )
    except FileNotFoundError:
        logger.error("pytest not found")
        return TestRunResult(
            passed=False,
            total=0,
            passed_count=0,
            failed_count=0,
            error_count=1,
            skipped_count=0,
            duration=0,
            raw_output="pytest command not found",
        )


def parse_pytest_report(report: dict, raw_output: str) -> TestRunResult:
    """Parse pytest JSON report."""
    summary = report.get("summary", {})
    tests = report.get("tests", [])

    test_cases = []
    for test in tests:
        outcome_str = test.get("outcome", "passed")
        outcome = TestOutcome.PASSED
        if outcome_str == "failed":
            outcome = TestOutcome.FAILED
        elif outcome_str == "error":
            outcome = TestOutcome.ERROR
        elif outcome_str == "skipped":
            outcome = TestOutcome.SKIPPED

        error_msg = ""
        if "call" in test and "longrepr" in test["call"]:
            error_msg = str(test["call"]["longrepr"])[:500]

        nodeid = test.get("nodeid", "")
        file_path = nodeid.split("::")[0] if "::" in nodeid else nodeid

        test_cases.append(TestCaseResult(
            name=nodeid,
            outcome=outcome,
            duration=test.get("duration", 0),
            error_message=error_msg,
            file_path=file_path,
        ))

    return TestRunResult(
        passed=summary.get("failed", 0) == 0 and summary.get("error", 0) == 0,
        total=summary.get("total", len(test_cases)),
        passed_count=summary.get("passed", 0),
        failed_count=summary.get("failed", 0),
        error_count=summary.get("error", 0),
        skipped_count=summary.get("skipped", 0),
        duration=report.get("duration", 0),
        test_cases=test_cases,
        raw_output=raw_output,
    )


def parse_pytest_stdout(stdout: str, raw_output: str) -> TestRunResult:
    """Parse pytest output from stdout."""
    test_cases = []
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    # Parse summary line: "2 passed, 1 failed, 1 error in 0.5s"
    summary_match = re.search(
        r"(\d+) passed.*?(\d+) failed|(\d+) passed",
        stdout
    )

    for line in stdout.split("\n"):
        # Match: test_file.py::test_name PASSED/FAILED
        test_match = re.match(r"(.+::[\w_]+)\s+(PASSED|FAILED|ERROR|SKIPPED)", line)
        if test_match:
            name = test_match.group(1)
            result_str = test_match.group(2)

            outcome = TestOutcome.PASSED
            if result_str == "FAILED":
                outcome = TestOutcome.FAILED
                failed += 1
            elif result_str == "ERROR":
                outcome = TestOutcome.ERROR
                errors += 1
            elif result_str == "SKIPPED":
                outcome = TestOutcome.SKIPPED
                skipped += 1
            else:
                passed += 1

            test_cases.append(TestCaseResult(
                name=name,
                outcome=outcome,
                duration=0,
            ))

    total = passed + failed + errors + skipped

    return TestRunResult(
        passed=failed == 0 and errors == 0,
        total=total,
        passed_count=passed,
        failed_count=failed,
        error_count=errors,
        skipped_count=skipped,
        duration=0,
        test_cases=test_cases,
        raw_output=raw_output,
    )


async def run_jest(test_files: list[Path], project_path: Path) -> TestRunResult:
    """Run jest/vitest and parse results."""
    try:
        result = subprocess.run(
            ["npm", "test", "--", "--json"] + [str(f) for f in test_files],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )

        raw_output = result.stdout + result.stderr

        # Try to parse JSON output
        try:
            # Find JSON in output (may be mixed with other output)
            json_start = result.stdout.find("{")
            if json_start >= 0:
                report = json.loads(result.stdout[json_start:])
                return parse_jest_report(report, raw_output)
        except json.JSONDecodeError:
            pass

        # Fallback to basic parsing
        return parse_jest_stdout(result.stdout, raw_output, result.returncode)

    except subprocess.TimeoutExpired:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=300,
            raw_output="Test execution timed out",
        )
    except FileNotFoundError:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=0,
            raw_output="npm command not found",
        )


def parse_jest_report(report: dict, raw_output: str) -> TestRunResult:
    """Parse Jest JSON report."""
    test_cases = []

    for result in report.get("testResults", []):
        for assertion in result.get("assertionResults", []):
            status = assertion.get("status", "passed")
            outcome = TestOutcome.PASSED
            if status == "failed":
                outcome = TestOutcome.FAILED
            elif status == "pending":
                outcome = TestOutcome.SKIPPED

            test_cases.append(TestCaseResult(
                name=assertion.get("fullName", assertion.get("title", "Unknown")),
                outcome=outcome,
                duration=assertion.get("duration", 0) / 1000,  # ms to seconds
                error_message="\n".join(assertion.get("failureMessages", []))[:500],
                file_path=result.get("name", ""),
            ))

    passed = sum(1 for tc in test_cases if tc.outcome == TestOutcome.PASSED)
    failed = sum(1 for tc in test_cases if tc.outcome == TestOutcome.FAILED)
    skipped = sum(1 for tc in test_cases if tc.outcome == TestOutcome.SKIPPED)

    return TestRunResult(
        passed=report.get("success", failed == 0),
        total=len(test_cases),
        passed_count=passed,
        failed_count=failed,
        error_count=0,
        skipped_count=skipped,
        duration=report.get("testResults", [{}])[0].get("endTime", 0) / 1000 if report.get("testResults") else 0,
        test_cases=test_cases,
        raw_output=raw_output,
    )


def parse_jest_stdout(stdout: str, raw_output: str, returncode: int) -> TestRunResult:
    """Parse Jest output from stdout (basic)."""
    # Jest basic output: Tests: 2 passed, 1 failed, 3 total
    match = re.search(r"Tests:\s*(\d+)\s+passed.*?(\d+)\s+failed.*?(\d+)\s+total", stdout)

    if match:
        passed = int(match.group(1))
        failed = int(match.group(2))
        total = int(match.group(3))
    else:
        passed = 0
        failed = 1 if returncode != 0 else 0
        total = 1

    return TestRunResult(
        passed=returncode == 0,
        total=total,
        passed_count=passed,
        failed_count=failed,
        error_count=0,
        skipped_count=0,
        duration=0,
        raw_output=raw_output,
    )


async def run_go_test(test_files: list[Path], project_path: Path) -> TestRunResult:
    """Run go test and parse results."""
    try:
        # Get unique packages
        packages = list({f.parent for f in test_files})

        result = subprocess.run(
            ["go", "test", "-v", "-json"] + [f"./{p.relative_to(project_path)}/..." for p in packages],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "CGO_ENABLED": "0"},
        )

        raw_output = result.stdout + result.stderr
        return parse_go_test_output(result.stdout, raw_output)

    except subprocess.TimeoutExpired:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=300,
            raw_output="Test execution timed out",
        )
    except FileNotFoundError:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=0,
            raw_output="go command not found",
        )


def parse_go_test_output(stdout: str, raw_output: str) -> TestRunResult:
    """Parse go test -json output."""
    test_cases = []
    test_results = {}

    for line in stdout.split("\n"):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
            action = event.get("Action")
            test_name = event.get("Test")

            if test_name and action in ("pass", "fail", "skip"):
                outcome = TestOutcome.PASSED
                if action == "fail":
                    outcome = TestOutcome.FAILED
                elif action == "skip":
                    outcome = TestOutcome.SKIPPED

                test_results[test_name] = TestCaseResult(
                    name=test_name,
                    outcome=outcome,
                    duration=event.get("Elapsed", 0),
                    file_path=event.get("Package", ""),
                )

        except json.JSONDecodeError:
            # Fall back to regex parsing for non-JSON output
            fail_match = re.match(r"--- FAIL: (\w+)", line)
            if fail_match:
                test_results[fail_match.group(1)] = TestCaseResult(
                    name=fail_match.group(1),
                    outcome=TestOutcome.FAILED,
                    duration=0,
                )

            pass_match = re.match(r"--- PASS: (\w+)", line)
            if pass_match:
                test_results[pass_match.group(1)] = TestCaseResult(
                    name=pass_match.group(1),
                    outcome=TestOutcome.PASSED,
                    duration=0,
                )

    test_cases = list(test_results.values())
    passed = sum(1 for tc in test_cases if tc.outcome == TestOutcome.PASSED)
    failed = sum(1 for tc in test_cases if tc.outcome == TestOutcome.FAILED)
    skipped = sum(1 for tc in test_cases if tc.outcome == TestOutcome.SKIPPED)

    return TestRunResult(
        passed=failed == 0,
        total=len(test_cases),
        passed_count=passed,
        failed_count=failed,
        error_count=0,
        skipped_count=skipped,
        duration=0,
        test_cases=test_cases,
        raw_output=raw_output,
    )


async def run_cargo_test(test_files: list[Path], project_path: Path) -> TestRunResult:
    """Run cargo test and parse results."""
    try:
        result = subprocess.run(
            ["cargo", "test", "--", "--nocapture"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
        )

        raw_output = result.stdout + result.stderr
        return parse_cargo_test_output(raw_output)

    except subprocess.TimeoutExpired:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=300,
            raw_output="Test execution timed out",
        )
    except FileNotFoundError:
        return TestRunResult(
            passed=False, total=0, passed_count=0, failed_count=0,
            error_count=1, skipped_count=0, duration=0,
            raw_output="cargo command not found",
        )


def parse_cargo_test_output(raw_output: str) -> TestRunResult:
    """Parse cargo test output."""
    # Parse summary: test result: ok. 3 passed; 1 failed; 0 ignored
    summary_match = re.search(
        r"test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored",
        raw_output
    )

    if summary_match:
        status = summary_match.group(1)
        passed = int(summary_match.group(2))
        failed = int(summary_match.group(3))
        skipped = int(summary_match.group(4))
        total = passed + failed + skipped

        return TestRunResult(
            passed=status == "ok",
            total=total,
            passed_count=passed,
            failed_count=failed,
            error_count=0,
            skipped_count=skipped,
            duration=0,
            raw_output=raw_output,
        )

    # Fallback for no summary
    return TestRunResult(
        passed=False,
        total=0,
        passed_count=0,
        failed_count=0,
        error_count=1,
        skipped_count=0,
        duration=0,
        raw_output=raw_output,
    )


async def run_generic(test_files: list[Path], project_path: Path) -> TestRunResult:
    """Generic test runner fallback."""
    return TestRunResult(
        passed=False,
        total=0,
        passed_count=0,
        failed_count=0,
        error_count=1,
        skipped_count=0,
        duration=0,
        raw_output="No supported test framework detected",
    )


def build_fix_context(issues: list[dict]) -> str:
    """Build context string for QA fixer.

    Args:
        issues: List of issues to fix

    Returns:
        Formatted context string
    """
    lines = ["## Issues to Fix\n"]

    for i, issue in enumerate(issues, 1):
        lines.append(f"### Issue {i}: {issue.get('type', 'Unknown')}")

        if issue.get('test_name'):
            lines.append(f"**Test:** `{issue['test_name']}`")

        if issue.get('file'):
            lines.append(f"**File:** `{issue['file']}`")

        if issue.get('error'):
            error_truncated = issue['error'][:500]
            lines.append(f"**Error:**\n```\n{error_truncated}\n```")

        lines.append("")

    lines.append("""
## Fix Instructions

1. Read the failing test carefully
2. Understand what the test expects
3. Modify the implementation to make the test pass
4. Do NOT modify the test assertions
5. Run the test again to verify the fix
""")

    return "\n".join(lines)


def extract_test_failures(result: TestRunResult) -> list[dict]:
    """Extract failure details from test result.

    Args:
        result: Test run result

    Returns:
        List of issue dicts for QA fixer
    """
    issues = []

    for tc in result.test_cases:
        if tc.outcome in (TestOutcome.FAILED, TestOutcome.ERROR):
            issues.append({
                "type": "test_failure",
                "test_name": tc.name,
                "error": tc.error_message,
                "file": tc.file_path,
                "line": tc.line_number,
            })

    return issues
