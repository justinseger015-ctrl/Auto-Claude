"""Unit tests for BMAD story file parser.

Tests story file discovery, markdown parsing, AC extraction, and Task conversion.

Story 2.2: BMAD Story File Parser (AC: all)
"""

import pytest
from pathlib import Path

from adapters.bmad.parser import (
    BMADStory,
    ParseError,
    find_story_files,
    parse_story_file,
    story_to_task,
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
def test_story(fixtures_path: Path) -> BMADStory:
    """Return parsed test story fixture."""
    return parse_story_file(fixtures_path / "bmad" / "stories" / "1-1-test-story.md")


# =============================================================================
# Story File Discovery Tests
# =============================================================================


class TestFindStoryFiles:
    """Tests for find_story_files function."""

    def test_returns_empty_when_no_directory(self, tmp_path: Path) -> None:
        """Test graceful handling when stories dir doesn't exist."""
        result = find_story_files(tmp_path)
        assert result == []

    def test_returns_empty_when_no_matching_files(self, tmp_path: Path) -> None:
        """Test empty result when no matching files found."""
        stories_dir = tmp_path / "_bmad-output" / "stories"
        stories_dir.mkdir(parents=True)
        (stories_dir / "readme.md").write_text("Not a story")

        result = find_story_files(tmp_path)
        assert result == []

    def test_finds_matching_files(self, tmp_path: Path) -> None:
        """Test finding story files matching pattern."""
        stories_dir = tmp_path / "_bmad-output" / "stories"
        stories_dir.mkdir(parents=True)
        (stories_dir / "1-1-first-story.md").write_text("# Story 1.1")

        result = find_story_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "1-1-first-story.md"

    def test_returns_sorted_by_epic_then_story(self, tmp_path: Path) -> None:
        """Test story files are sorted correctly."""
        stories_dir = tmp_path / "_bmad-output" / "stories"
        stories_dir.mkdir(parents=True)

        # Create in random order
        (stories_dir / "2-1-second-epic.md").write_text("# Story 2.1: Test")
        (stories_dir / "1-2-first-epic-second.md").write_text("# Story 1.2: Test")
        (stories_dir / "1-1-first-epic-first.md").write_text("# Story 1.1: Test")
        (stories_dir / "1-10-first-epic-tenth.md").write_text("# Story 1.10: Test")

        files = find_story_files(tmp_path)

        assert len(files) == 4
        assert files[0].name == "1-1-first-epic-first.md"
        assert files[1].name == "1-2-first-epic-second.md"
        assert files[2].name == "1-10-first-epic-tenth.md"
        assert files[3].name == "2-1-second-epic.md"

    def test_ignores_non_matching_files(self, tmp_path: Path) -> None:
        """Test files not matching pattern are ignored."""
        stories_dir = tmp_path / "_bmad-output" / "stories"
        stories_dir.mkdir(parents=True)

        (stories_dir / "1-1-valid-story.md").write_text("# Story")
        (stories_dir / "readme.md").write_text("Readme")
        (stories_dir / "index.md").write_text("Index")
        (stories_dir / "1-story.md").write_text("Missing story num")

        files = find_story_files(tmp_path)
        assert len(files) == 1


# =============================================================================
# Story Parsing Tests
# =============================================================================


class TestParseStoryFile:
    """Tests for parse_story_file function."""

    def test_extracts_title(self, test_story: BMADStory) -> None:
        """Test title extraction from header."""
        assert test_story.title == "Test Story Title"

    def test_extracts_status(self, test_story: BMADStory) -> None:
        """Test status extraction."""
        assert test_story.status == "in-progress"

    def test_extracts_epic_and_story_numbers(self, test_story: BMADStory) -> None:
        """Test epic and story number extraction from filename."""
        assert test_story.epic_num == 1
        assert test_story.story_num == 1
        assert test_story.id == "1-1"

    def test_extracts_key(self, test_story: BMADStory) -> None:
        """Test key extraction from filename."""
        assert test_story.key == "1-1-test-story"

    def test_extracts_user_story(self, test_story: BMADStory) -> None:
        """Test user story section extraction."""
        assert "test user" in test_story.user_story
        assert "test the story parser" in test_story.user_story

    def test_extracts_acceptance_criteria(self, test_story: BMADStory) -> None:
        """Test acceptance criteria extraction."""
        assert len(test_story.acceptance_criteria) == 3
        assert "Given" in test_story.acceptance_criteria[0]
        assert "When" in test_story.acceptance_criteria[0]
        assert "Then" in test_story.acceptance_criteria[0]

    def test_extracts_tasks(self, test_story: BMADStory) -> None:
        """Test task checkbox extraction."""
        assert len(test_story.tasks) == 3

        # First task is completed with subtasks
        assert test_story.tasks[0]["completed"] is True
        assert "Create test fixtures" in test_story.tasks[0]["text"]
        assert len(test_story.tasks[0]["subtasks"]) == 2

        # Second task is incomplete
        assert test_story.tasks[1]["completed"] is False

    def test_extracts_dev_notes(self, test_story: BMADStory) -> None:
        """Test dev notes section extraction."""
        assert "Dependencies" in test_story.dev_notes
        assert "Technical Details" in test_story.dev_notes

    def test_stores_file_path(self, test_story: BMADStory) -> None:
        """Test file path storage."""
        assert test_story.file_path is not None
        assert test_story.file_path.name == "1-1-test-story.md"

    def test_raises_on_invalid_filename(self, tmp_path: Path) -> None:
        """Test ValueError on invalid filename format."""
        bad_file = tmp_path / "invalid-name.md"
        bad_file.write_text("# Story")

        with pytest.raises(ValueError, match="Invalid story filename"):
            parse_story_file(bad_file)

    def test_handles_missing_sections(self, tmp_path: Path) -> None:
        """Test graceful handling of missing optional sections."""
        story_file = tmp_path / "1-1-minimal.md"
        story_file.write_text("# Story 1.1: Minimal\n\nStatus: backlog")

        story = parse_story_file(story_file)
        assert story.title == "Minimal"
        assert story.status == "backlog"
        assert story.acceptance_criteria == []
        assert story.tasks == []

    def test_defaults_status_to_backlog(self, tmp_path: Path) -> None:
        """Test default status when not specified."""
        story_file = tmp_path / "1-1-no-status.md"
        story_file.write_text("# Story 1.1: No Status")

        story = parse_story_file(story_file)
        assert story.status == "backlog"


# =============================================================================
# Story to Task Conversion Tests
# =============================================================================


class TestStoryToTask:
    """Tests for story_to_task function."""

    def test_maps_id(self, test_story: BMADStory) -> None:
        """Test ID mapping."""
        task = story_to_task(test_story)
        assert task.id == "1-1"

    def test_maps_title(self, test_story: BMADStory) -> None:
        """Test title mapping."""
        task = story_to_task(test_story)
        assert task.title == "Test Story Title"

    def test_maps_description(self, test_story: BMADStory) -> None:
        """Test description mapping from user story."""
        task = story_to_task(test_story)
        assert "test the story parser" in task.description

    def test_maps_status_in_progress(self, test_story: BMADStory) -> None:
        """Test status mapping for in-progress."""
        task = story_to_task(test_story)
        assert task.status == UnifiedStatus.IN_PROGRESS

    def test_maps_status_ready_for_dev(self, fixtures_path: Path) -> None:
        """Test status mapping for ready-for-dev."""
        # Create a story with ready-for-dev status
        story = parse_story_file(fixtures_path / "bmad" / "stories" / "1-1-test-story.md")
        story.status = "ready-for-dev"

        task = story_to_task(story)
        assert task.status == UnifiedStatus.PENDING

    def test_maps_status_done(self, test_story: BMADStory) -> None:
        """Test status mapping for done."""
        test_story.status = "done"
        task = story_to_task(test_story)
        assert task.status == UnifiedStatus.COMPLETED

    def test_converts_ac_to_checkpoints(self, test_story: BMADStory) -> None:
        """Test acceptance criteria to checkpoints conversion."""
        task = story_to_task(test_story)

        assert len(task.checkpoints) == 3
        assert task.checkpoints[0].id == "ac-1"
        assert "Given" in task.checkpoints[0].description
        assert task.checkpoints[0].completed is False

    def test_preserves_metadata(self, test_story: BMADStory) -> None:
        """Test metadata preservation."""
        task = story_to_task(test_story)

        assert task.metadata["key"] == "1-1-test-story"
        assert task.metadata["epic_num"] == 1
        assert task.metadata["story_num"] == 1
        assert "tasks" in task.metadata
        assert "dev_notes" in task.metadata
        assert "source_file" in task.metadata

    def test_handles_unknown_status_gracefully(self, test_story: BMADStory) -> None:
        """Test graceful handling of unknown status."""
        test_story.status = "unknown-status"
        task = story_to_task(test_story)
        assert task.status == UnifiedStatus.PENDING
