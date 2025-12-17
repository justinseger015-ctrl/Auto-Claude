"""Tests for TEA traceability module."""
import pytest
from pathlib import Path


def test_trace_module_imports():
    """Test trace module can be imported."""
    from integrations.tea.trace import (
        TraceabilityMatrix,
        generate_traceability_matrix,
        format_traceability_report,
    )
    assert TraceabilityMatrix is not None
    assert generate_traceability_matrix is not None


def test_traceability_matrix_dataclass():
    """Test TraceabilityMatrix dataclass."""
    from integrations.tea import TraceabilityMatrix

    matrix = TraceabilityMatrix(
        requirement_coverage={"ac-1": ["tc-1", "tc-2"]},
        uncovered_requirements=["ac-3"],
        tests_without_requirement=["tc-5"],
        coverage_percentage=66.7,
        quality_gate_passed=False,
    )

    assert matrix.coverage_percentage == 66.7
    assert not matrix.quality_gate_passed
    assert "ac-3" in matrix.uncovered_requirements


@pytest.mark.asyncio
async def test_generate_traceability_matrix(tmp_path):
    """Test traceability matrix generation."""
    from integrations.tea import generate_traceability_matrix, TestPlan, TestCase, TestFramework

    # Create story file
    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("""# Story

## Acceptance Criteria

1. **Given** A **When** B **Then** C

2. **Given** D **When** E **Then** F
""")

    # Create test plan covering AC 1 but not AC 2
    test_plan = TestPlan(
        story_id="1-1-test",
        framework=TestFramework.PYTEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Test AC1",
                description="Tests AC 1",
                acceptance_criteria_id="ac-1",
                given="A",
                when="B",
                then="C",
                priority="high",
            ),
        ],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={"ac-1": ["tc-1"]},
    )

    matrix = await generate_traceability_matrix(story_path, test_plan, tmp_path)

    assert matrix.coverage_percentage == 50.0  # 1 of 2 ACs covered
    assert "ac-2" in matrix.uncovered_requirements
    assert not matrix.quality_gate_passed


@pytest.mark.asyncio
async def test_generate_traceability_full_coverage(tmp_path):
    """Test traceability with full coverage."""
    from integrations.tea import generate_traceability_matrix, TestPlan, TestCase, TestFramework

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("""# Story

## Acceptance Criteria

1. **Given** A **When** B **Then** C
""")

    test_plan = TestPlan(
        story_id="1-1-test",
        framework=TestFramework.PYTEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Test AC1",
                description="Tests AC 1",
                acceptance_criteria_id="ac-1",
                given="A",
                when="B",
                then="C",
                priority="high",
            ),
        ],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={"ac-1": ["tc-1"]},
    )

    matrix = await generate_traceability_matrix(story_path, test_plan, tmp_path)

    assert matrix.coverage_percentage == 100.0
    assert len(matrix.uncovered_requirements) == 0
    assert matrix.quality_gate_passed


def test_format_traceability_report_passed():
    """Test formatting passed traceability report."""
    from integrations.tea import format_traceability_report, TraceabilityMatrix

    matrix = TraceabilityMatrix(
        requirement_coverage={"ac-1": ["tc-1"]},
        uncovered_requirements=[],
        tests_without_requirement=[],
        coverage_percentage=100.0,
        quality_gate_passed=True,
    )

    report = format_traceability_report(matrix)

    assert "Traceability Matrix Report" in report
    assert "100.0%" in report
    assert "✅ PASSED" in report


def test_format_traceability_report_failed():
    """Test formatting failed traceability report."""
    from integrations.tea import format_traceability_report, TraceabilityMatrix

    matrix = TraceabilityMatrix(
        requirement_coverage={"ac-1": ["tc-1"]},
        uncovered_requirements=["ac-2", "ac-3"],
        tests_without_requirement=["tc-orphan"],
        coverage_percentage=33.3,
        quality_gate_passed=False,
    )

    report = format_traceability_report(matrix)

    assert "❌ FAILED" in report
    assert "Uncovered Requirements" in report
    assert "ac-2" in report
    assert "tc-orphan" in report
