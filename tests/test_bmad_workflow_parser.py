"""Unit tests for BMAD workflow status parser.

Tests workflow file discovery, parsing, and integration functions.

Story 2.3: BMAD Workflow Status Parser (AC: all)
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from adapters.bmad.parser import (
    WorkflowStatus,
    ParseError,
    find_workflow_status_file,
    parse_workflow_status,
    default_workflow_status,
    get_workflow_context_for_story,
    get_active_workflow_info,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def active_workflow() -> WorkflowStatus:
    """Return a sample active workflow status."""
    return WorkflowStatus(
        workflow_name="create-story",
        status="active",
        current_step=3,
        steps_completed=[1, 2],
        started_at=datetime(2025, 12, 16, 10, 30, 0, tzinfo=timezone.utc),
        context={"story_key": "1-2-create-unified-data-model", "epic_num": 1},
        blockers=[],
        next_action="Complete step 3: Architecture analysis",
    )


@pytest.fixture
def paused_workflow() -> WorkflowStatus:
    """Return a sample paused workflow with blockers."""
    return WorkflowStatus(
        workflow_name="dev-story",
        status="paused",
        current_step=2,
        steps_completed=[1],
        context={"story_key": "1-3-framework-selector"},
        blockers=["Waiting for code review", "Need design clarification"],
        next_action="Resume after review",
    )


# =============================================================================
# Workflow File Discovery Tests
# =============================================================================


class TestFindWorkflowStatusFile:
    """Tests for find_workflow_status_file function."""

    def test_finds_existing_file(self, tmp_path: Path) -> None:
        """Test finding workflow status file when it exists."""
        workflow_file = tmp_path / "_bmad-output" / "bmm-workflow-status.yaml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text("workflow: test")

        result = find_workflow_status_file(tmp_path)
        assert result == workflow_file

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """Test graceful handling when file doesn't exist."""
        result = find_workflow_status_file(tmp_path)
        assert result is None

    def test_returns_none_when_directory_empty(self, tmp_path: Path) -> None:
        """Test returns None when _bmad-output exists but no workflow file."""
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        result = find_workflow_status_file(tmp_path)
        assert result is None


# =============================================================================
# Workflow Parsing Tests
# =============================================================================


class TestParseWorkflowStatus:
    """Tests for parse_workflow_status function."""

    def test_extracts_workflow_name(self, tmp_path: Path) -> None:
        """Test workflow name extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: create-story\nstatus: active\ncurrent_step: 1")

        status = parse_workflow_status(workflow_file)
        assert status.workflow_name == "create-story"

    def test_extracts_status(self, tmp_path: Path) -> None:
        """Test status extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: test\nstatus: paused\ncurrent_step: 2")

        status = parse_workflow_status(workflow_file)
        assert status.status == "paused"

    def test_extracts_current_step(self, tmp_path: Path) -> None:
        """Test current step extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: test\nstatus: active\ncurrent_step: 5")

        status = parse_workflow_status(workflow_file)
        assert status.current_step == 5

    def test_extracts_steps_completed(self, tmp_path: Path) -> None:
        """Test steps_completed list extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: test\nstatus: active\ncurrent_step: 3\nsteps_completed: [1, 2]")

        status = parse_workflow_status(workflow_file)
        assert status.steps_completed == [1, 2]

    def test_extracts_context(self, tmp_path: Path) -> None:
        """Test context dict extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("""
workflow: create-story
status: active
current_step: 1
context:
  story_key: "1-2-test"
  epic_num: 1
""")

        status = parse_workflow_status(workflow_file)
        assert status.context["story_key"] == "1-2-test"
        assert status.context["epic_num"] == 1

    def test_extracts_blockers(self, tmp_path: Path) -> None:
        """Test blockers list extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("""
workflow: test
status: paused
current_step: 2
blockers:
  - "Waiting for review"
  - "Need clarification"
""")

        status = parse_workflow_status(workflow_file)
        assert len(status.blockers) == 2
        assert "Waiting for review" in status.blockers

    def test_extracts_next_action(self, tmp_path: Path) -> None:
        """Test next_action extraction."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text('workflow: test\nstatus: active\ncurrent_step: 3\nnext_action: "Complete architecture"')

        status = parse_workflow_status(workflow_file)
        assert status.next_action == "Complete architecture"

    def test_parses_started_at_timestamp(self, tmp_path: Path) -> None:
        """Test ISO timestamp parsing."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: test\nstatus: active\ncurrent_step: 1\nstarted_at: 2025-12-16T10:30:00Z")

        status = parse_workflow_status(workflow_file)
        assert status.started_at is not None
        assert status.started_at.year == 2025
        assert status.started_at.month == 12
        assert status.started_at.day == 16

    def test_handles_missing_optional_fields(self, tmp_path: Path) -> None:
        """Test defaults for missing optional fields."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("workflow: minimal")

        status = parse_workflow_status(workflow_file)
        assert status.status == "inactive"
        assert status.current_step == 0
        assert status.steps_completed == []
        assert status.context == {}
        assert status.blockers == []
        assert status.next_action == ""

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty YAML file."""
        workflow_file = tmp_path / "workflow.yaml"
        workflow_file.write_text("")

        status = parse_workflow_status(workflow_file)
        assert status.workflow_name == "unknown"
        assert status.status == "inactive"

    def test_raises_on_malformed_yaml(self, tmp_path: Path) -> None:
        """Test ParseError on malformed YAML."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{ invalid yaml [")

        with pytest.raises(ParseError, match="Invalid YAML"):
            parse_workflow_status(bad_file)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Test ParseError on missing file."""
        missing = tmp_path / "nonexistent.yaml"

        with pytest.raises(ParseError, match="not found"):
            parse_workflow_status(missing)


