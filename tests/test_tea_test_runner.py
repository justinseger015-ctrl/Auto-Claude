"""Tests for TEA test runner module."""
import pytest
from pathlib import Path


def test_test_runner_imports():
    """Test test runner module can be imported."""
    from integrations.tea.test_runner import (
        TestOutcome,
        TestCaseResult,
        TestRunResult,
        run_tea_tests,
        build_fix_context,
        extract_test_failures,
    )
    assert TestOutcome is not None
    assert TestRunResult is not None


def test_test_outcome_enum():
    """Test TestOutcome enum values."""
    from integrations.tea import TestOutcome

    assert TestOutcome.PASSED.value == "passed"
    assert TestOutcome.FAILED.value == "failed"
    assert TestOutcome.ERROR.value == "error"
    assert TestOutcome.SKIPPED.value == "skipped"


def test_test_case_result_dataclass():
    """Test TestCaseResult dataclass."""
    from integrations.tea import TestCaseResult, TestOutcome

    result = TestCaseResult(
        name="test_example",
        outcome=TestOutcome.FAILED,
        duration=0.5,
        error_message="AssertionError: expected True",
        file_path="test_example.py",
        line_number=42,
    )

    assert result.name == "test_example"
    assert result.outcome == TestOutcome.FAILED
    assert result.error_message == "AssertionError: expected True"


def test_test_run_result_dataclass():
    """Test TestRunResult dataclass."""
    from integrations.tea import TestRunResult, TestCaseResult, TestOutcome

    result = TestRunResult(
        passed=False,
        total=3,
        passed_count=1,
        failed_count=1,
        error_count=1,
        skipped_count=0,
        duration=1.5,
        test_cases=[
            TestCaseResult("test_pass", TestOutcome.PASSED, 0.5),
            TestCaseResult("test_fail", TestOutcome.FAILED, 0.5, "Error"),
            TestCaseResult("test_error", TestOutcome.ERROR, 0.5, "Exception"),
        ],
        raw_output="Test output...",
    )

    assert result.total == 3
    assert result.passed_count == 1
    assert result.failed_count == 1
    assert len(result.test_cases) == 3


def test_build_fix_context():
    """Test fix context building."""
    from integrations.tea import build_fix_context

    issues = [
        {
            "type": "test_failure",
            "test_name": "test_example",
            "error": "AssertionError: expected True",
            "file": "test_example.py",
        }
    ]

    context = build_fix_context(issues)

    assert "Issues to Fix" in context
    assert "test_example" in context
    assert "AssertionError" in context
    assert "Do NOT modify the test assertions" in context


def test_build_fix_context_multiple_issues():
    """Test fix context with multiple issues."""
    from integrations.tea import build_fix_context

    issues = [
        {"type": "test_failure", "test_name": "test_1", "error": "Error 1"},
        {"type": "test_failure", "test_name": "test_2", "error": "Error 2"},
        {"type": "test_failure", "test_name": "test_3", "error": "Error 3"},
    ]

    context = build_fix_context(issues)

    assert "Issue 1" in context
    assert "Issue 2" in context
    assert "Issue 3" in context


def test_extract_test_failures():
    """Test extracting failures from test result."""
    from integrations.tea import extract_test_failures, TestRunResult, TestCaseResult, TestOutcome

    result = TestRunResult(
        passed=False,
        total=4,
        passed_count=2,
        failed_count=1,
        error_count=1,
        skipped_count=0,
        duration=1.0,
        test_cases=[
            TestCaseResult("test_pass_1", TestOutcome.PASSED, 0.1),
            TestCaseResult("test_pass_2", TestOutcome.PASSED, 0.1),
            TestCaseResult("test_fail", TestOutcome.FAILED, 0.1, "Failed assertion"),
            TestCaseResult("test_error", TestOutcome.ERROR, 0.1, "Exception raised"),
        ],
    )

    issues = extract_test_failures(result)

    assert len(issues) == 2
    assert issues[0]["test_name"] == "test_fail"
    assert issues[1]["test_name"] == "test_error"


def test_extract_test_failures_all_pass():
    """Test extracting failures when all tests pass."""
    from integrations.tea import extract_test_failures, TestRunResult, TestCaseResult, TestOutcome

    result = TestRunResult(
        passed=True,
        total=2,
        passed_count=2,
        failed_count=0,
        error_count=0,
        skipped_count=0,
        duration=0.5,
        test_cases=[
            TestCaseResult("test_1", TestOutcome.PASSED, 0.25),
            TestCaseResult("test_2", TestOutcome.PASSED, 0.25),
        ],
    )

    issues = extract_test_failures(result)

    assert len(issues) == 0


def test_parse_pytest_stdout():
    """Test parsing pytest stdout."""
    from integrations.tea.test_runner import parse_pytest_stdout

    stdout = """
tests/test_example.py::test_pass PASSED
tests/test_example.py::test_fail FAILED
tests/test_example.py::test_skip SKIPPED

======= 1 passed, 1 failed, 1 skipped in 0.5s =======
"""

    result = parse_pytest_stdout(stdout, stdout)

    assert result.passed_count == 1
    assert result.failed_count == 1
    assert result.skipped_count == 1
    assert not result.passed


def test_parse_pytest_report():
    """Test parsing pytest JSON report."""
    from integrations.tea.test_runner import parse_pytest_report

    report = {
        "summary": {"total": 3, "passed": 2, "failed": 1, "error": 0, "skipped": 0},
        "tests": [
            {"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.1},
            {"nodeid": "test.py::test_2", "outcome": "passed", "duration": 0.1},
            {"nodeid": "test.py::test_3", "outcome": "failed", "duration": 0.2,
             "call": {"longrepr": "AssertionError"}},
        ],
        "duration": 0.4,
    }

    result = parse_pytest_report(report, "")

    assert result.total == 3
    assert result.passed_count == 2
    assert result.failed_count == 1
    assert not result.passed
    assert len(result.test_cases) == 3


def test_parse_go_test_output():
    """Test parsing Go test output."""
    from integrations.tea.test_runner import parse_go_test_output

    stdout = """
{"Time":"2024-01-01T00:00:00Z","Action":"run","Test":"TestExample"}
{"Time":"2024-01-01T00:00:01Z","Action":"pass","Test":"TestExample","Elapsed":1.0}
{"Time":"2024-01-01T00:00:01Z","Action":"run","Test":"TestFailing"}
{"Time":"2024-01-01T00:00:02Z","Action":"fail","Test":"TestFailing","Elapsed":1.0}
"""

    result = parse_go_test_output(stdout, stdout)

    assert result.passed_count == 1
    assert result.failed_count == 1
    assert not result.passed


def test_parse_cargo_test_output():
    """Test parsing Cargo test output."""
    from integrations.tea.test_runner import parse_cargo_test_output

    output = """
running 3 tests
test test_1 ... ok
test test_2 ... ok
test test_3 ... FAILED

failures:
    test_3

test result: FAILED. 2 passed; 1 failed; 0 ignored
"""

    result = parse_cargo_test_output(output)

    assert result.passed_count == 2
    assert result.failed_count == 1
    assert not result.passed
