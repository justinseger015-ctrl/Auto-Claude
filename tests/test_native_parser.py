"""Unit tests for Native artifact parser.

Tests spec discovery, parsing, and conversion to unified models.

Story 2.4: Native Artifact Parser (AC: all)
"""

import json
import pytest
from pathlib import Path

from adapters.native.parser import (
    NativeSubtask,
    NativePhase,
    NativeSpec,
    ParseError,
    find_specs,
    parse_spec,
    spec_to_work_unit,
    subtask_to_task,
)
from models import UnifiedStatus


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fixtures_path() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_spec(fixtures_path: Path) -> NativeSpec:
    """Return parsed sample spec fixture."""
    return parse_spec(fixtures_path / "native" / "001-sample")


# =============================================================================
# Spec Discovery Tests
# =============================================================================


class TestFindSpecs:
    """Tests for find_specs function."""

    def test_returns_empty_when_no_directory(self, tmp_path: Path) -> None:
        """Test graceful handling when .auto-claude/specs doesn't exist."""
        result = find_specs(tmp_path)
        assert result == []

    def test_returns_empty_when_no_matching_dirs(self, tmp_path: Path) -> None:
        """Test empty result when no matching spec directories."""
        specs_dir = tmp_path / ".auto-claude" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "readme.md").touch()
        (specs_dir / "invalid-dir").mkdir()

        result = find_specs(tmp_path)
        assert result == []

    def test_finds_matching_directories(self, tmp_path: Path) -> None:
        """Test finding spec directories matching pattern."""
        specs_dir = tmp_path / ".auto-claude" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "001-first").mkdir()

        result = find_specs(tmp_path)
        assert len(result) == 1
        assert result[0].name == "001-first"

    def test_returns_sorted_by_id(self, tmp_path: Path) -> None:
        """Test spec directories are sorted by ID."""
        specs_dir = tmp_path / ".auto-claude" / "specs"
        specs_dir.mkdir(parents=True)

        # Create in random order
        (specs_dir / "003-third").mkdir()
        (specs_dir / "001-first").mkdir()
        (specs_dir / "002-second").mkdir()

        result = find_specs(tmp_path)

        assert len(result) == 3
        assert result[0].name == "001-first"
        assert result[1].name == "002-second"
        assert result[2].name == "003-third"

    def test_ignores_non_matching_directories(self, tmp_path: Path) -> None:
        """Test directories not matching pattern are ignored."""
        specs_dir = tmp_path / ".auto-claude" / "specs"
        specs_dir.mkdir(parents=True)

        (specs_dir / "001-valid").mkdir()
        (specs_dir / "01-short-id").mkdir()
        (specs_dir / "0001-too-long").mkdir()
        (specs_dir / "invalid").mkdir()

        result = find_specs(tmp_path)
        assert len(result) == 1
        assert result[0].name == "001-valid"


# =============================================================================
# Spec Parsing Tests
# =============================================================================