class TestDefaultWorkflowStatus:
    """Tests for default_workflow_status function."""

    def test_returns_inactive_status(self) -> None:
        """Test default status is inactive."""
        status = default_workflow_status()
        assert status.workflow_name == "none"
        assert status.status == "inactive"
        assert status.current_step == 0
        assert status.steps_completed == []


# =============================================================================
# Workflow Integration Tests
# =============================================================================


class TestGetWorkflowContextForStory:
    """Tests for get_workflow_context_for_story function."""

    def test_returns_context_for_matching_story(self, active_workflow: WorkflowStatus) -> None:
        """Test context returned when story key matches."""
        context = get_workflow_context_for_story(active_workflow, "1-2-create-unified-data-model")

        assert context is not None
        assert context["workflow"] == "create-story"
        assert context["status"] == "active"
        assert context["current_step"] == 3
        assert context["next_action"] == "Complete step 3: Architecture analysis"

    def test_returns_none_for_non_matching_story(self, active_workflow: WorkflowStatus) -> None:
        """Test None returned for non-matching story."""
        context = get_workflow_context_for_story(active_workflow, "1-3-framework-selector")
        assert context is None

    def test_returns_none_when_workflow_is_none(self) -> None:
        """Test None returned when no workflow status."""
        context = get_workflow_context_for_story(None, "1-2-test")
        assert context is None

    def test_includes_blockers_in_context(self, paused_workflow: WorkflowStatus) -> None:
        """Test blockers are included in context."""
        context = get_workflow_context_for_story(paused_workflow, "1-3-framework-selector")

        assert context is not None
        assert len(context["blockers"]) == 2

    def test_includes_started_at_in_context(self, active_workflow: WorkflowStatus) -> None:
        """Test started_at is included as ISO string."""
        context = get_workflow_context_for_story(active_workflow, "1-2-create-unified-data-model")

        assert context is not None
        assert context["started_at"] is not None
        assert "2025-12-16" in context["started_at"]


class TestGetActiveWorkflowInfo:
    """Tests for get_active_workflow_info function."""

    def test_returns_info_for_active_workflow(self, active_workflow: WorkflowStatus) -> None:
        """Test info returned for active workflow."""
        info = get_active_workflow_info(active_workflow)

        assert info is not None
        assert info["workflow_name"] == "create-story"
        assert info["status"] == "active"
        assert info["current_step"] == 3
        assert info["total_completed"] == 2

    def test_returns_info_for_paused_workflow(self, paused_workflow: WorkflowStatus) -> None:
        """Test info returned for paused workflow."""
        info = get_active_workflow_info(paused_workflow)

        assert info is not None
        assert info["status"] == "paused"
        assert info["has_blockers"] is True
        assert len(info["blockers"]) == 2

    def test_returns_none_for_inactive_workflow(self) -> None:
        """Test None returned for inactive workflow."""
        inactive = WorkflowStatus(
            workflow_name="test",
            status="inactive",
            current_step=0,
            steps_completed=[],
        )
        info = get_active_workflow_info(inactive)
        assert info is None

    def test_returns_none_for_complete_workflow(self) -> None:
        """Test None returned for completed workflow."""
        complete = WorkflowStatus(
            workflow_name="test",
            status="complete",
            current_step=5,
            steps_completed=[1, 2, 3, 4, 5],
        )
        info = get_active_workflow_info(complete)
        assert info is None

    def test_returns_none_when_workflow_is_none(self) -> None:
        """Test None returned when no workflow."""
        info = get_active_workflow_info(None)
        assert info is None
