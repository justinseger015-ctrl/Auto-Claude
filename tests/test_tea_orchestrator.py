"""Tests for TEA orchestrator module."""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock


def test_orchestrator_imports():
    """Test orchestrator module can be imported."""
    from integrations.tea.orchestrator import (
        run_tea_for_tier,
        should_run_tea,
        get_tea_workflows_for_tier,
        format_tea_summary,
        TEAResult,
    )
    assert run_tea_for_tier is not None
    assert TEAResult is not None


def test_should_run_tea_simple():
    """Test TEA should not run for simple tier."""
    from integrations.tea import should_run_tea

    assert should_run_tea("simple") is False
    assert should_run_tea("quick-flow") is False


def test_should_run_tea_standard():
    """Test TEA should run for standard tier."""
    from integrations.tea import should_run_tea

    assert should_run_tea("standard") is True
    assert should_run_tea("method") is True


def test_should_run_tea_complex():
    """Test TEA should run for complex tier."""
    from integrations.tea import should_run_tea

    assert should_run_tea("complex") is True
    assert should_run_tea("enterprise") is True


def test_get_tea_workflows_simple():
    """Test no workflows for simple tier."""
    from integrations.tea import get_tea_workflows_for_tier

    workflows = get_tea_workflows_for_tier("simple")
    assert workflows == []


def test_get_tea_workflows_standard():
    """Test standard tier workflows."""
    from integrations.tea import get_tea_workflows_for_tier

    workflows = get_tea_workflows_for_tier("standard")
    assert "test-design" in workflows
    assert "atdd" in workflows
    assert "trace" not in workflows


def test_get_tea_workflows_complex():
    """Test complex tier workflows."""
    from integrations.tea import get_tea_workflows_for_tier

    workflows = get_tea_workflows_for_tier("complex")
    assert "test-design" in workflows
    assert "atdd" in workflows
    assert "trace" in workflows
    assert "nfr-assess" in workflows


@pytest.mark.asyncio
async def test_run_tea_skips_for_simple(tmp_path):
    """Test TEA is skipped for simple tier."""
    from integrations.tea import run_tea_for_tier

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("# Story\n## Acceptance Criteria\n1. Test")

    result = await run_tea_for_tier("simple", story_path, tmp_path)

    assert result.depth == "none"
    assert result.test_plan is None
    assert result.test_files == []
    assert result.success is True


@pytest.mark.asyncio
async def test_run_tea_standard_generates_tests(tmp_path):
    """Test TEA generates tests for standard tier."""
    from integrations.tea import run_tea_for_tier, TestPlan, TestFramework

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("""# Story

## Acceptance Criteria

1. **Given** X **When** Y **Then** Z
""")

    # Create pytest.ini for framework detection
    (tmp_path / "pytest.ini").write_text("[pytest]")

    # Mock the TEA agent
    mock_plan = TestPlan(
        story_id="1-1-test",
        framework=TestFramework.PYTEST,
        test_cases=[],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={},
    )

    with patch('integrations.tea.orchestrator.invoke_tea_test_design',
               new=AsyncMock(return_value=mock_plan)):
        with patch('integrations.tea.orchestrator.generate_atdd_tests',
                   new=AsyncMock(return_value=[])):
            result = await run_tea_for_tier("standard", story_path, tmp_path)

    assert result.depth == "standard"
    assert result.test_plan is not None
    assert result.success is True
    # Standard doesn't run trace/nfr
    assert result.traceability is None
    assert result.nfr_assessment is None


@pytest.mark.asyncio
async def test_run_tea_complex_runs_full_suite(tmp_path):
    """Test TEA runs full suite for complex tier."""
    from integrations.tea import run_tea_for_tier, TestPlan, TestFramework
    from integrations.tea.trace import TraceabilityMatrix
    from integrations.tea.nfr_assess import NFRAssessment

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("""# Story

## Acceptance Criteria

1. **Given** X **When** Y **Then** Z
""")

    (tmp_path / "pytest.ini").write_text("[pytest]")

    mock_plan = TestPlan(
        story_id="1-1-test",
        framework=TestFramework.PYTEST,
        test_cases=[],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={},
    )

    mock_trace = TraceabilityMatrix(
        requirement_coverage={},
        uncovered_requirements=[],
        tests_without_requirement=[],
        coverage_percentage=100.0,
        quality_gate_passed=True,
    )

    mock_nfr = NFRAssessment(passed=True)

    with patch('integrations.tea.orchestrator.invoke_tea_test_design',
               new=AsyncMock(return_value=mock_plan)):
        with patch('integrations.tea.orchestrator.generate_atdd_tests',
                   new=AsyncMock(return_value=[])):
            with patch('integrations.tea.orchestrator.generate_traceability_matrix',
                       new=AsyncMock(return_value=mock_trace)):
                with patch('integrations.tea.orchestrator.run_nfr_assessment',
                           new=AsyncMock(return_value=mock_nfr)):
                    result = await run_tea_for_tier("complex", story_path, tmp_path)

    assert result.depth == "full"
    assert result.test_plan is not None
    assert result.traceability is not None
    assert result.nfr_assessment is not None
    assert result.success is True


def test_format_tea_summary():
    """Test TEA summary formatting."""
    from integrations.tea import format_tea_summary, TEAResult

    result = TEAResult(
        depth="standard",
        tier="standard",
        test_files=["test_example.py"],
        success=True,
    )

    summary = format_tea_summary(result)

    assert "TEA Execution Summary" in summary
    assert "standard" in summary
    assert "Success" in summary
    assert "test_example.py" in summary


def test_format_tea_summary_with_error():
    """Test TEA summary formatting with error."""
    from integrations.tea import format_tea_summary, TEAResult

    result = TEAResult(
        depth="standard",
        tier="standard",
        success=False,
        error="Test generation failed",
    )

    summary = format_tea_summary(result)

    assert "Failed" in summary
    assert "Test generation failed" in summary
