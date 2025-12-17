"""Unit tests for BMAD sprint status parser.

Tests file discovery, YAML parsing, status conversion, and error handling.

Story 2.1: BMAD Sprint Status Parser (AC: all)
"""

import pytest
from pathlib import Path

from adapters.bmad.parser import (
    SprintStatus,
    ParseError,
    find_sprint_status_file,
    parse_sprint_status,
    default_sprint_status,
    get_unified_epic_status,
    get_unified_story_status,
    get_unified_retrospective_status,
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
def valid_sprint_status(fixtures_path: Path) -> SprintStatus:
    """Return parsed valid sprint status fixture."""
    return parse_sprint_status(fixtures_path / "bmad" / "valid-sprint-status.yaml")


# =============================================================================
# File Discovery Tests
# =============================================================================


class TestFindSprintStatusFile:
    """Tests for find_sprint_status_file function."""

    def test_finds_primary_location(self, tmp_path: Path) -> None:
        """Test finding sprint status at primary location."""
        status_file = tmp_path / "_bmad-output" / "bmm-sprint-status.yaml"
        status_file.parent.mkdir(parents=True)
        status_file.write_text("project: Test")

        result = find_sprint_status_file(tmp_path)
        assert result == status_file

    def test_finds_legacy_location(self, tmp_path: Path) -> None:
        """Test fallback to legacy location."""
        status_file = tmp_path / "_bmad-output" / "sprint-status.yaml"
        status_file.parent.mkdir(parents=True)
        status_file.write_text("project: Test")

        result = find_sprint_status_file(tmp_path)
        assert result == status_file

    def test_prefers_primary_over_legacy(self, tmp_path: Path) -> None:
        """Test primary location takes precedence."""
        bmad_dir = tmp_path / "_bmad-output"
        bmad_dir.mkdir(parents=True)

        primary = bmad_dir / "bmm-sprint-status.yaml"
        legacy = bmad_dir / "sprint-status.yaml"
        primary.write_text("project: Primary")
        legacy.write_text("project: Legacy")

        result = find_sprint_status_file(tmp_path)
        assert result == primary

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """Test graceful handling when file not found."""
        result = find_sprint_status_file(tmp_path)
        assert result is None


# =============================================================================
# Parsing Tests
# =============================================================================


class TestParseSprintStatus:
    """Tests for parse_sprint_status function."""

    def test_parses_project_metadata(self, valid_sprint_status: SprintStatus) -> None:
        """Test extraction of project metadata."""
        assert valid_sprint_status.project_name == "Test Project"
        assert valid_sprint_status.project_key == "test-project"
        assert valid_sprint_status.tracking_system == "file-system"
        assert valid_sprint_status.story_location == "_bmad-output/stories"

    def test_extracts_epics(self, valid_sprint_status: SprintStatus) -> None:
        """Test epic extraction from sprint status."""
        assert "epic-1" in valid_sprint_status.epics
        assert valid_sprint_status.epics["epic-1"] == "in-progress"
        assert "epic-2" in valid_sprint_status.epics
        assert valid_sprint_status.epics["epic-2"] == "backlog"

    def test_extracts_stories(self, valid_sprint_status: SprintStatus) -> None:
        """Test story extraction from sprint status."""
        stories = valid_sprint_status.stories
        assert "1-1-first-story" in stories
        assert stories["1-1-first-story"] == "ready-for-dev"
        assert "1-2-second-story" in stories
        assert stories["1-2-second-story"] == "in-progress"
        assert "1-3-third-story" in stories
        assert stories["1-3-third-story"] == "review"
        assert "1-4-fourth-story" in stories
        assert stories["1-4-fourth-story"] == "done"

    def test_extracts_retrospectives(self, valid_sprint_status: SprintStatus) -> None:
        """Test retrospective extraction from sprint status."""
        retros = valid_sprint_status.retrospectives
        assert "epic-1-retrospective" in retros
        assert retros["epic-1-retrospective"] == "optional"

    def test_stores_metadata(self, valid_sprint_status: SprintStatus) -> None:
        """Test metadata storage."""
        assert "generated" in valid_sprint_status.metadata
        assert "file_path" in valid_sprint_status.metadata

    def test_raises_on_malformed_yaml(self, tmp_path: Path) -> None:
        """Test ParseError on malformed YAML."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{ invalid yaml [")

        with pytest.raises(ParseError, match="Invalid YAML"):
            parse_sprint_status(bad_file)

    def test_raises_on_empty_file(self, tmp_path: Path) -> None:
        """Test ParseError on empty file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        with pytest.raises(ParseError, match="Empty sprint status"):
            parse_sprint_status(empty_file)

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Test ParseError on missing file."""
        missing = tmp_path / "nonexistent.yaml"

        with pytest.raises(ParseError, match="not found"):
            parse_sprint_status(missing)

    def test_handles_missing_optional_fields(self, tmp_path: Path) -> None:
        """Test graceful handling of missing optional fields."""
        minimal_file = tmp_path / "minimal.yaml"
        minimal_file.write_text("development_status:\n  epic-1: backlog")

        status = parse_sprint_status(minimal_file)
        assert status.project_name == "Unknown"
        assert status.project_key == "unknown"
        assert status.tracking_system == "file-system"


class TestDefaultSprintStatus:
    """Tests for default_sprint_status function."""

    def test_returns_empty_status(self) -> None:
        """Test default status has expected values."""
        status = default_sprint_status()
        assert status.project_name == "Unknown"
        assert status.project_key == "unknown"
        assert len(status.epics) == 0
        assert len(status.stories) == 0


# =============================================================================
# Status Conversion Tests
# =============================================================================


class TestStatusConversion:
    """Tests for status conversion functions."""

    def test_get_unified_epic_status_in_progress(self, valid_sprint_status: SprintStatus) -> None:
        """Test epic status conversion for in-progress."""
        status = get_unified_epic_status(valid_sprint_status, 1)
        assert status == UnifiedStatus.IN_PROGRESS

    def test_get_unified_epic_status_backlog(self, valid_sprint_status: SprintStatus) -> None:
        """Test epic status conversion for backlog."""
        status = get_unified_epic_status(valid_sprint_status, 2)
        assert status == UnifiedStatus.PENDING

    def test_get_unified_epic_status_missing(self, valid_sprint_status: SprintStatus) -> None:
        """Test default status for missing epic."""
        status = get_unified_epic_status(valid_sprint_status, 99)
        assert status == UnifiedStatus.PENDING

    def test_get_unified_story_status_ready_for_dev(self, valid_sprint_status: SprintStatus) -> None:
        """Test story status conversion for ready-for-dev."""
        status = get_unified_story_status(valid_sprint_status, "1-1-first-story")
        assert status == UnifiedStatus.PENDING

    def test_get_unified_story_status_in_progress(self, valid_sprint_status: SprintStatus) -> None:
        """Test story status conversion for in-progress."""
        status = get_unified_story_status(valid_sprint_status, "1-2-second-story")
        assert status == UnifiedStatus.IN_PROGRESS

    def test_get_unified_story_status_review(self, valid_sprint_status: SprintStatus) -> None:
        """Test story status conversion for review."""
        status = get_unified_story_status(valid_sprint_status, "1-3-third-story")
        assert status == UnifiedStatus.REVIEW

    def test_get_unified_story_status_done(self, valid_sprint_status: SprintStatus) -> None:
        """Test story status conversion for done."""
        status = get_unified_story_status(valid_sprint_status, "1-4-fourth-story")
        assert status == UnifiedStatus.COMPLETED

    def test_get_unified_story_status_missing(self, valid_sprint_status: SprintStatus) -> None:
        """Test default status for missing story."""
        status = get_unified_story_status(valid_sprint_status, "99-99-nonexistent")
        assert status == UnifiedStatus.PENDING

    def test_get_unified_retrospective_status(self, valid_sprint_status: SprintStatus) -> None:
        """Test retrospective status retrieval."""
        status = get_unified_retrospective_status(valid_sprint_status, 1)
        assert status == "optional"

    def test_get_unified_retrospective_status_missing(self, valid_sprint_status: SprintStatus) -> None:
        """Test default retrospective status for missing epic."""
        status = get_unified_retrospective_status(valid_sprint_status, 99)
        assert status == "optional"