class TestParseSpec:
    """Tests for parse_spec function."""

    def test_extracts_id_and_name(self, sample_spec: NativeSpec) -> None:
        """Test ID and name extraction from directory name."""
        assert sample_spec.id == "001"
        assert sample_spec.name == "sample"

    def test_extracts_description(self, sample_spec: NativeSpec) -> None:
        """Test description extraction from spec.md."""
        assert "sample feature" in sample_spec.description.lower()

    def test_extracts_requirements(self, sample_spec: NativeSpec) -> None:
        """Test requirements extraction from spec.md."""
        assert len(sample_spec.requirements) == 3
        assert "First requirement" in sample_spec.requirements[0]

    def test_extracts_acceptance_criteria(self, sample_spec: NativeSpec) -> None:
        """Test AC extraction from spec.md."""
        assert len(sample_spec.acceptance_criteria) == 3
        assert "Feature works correctly" in sample_spec.acceptance_criteria[0]

    def test_extracts_status(self, sample_spec: NativeSpec) -> None:
        """Test status extraction from implementation_plan.json."""
        assert sample_spec.status == "in_progress"

    def test_extracts_phases(self, sample_spec: NativeSpec) -> None:
        """Test phases extraction from implementation_plan.json."""
        assert len(sample_spec.phases) == 3
        assert sample_spec.phases[0].name == "Setup"
        assert sample_spec.phases[1].name == "Implementation"
        assert sample_spec.phases[2].name == "Testing"

    def test_extracts_subtasks(self, sample_spec: NativeSpec) -> None:
        """Test subtasks extraction within phases."""
        setup_phase = sample_spec.phases[0]
        assert len(setup_phase.subtasks) == 2
        assert setup_phase.subtasks[0].id == "1.1"
        assert "directory structure" in setup_phase.subtasks[0].description.lower()

    def test_extracts_subtask_files(self, sample_spec: NativeSpec) -> None:
        """Test file paths extraction in subtasks."""
        setup_phase = sample_spec.phases[0]
        assert setup_phase.subtasks[0].files == ["src/feature/index.ts"]

    def test_stores_spec_dir(self, sample_spec: NativeSpec) -> None:
        """Test spec directory is stored."""
        assert sample_spec.spec_dir is not None
        assert "001-sample" in str(sample_spec.spec_dir)

    def test_handles_missing_spec_md(self, tmp_path: Path) -> None:
        """Test graceful handling when spec.md is missing."""
        spec_dir = tmp_path / ".auto-claude" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        plan = {"status": "pending", "phases": []}
        (spec_dir / "implementation_plan.json").write_text(json.dumps(plan))

        spec = parse_spec(spec_dir)
        assert spec.id == "001"
        assert spec.description == ""
        assert spec.requirements == []
        assert spec.acceptance_criteria == []

    def test_handles_missing_implementation_plan(self, tmp_path: Path) -> None:
        """Test graceful handling when implementation_plan.json is missing."""
        spec_dir = tmp_path / ".auto-claude" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("# Spec: Test\n\n## Overview\nTest spec")

        spec = parse_spec(spec_dir)
        assert spec.id == "001"
        assert spec.status == "pending"
        assert spec.phases == []

    def test_raises_on_invalid_directory_name(self, tmp_path: Path) -> None:
        """Test ValueError on invalid directory name."""
        invalid_dir = tmp_path / "invalid-name"
        invalid_dir.mkdir()

        with pytest.raises(ValueError, match="Invalid spec directory name"):
            parse_spec(invalid_dir)

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        """Test ParseError on malformed JSON."""
        spec_dir = tmp_path / ".auto-claude" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "implementation_plan.json").write_text("{ invalid json")

        with pytest.raises(ParseError, match="Invalid JSON"):
            parse_spec(spec_dir)


# =============================================================================
# Spec to WorkUnit Conversion Tests
# =============================================================================


class TestSpecToWorkUnit:
    """Tests for spec_to_work_unit function."""

    def test_maps_id(self, sample_spec: NativeSpec) -> None:
        """Test ID mapping."""
        work_unit = spec_to_work_unit(sample_spec)
        assert work_unit.id == "001"

    def test_maps_title(self, sample_spec: NativeSpec) -> None:
        """Test title mapping with formatting."""
        work_unit = spec_to_work_unit(sample_spec)
        assert work_unit.title == "Sample"

    def test_maps_description(self, sample_spec: NativeSpec) -> None:
        """Test description mapping."""
        work_unit = spec_to_work_unit(sample_spec)
        assert "sample feature" in work_unit.description.lower()

    def test_maps_status_in_progress(self, sample_spec: NativeSpec) -> None:
        """Test status mapping for in_progress."""
        work_unit = spec_to_work_unit(sample_spec)
        assert work_unit.status == UnifiedStatus.IN_PROGRESS

    def test_creates_tasks_from_subtasks(self, sample_spec: NativeSpec) -> None:
        """Test tasks created from all subtasks across phases."""
        work_unit = spec_to_work_unit(sample_spec)

        # 2 + 2 + 2 subtasks = 6 tasks
        assert len(work_unit.tasks) == 6
        assert work_unit.tasks[0].id == "1.1"
        assert work_unit.tasks[2].id == "2.1"

    def test_task_includes_phase_metadata(self, sample_spec: NativeSpec) -> None:
        """Test phase info in task metadata."""
        work_unit = spec_to_work_unit(sample_spec)

        first_task = work_unit.tasks[0]
        assert first_task.metadata["phase_id"] == 1
        assert first_task.metadata["phase_name"] == "Setup"

    def test_task_includes_files(self, sample_spec: NativeSpec) -> None:
        """Test file paths preserved in tasks."""
        work_unit = spec_to_work_unit(sample_spec)

        first_task = work_unit.tasks[0]
        assert first_task.files == ["src/feature/index.ts"]

    def test_preserves_requirements_in_metadata(self, sample_spec: NativeSpec) -> None:
        """Test requirements preserved in metadata."""
        work_unit = spec_to_work_unit(sample_spec)
        assert "requirements" in work_unit.metadata
        assert len(work_unit.metadata["requirements"]) == 3

    def test_preserves_acceptance_criteria_in_metadata(self, sample_spec: NativeSpec) -> None:
        """Test AC preserved in metadata."""
        work_unit = spec_to_work_unit(sample_spec)
        assert "acceptance_criteria" in work_unit.metadata
        assert len(work_unit.metadata["acceptance_criteria"]) == 3

    def test_maps_done_status(self, tmp_path: Path) -> None:
        """Test status mapping for done."""
        spec_dir = tmp_path / ".auto-claude" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        plan = {"status": "done", "phases": []}
        (spec_dir / "implementation_plan.json").write_text(json.dumps(plan))

        spec = parse_spec(spec_dir)
        work_unit = spec_to_work_unit(spec)
        assert work_unit.status == UnifiedStatus.COMPLETED

    def test_handles_unknown_status_gracefully(self, tmp_path: Path) -> None:
        """Test graceful handling of unknown status."""
        spec_dir = tmp_path / ".auto-claude" / "specs" / "001-test"
        spec_dir.mkdir(parents=True)
        plan = {"status": "unknown-status", "phases": []}
        (spec_dir / "implementation_plan.json").write_text(json.dumps(plan))

        spec = parse_spec(spec_dir)
        work_unit = spec_to_work_unit(spec)
        assert work_unit.status == UnifiedStatus.PENDING


