"""Unit tests for BMAD Adapter.

Tests the BMADAdapter class that implements the FrameworkAdapter interface.

Story 2.5: BMAD Adapter Implementation (AC: all)
"""

import pytest
from pathlib import Path

from adapters import get_adapter, register_adapter, FrameworkAdapter
from adapters.bmad import BMADAdapter
from adapters.glossary import BMAD_GLOSSARY
from models import UnifiedStatus


# =============================================================================
# Adapter Registration Tests
# =============================================================================


class TestAdapterRegistration:
    """Tests for adapter factory registration."""

    def test_bmad_adapter_is_registered(self) -> None:
        """Test that BMADAdapter is registered in the factory."""
        adapter = get_adapter("bmad")
        assert isinstance(adapter, BMADAdapter)

    def test_get_adapter_returns_new_instance(self) -> None:
        """Test that get_adapter returns a new instance each time."""
        adapter1 = get_adapter("bmad")
        adapter2 = get_adapter("bmad")
        assert adapter1 is not adapter2

    def test_unknown_adapter_raises_error(self) -> None:
        """Test that unknown framework name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown framework"):
            get_adapter("unknown-framework")

    def test_error_message_includes_available_frameworks(self) -> None:
        """Test that error message includes available frameworks."""
        with pytest.raises(ValueError, match="bmad"):
            get_adapter("unknown")


# =============================================================================
# Adapter Interface Tests
# =============================================================================


class TestAdapterInterface:
    """Tests for FrameworkAdapter interface implementation."""

    def test_implements_framework_adapter(self) -> None:
        """Test that BMADAdapter implements FrameworkAdapter."""
        adapter = BMADAdapter()
        assert isinstance(adapter, FrameworkAdapter)

    def test_name_property(self) -> None:
        """Test name property returns 'bmad'."""
        adapter = BMADAdapter()
        assert adapter.name == "bmad"

    def test_glossary_property(self) -> None:
        """Test glossary property returns BMAD glossary."""
        adapter = BMADAdapter()
        assert adapter.glossary == BMAD_GLOSSARY

    def test_glossary_has_expected_terms(self) -> None:
        """Test glossary has expected BMAD terminology."""
        adapter = BMADAdapter()
        glossary = adapter.glossary

        assert glossary["workUnit"] == "Epic"
        assert glossary["task"] == "Story"
        assert glossary["checkpoint"] == "Task"


# =============================================================================
# Parse Work Units Tests
# =============================================================================


class TestParseWorkUnits:
    """Tests for parse_work_units method."""

    def test_returns_empty_when_no_sprint_status(self, tmp_path: Path) -> None:
        """Test returns empty list when no sprint status file exists."""
        adapter = BMADAdapter()
        result = adapter.parse_work_units(tmp_path)
        assert result == []

    def test_parses_epics_from_sprint_status(
        self, bmad_project_fixture: Path
    ) -> None:
        """Test parsing epics from sprint status file."""
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(bmad_project_fixture)

        assert len(work_units) == 2
        assert work_units[0].id == "1"
        assert work_units[1].id == "2"

    def test_epic_status_is_mapped(self, bmad_project_fixture: Path) -> None:
        """Test that epic statuses are mapped to UnifiedStatus."""
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(bmad_project_fixture)

        # epic-1 has "in-progress" status
        assert work_units[0].status == UnifiedStatus.IN_PROGRESS
        # epic-2 has "pending" status
        assert work_units[1].status == UnifiedStatus.PENDING

    def test_stories_are_grouped_by_epic(self, bmad_project_fixture: Path) -> None:
        """Test that stories are grouped under their respective epics."""
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(bmad_project_fixture)

        # Epic 1 should have 2 stories (1-1 and 1-2)
        assert len(work_units[0].tasks) == 2

        # Epic 2 should have no stories (no story files for epic 2)
        assert len(work_units[1].tasks) == 0

    def test_work_units_sorted_by_id(self, bmad_project_fixture: Path) -> None:
        """Test that work units are sorted by epic number."""
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(bmad_project_fixture)

        ids = [wu.id for wu in work_units]
        assert ids == sorted(ids, key=int)

    def test_metadata_includes_epic_key(self, bmad_project_fixture: Path) -> None:
        """Test that metadata includes original epic key."""
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(bmad_project_fixture)

        assert "epic_key" in work_units[0].metadata
        assert work_units[0].metadata["epic_key"] == "epic-1"

    def test_caches_work_units(self, bmad_project_fixture: Path) -> None:
        """Test that work units are cached after first parse."""
        adapter = BMADAdapter()

        # First call
        work_units1 = adapter.parse_work_units(bmad_project_fixture)

        # Second call should use cache (same object)
        work_units2 = adapter.parse_work_units(bmad_project_fixture)

        # Results should be equal
        assert len(work_units1) == len(work_units2)


# =============================================================================
# Parse Tasks Tests
# =============================================================================


class TestParseTasks:
    """Tests for parse_tasks method."""

    def test_returns_tasks_for_work_unit(self, bmad_project_fixture: Path) -> None:
        """Test returning tasks for a specific work unit."""
        adapter = BMADAdapter()
        adapter.parse_work_units(bmad_project_fixture)

        tasks = adapter.parse_tasks("1")
        assert len(tasks) == 2

    def test_raises_error_for_unknown_work_unit(
        self, bmad_project_fixture: Path
    ) -> None:
        """Test that ValueError is raised for unknown work unit."""
        adapter = BMADAdapter()
        adapter.parse_work_units(bmad_project_fixture)

        with pytest.raises(ValueError, match="Work unit not found"):
            adapter.parse_tasks("999")

    def test_task_has_correct_structure(self, bmad_project_fixture: Path) -> None:
        """Test that tasks have correct structure."""
        adapter = BMADAdapter()
        adapter.parse_work_units(bmad_project_fixture)

        tasks = adapter.parse_tasks("1")
        task = tasks[0]

        assert task.id is not None
        assert task.title is not None
        assert task.status is not None


# =============================================================================
# Get Status Tests
# =============================================================================


class TestGetStatus:
    """Tests for get_status method."""

    def test_returns_project_status(self, bmad_project_fixture: Path) -> None:
        """Test returning ProjectStatus object."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        assert status.framework == "bmad"

    def test_includes_work_units(self, bmad_project_fixture: Path) -> None:
        """Test that status includes work units."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        assert len(status.work_units) == 2

    def test_calculates_total_tasks(self, bmad_project_fixture: Path) -> None:
        """Test that total_tasks is calculated correctly."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        # 2 stories total (1-1 and 1-2)
        assert status.total_tasks == 2

    def test_calculates_completed_tasks(self, bmad_project_fixture: Path) -> None:
        """Test that completed_tasks is calculated correctly."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        # Story 1-1 is done (status: Done)
        assert status.completed_tasks >= 1

    def test_calculates_progress_percentage(self, bmad_project_fixture: Path) -> None:
        """Test that progress percentage is calculated correctly."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        # Progress should be between 0 and 100
        assert 0 <= status.progress_percentage <= 100

    def test_detects_active_task_from_workflow(
        self, bmad_project_fixture: Path
    ) -> None:
        """Test that active task is detected from workflow status."""
        adapter = BMADAdapter()
        status = adapter.get_status(bmad_project_fixture)

        # Workflow status has story_key: "1-2"
        if status.active_task:
            assert "1-2" in status.active_task.id or "1-2" in str(status.active_task.metadata.get("key", ""))

    def test_handles_missing_workflow_gracefully(self, tmp_path: Path) -> None:
        """Test graceful handling when workflow status is missing."""
        # Create minimal BMAD project without workflow status
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        sprint_status = """project: Test
project_key: test
tracking_system: file-system
story_location: _bmad-output/stories

development_status:
  epic-1: pending
"""
        (bmad_dir / "bmm-sprint-status.yaml").write_text(sprint_status)

        adapter = BMADAdapter()
        status = adapter.get_status(tmp_path)

        # Should not raise error
        assert status.framework == "bmad"
        assert status.active_task is None


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_invalid_epic_key_format(self, tmp_path: Path) -> None:
        """Test graceful handling of invalid epic key format."""
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        # Invalid epic key format in development_status
        sprint_status = """project: Test
project_key: test
tracking_system: file-system
story_location: _bmad-output/stories

development_status:
  invalid-key: pending
  epic-1: done
"""
        (bmad_dir / "bmm-sprint-status.yaml").write_text(sprint_status)

        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(tmp_path)

        # Should only include valid epic (epic-1)
        assert len(work_units) == 1
        assert work_units[0].id == "1"

    def test_handles_malformed_story_files(self, tmp_path: Path) -> None:
        """Test graceful handling of malformed story files."""
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        sprint_status = """project: Test
project_key: test
tracking_system: file-system
story_location: _bmad-output/stories

development_status:
  epic-1: in-progress
  1-1-malformed: pending
"""
        (bmad_dir / "bmm-sprint-status.yaml").write_text(sprint_status)

        # Create malformed story file (no valid header format)
        stories_dir = bmad_dir / "stories"
        stories_dir.mkdir()
        (stories_dir / "1-1-malformed.md").write_text("Not a valid story file")

        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(tmp_path)

        # Should still return work unit, just with no tasks (story parsing failed)
        assert len(work_units) == 1

    def test_handles_unknown_status_gracefully(self, tmp_path: Path) -> None:
        """Test graceful handling of unknown BMAD status values."""
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        sprint_status = """project: Test
project_key: test
tracking_system: file-system
story_location: _bmad-output/stories

development_status:
  epic-1: unknown-status-value
"""
        (bmad_dir / "bmm-sprint-status.yaml").write_text(sprint_status)

        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(tmp_path)

        # Should default to PENDING for unknown status
        assert len(work_units) == 1
        assert work_units[0].status == UnifiedStatus.PENDING

    def test_handles_empty_project(self, tmp_path: Path) -> None:
        """Test handling of completely empty project."""
        adapter = BMADAdapter()

        work_units = adapter.parse_work_units(tmp_path)
        assert work_units == []

        status = adapter.get_status(tmp_path)
        assert status.total_tasks == 0
        assert status.progress_percentage == 0.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for BMAD adapter with full workflow."""

    def test_full_workflow(self, bmad_project_fixture: Path) -> None:
        """Test complete workflow from parsing to status."""
        # Get adapter through factory
        adapter = get_adapter("bmad")

        # Parse work units
        work_units = adapter.parse_work_units(bmad_project_fixture)
        assert len(work_units) > 0

        # Get tasks for first work unit
        tasks = adapter.parse_tasks(work_units[0].id)
        assert isinstance(tasks, list)

        # Get overall status
        status = adapter.get_status(bmad_project_fixture)
        assert status.framework == "bmad"
        assert status.work_units == work_units

    def test_adapter_provides_correct_glossary(self) -> None:
        """Test that adapter provides correct framework-specific glossary."""
        adapter = get_adapter("bmad")
        glossary = adapter.glossary

        # BMAD terminology (TypedDict with camelCase keys)
        assert glossary["workUnit"] == "Epic"
        assert glossary["task"] == "Story"
        assert glossary["checkpoint"] == "Task"
