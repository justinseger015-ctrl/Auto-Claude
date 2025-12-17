"""Tests for the unified data models - Story 1.2: Create Unified Data Model.

Tests validate:
1. UnifiedStatus enum values and string representations
2. Checkpoint, Task, WorkUnit, ProjectStatus dataclass creation
3. Status mapping functions for BMAD and Native
4. Import paths work correctly
"""

import pytest
from pathlib import Path

from models import (
    UnifiedStatus,
    Checkpoint,
    Task,
    WorkUnit,
    ProjectStatus,
    BMAD_STATUS_MAP,
    NATIVE_STATUS_MAP,
    map_bmad_status,
    map_native_status,
)


class TestUnifiedStatus:
    """Tests for UnifiedStatus enum."""

    def test_unified_status_values(self):
        """All 6 status values exist with correct string representations."""
        assert UnifiedStatus.PENDING.value == "pending"
        assert UnifiedStatus.IN_PROGRESS.value == "in_progress"
        assert UnifiedStatus.REVIEW.value == "review"
        assert UnifiedStatus.BLOCKED.value == "blocked"
        assert UnifiedStatus.COMPLETED.value == "completed"
        assert UnifiedStatus.FAILED.value == "failed"

    def test_unified_status_count(self):
        """UnifiedStatus has exactly 6 members."""
        assert len(UnifiedStatus) == 6


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    def test_checkpoint_creation(self):
        """Checkpoint instantiates with required fields."""
        checkpoint = Checkpoint(
            id="cp-1",
            description="Verify API endpoint returns 200",
        )
        assert checkpoint.id == "cp-1"
        assert checkpoint.description == "Verify API endpoint returns 200"
        assert checkpoint.completed is False  # default

    def test_checkpoint_completed_flag(self):
        """Checkpoint completed flag can be set."""
        checkpoint = Checkpoint(
            id="cp-2",
            description="Test completed",
            completed=True,
        )
        assert checkpoint.completed is True


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Task instantiates with all required fields."""
        task = Task(
            id="1-2",
            title="Create Unified Data Model",
            description="Implement dataclasses for cross-framework compatibility",
            status=UnifiedStatus.IN_PROGRESS,
        )
        assert task.id == "1-2"
        assert task.title == "Create Unified Data Model"
        assert task.status == UnifiedStatus.IN_PROGRESS
        assert task.checkpoints == []  # default factory
        assert task.files == []  # default factory
        assert task.acceptance_criteria == []  # default factory
        assert task.metadata == {}  # default factory

    def test_task_with_checkpoints(self):
        """Task can contain checkpoints."""
        checkpoint = Checkpoint(id="cp-1", description="Test checkpoint")
        task = Task(
            id="1-1",
            title="Test Task",
            checkpoints=[checkpoint],
        )
        assert len(task.checkpoints) == 1
        assert task.checkpoints[0].id == "cp-1"

    def test_task_default_status(self):
        """Task defaults to PENDING status."""
        task = Task(id="test", title="Test")
        assert task.status == UnifiedStatus.PENDING


class TestWorkUnit:
    """Tests for WorkUnit dataclass."""

    def test_work_unit_creation(self):
        """WorkUnit instantiates with all required fields."""
        work_unit = WorkUnit(
            id="1",
            title="Framework Selection & Setup",
            description="Set up adapter infrastructure",
            status=UnifiedStatus.IN_PROGRESS,
        )
        assert work_unit.id == "1"
        assert work_unit.title == "Framework Selection & Setup"
        assert work_unit.status == UnifiedStatus.IN_PROGRESS
        assert work_unit.tasks == []  # default factory
        assert work_unit.metadata == {}  # default factory

    def test_work_unit_with_tasks(self):
        """WorkUnit can contain nested tasks."""
        task1 = Task(id="1-1", title="Task 1")
        task2 = Task(id="1-2", title="Task 2")
        work_unit = WorkUnit(
            id="1",
            title="Epic 1",
            tasks=[task1, task2],
        )
        assert len(work_unit.tasks) == 2
        assert work_unit.tasks[0].id == "1-1"
        assert work_unit.tasks[1].id == "1-2"

    def test_work_unit_default_status(self):
        """WorkUnit defaults to PENDING status."""
        work_unit = WorkUnit(id="test", title="Test")
        assert work_unit.status == UnifiedStatus.PENDING


class TestProjectStatus:
    """Tests for ProjectStatus dataclass."""

    def test_project_status_creation(self):
        """ProjectStatus instantiates with framework name."""
        status = ProjectStatus(framework="bmad")
        assert status.framework == "bmad"
        assert status.work_units == []
        assert status.active_task is None
        assert status.total_tasks == 0
        assert status.completed_tasks == 0
        assert status.progress_percentage == 0.0

    def test_project_status_with_work_units(self):
        """ProjectStatus can track work units and progress."""
        task = Task(id="1-1", title="Test", status=UnifiedStatus.COMPLETED)
        work_unit = WorkUnit(id="1", title="Epic 1", tasks=[task])
        status = ProjectStatus(
            framework="bmad",
            work_units=[work_unit],
            total_tasks=5,
            completed_tasks=3,
            progress_percentage=60.0,
        )
        assert len(status.work_units) == 1
        assert status.total_tasks == 5
        assert status.completed_tasks == 3
        assert status.progress_percentage == 60.0


class TestBMADStatusMapping:
    """Tests for BMAD status mapping."""

    def test_bmad_status_map_keys(self):
        """BMAD_STATUS_MAP has all expected keys."""
        expected_keys = {"backlog", "ready-for-dev", "in-progress", "review", "blocked", "done"}
        assert expected_keys <= set(BMAD_STATUS_MAP.keys())

    def test_bmad_backlog_maps_to_pending(self):
        """BMAD 'backlog' maps to PENDING."""
        assert map_bmad_status("backlog") == UnifiedStatus.PENDING

    def test_bmad_ready_for_dev_maps_to_pending(self):
        """BMAD 'ready-for-dev' maps to PENDING."""
        assert map_bmad_status("ready-for-dev") == UnifiedStatus.PENDING

    def test_bmad_in_progress_maps(self):
        """BMAD 'in-progress' maps to IN_PROGRESS."""
        assert map_bmad_status("in-progress") == UnifiedStatus.IN_PROGRESS

    def test_bmad_review_maps(self):
        """BMAD 'review' maps to REVIEW."""
        assert map_bmad_status("review") == UnifiedStatus.REVIEW

    def test_bmad_blocked_maps(self):
        """BMAD 'blocked' maps to BLOCKED."""
        assert map_bmad_status("blocked") == UnifiedStatus.BLOCKED

    def test_bmad_done_maps_to_completed(self):
        """BMAD 'done' maps to COMPLETED."""
        assert map_bmad_status("done") == UnifiedStatus.COMPLETED

    def test_bmad_unknown_status_raises(self):
        """Unknown BMAD status raises ValueError."""
        with pytest.raises(ValueError, match="Unknown BMAD status"):
            map_bmad_status("nonexistent")


class TestNativeStatusMapping:
    """Tests for Native status mapping."""

    def test_native_status_map_keys(self):
        """NATIVE_STATUS_MAP has all expected keys."""
        expected_keys = {"pending", "in_progress", "ai_review", "human_review", "done", "failed"}
        assert expected_keys <= set(NATIVE_STATUS_MAP.keys())

    def test_native_pending_maps(self):
        """Native 'pending' maps to PENDING."""
        assert map_native_status("pending") == UnifiedStatus.PENDING

    def test_native_in_progress_maps(self):
        """Native 'in_progress' maps to IN_PROGRESS."""
        assert map_native_status("in_progress") == UnifiedStatus.IN_PROGRESS

    def test_native_ai_review_maps(self):
        """Native 'ai_review' maps to REVIEW."""
        assert map_native_status("ai_review") == UnifiedStatus.REVIEW

    def test_native_human_review_maps(self):
        """Native 'human_review' maps to REVIEW."""
        assert map_native_status("human_review") == UnifiedStatus.REVIEW

    def test_native_done_maps(self):
        """Native 'done' maps to COMPLETED."""
        assert map_native_status("done") == UnifiedStatus.COMPLETED

    def test_native_failed_maps(self):
        """Native 'failed' maps to FAILED."""
        assert map_native_status("failed") == UnifiedStatus.FAILED

    def test_native_unknown_status_raises(self):
        """Unknown Native status raises ValueError."""
        with pytest.raises(ValueError, match="Unknown Native status"):
            map_native_status("nonexistent")


class TestImports:
    """Tests for import structure."""

    def test_all_exports_available(self):
        """All expected exports are available from models package."""
        from models import (
            UnifiedStatus,
            Checkpoint,
            Task,
            WorkUnit,
            ProjectStatus,
            BMAD_STATUS_MAP,
            NATIVE_STATUS_MAP,
            map_bmad_status,
            map_native_status,
        )
        # If we get here without ImportError, test passes
        assert True


class TestStatusMappingEdgeCases:
    """Tests for status mapping edge cases - added in code review."""

    def test_bmad_optional_status_maps_to_pending(self):
        """BMAD 'optional' (retrospective status) maps to PENDING."""
        assert map_bmad_status("optional") == UnifiedStatus.PENDING

    def test_bmad_empty_string_raises(self):
        """Empty string raises ValueError for BMAD status."""
        with pytest.raises(ValueError, match="Unknown BMAD status"):
            map_bmad_status("")

    def test_native_empty_string_raises(self):
        """Empty string raises ValueError for Native status."""
        with pytest.raises(ValueError, match="Unknown Native status"):
            map_native_status("")

    def test_bmad_status_case_sensitive(self):
        """BMAD status mapping is case-sensitive."""
        # Uppercase should fail
        with pytest.raises(ValueError, match="Unknown BMAD status"):
            map_bmad_status("Backlog")
        with pytest.raises(ValueError, match="Unknown BMAD status"):
            map_bmad_status("DONE")

    def test_native_status_case_sensitive(self):
        """Native status mapping is case-sensitive."""
        # Uppercase should fail
        with pytest.raises(ValueError, match="Unknown Native status"):
            map_native_status("Pending")
        with pytest.raises(ValueError, match="Unknown Native status"):
            map_native_status("IN_PROGRESS")