class TestSubtaskToTask:
    """Tests for subtask_to_task function."""

    def test_maps_id(self) -> None:
        """Test ID mapping."""
        subtask = NativeSubtask(id="1.1", description="Test", status="pending")
        phase = NativePhase(id=1, name="Setup", status="pending")

        task = subtask_to_task(subtask, phase)
        assert task.id == "1.1"

    def test_maps_title_from_description(self) -> None:
        """Test title from description."""
        subtask = NativeSubtask(id="1.1", description="Create files", status="pending")
        phase = NativePhase(id=1, name="Setup", status="pending")

        task = subtask_to_task(subtask, phase)
        assert task.title == "Create files"

    def test_maps_status(self) -> None:
        """Test status mapping."""
        subtask = NativeSubtask(id="1.1", description="Test", status="in_progress")
        phase = NativePhase(id=1, name="Setup", status="pending")

        task = subtask_to_task(subtask, phase)
        assert task.status == UnifiedStatus.IN_PROGRESS

    def test_includes_files(self) -> None:
        """Test files included."""
        subtask = NativeSubtask(
            id="1.1",
            description="Test",
            status="pending",
            files=["src/test.ts", "src/test2.ts"]
        )
        phase = NativePhase(id=1, name="Setup", status="pending")

        task = subtask_to_task(subtask, phase)
        assert task.files == ["src/test.ts", "src/test2.ts"]

    def test_includes_phase_in_description(self) -> None:
        """Test phase info in description."""
        subtask = NativeSubtask(id="1.1", description="Test", status="pending")
        phase = NativePhase(id=2, name="Implementation", status="pending")

        task = subtask_to_task(subtask, phase)
        assert "Phase 2" in task.description
        assert "Implementation" in task.description


# =============================================================================
# Backward Compatibility Tests
# =============================================================================


class TestBackwardCompatibility:
    """Tests ensuring 100% backward compatibility with existing specs."""

    def test_parses_existing_spec_format(self, fixtures_path: Path) -> None:
        """Test parsing existing spec format works correctly."""
        spec = parse_spec(fixtures_path / "native" / "001-sample")

        # All expected fields should be extracted
        assert spec.id == "001"
        assert spec.name == "sample"
        assert len(spec.requirements) > 0
        assert len(spec.acceptance_criteria) > 0
        assert len(spec.phases) > 0

    def test_preserves_all_metadata(self, fixtures_path: Path) -> None:
        """Test all metadata from original files is preserved."""
        spec = parse_spec(fixtures_path / "native" / "001-sample")

        # Metadata from implementation_plan.json should be preserved
        assert "spec_id" in spec.metadata or "created_at" in spec.metadata

    def test_handles_all_native_statuses(self, tmp_path: Path) -> None:
        """Test all Native status values are handled."""
        statuses = ["pending", "in_progress", "ai_review", "human_review", "done", "failed"]

        for status in statuses:
            spec_dir = tmp_path / ".auto-claude" / "specs" / f"00{statuses.index(status) + 1}-test"
            spec_dir.mkdir(parents=True, exist_ok=True)
            plan = {"status": status, "phases": []}
            (spec_dir / "implementation_plan.json").write_text(json.dumps(plan))

            spec = parse_spec(spec_dir)
            work_unit = spec_to_work_unit(spec)

            # Should not raise error - all statuses should map
            assert work_unit.status is not None
