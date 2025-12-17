"""BMAD artifact parser.

Parses BMAD sprint status YAML files and story markdown files to extract
epic and story status information. Converts BMAD-specific data to unified
models.

Story 2.1: BMAD Sprint Status Parser (AC: #1, #2, #3, #4)
Story 2.2: BMAD Story File Parser (AC: #1, #2, #3, #4)
Story 2.3: BMAD Workflow Status Parser (AC: #1, #2, #3)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from models import UnifiedStatus, Task, Checkpoint, map_bmad_status
from adapters.exceptions import ParseError  # Shared exception from adapters base

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SprintStatus:
    """Parsed BMAD sprint status.

    Contains extracted information from bmm-sprint-status.yaml including
    epic statuses, story statuses, and retrospective statuses.

    Attributes:
        project_name: Human-readable project name.
        project_key: Machine-friendly project identifier.
        tracking_system: Type of tracking (e.g., 'file-system', 'linear').
        story_location: Relative path to story files.
        epics: Mapping of epic key to status string (e.g., 'epic-1': 'in-progress').
        stories: Mapping of story key to status string (e.g., '1-1-name': 'ready-for-dev').
        retrospectives: Mapping of retrospective key to status (e.g., 'epic-1-retrospective': 'optional').
        metadata: Additional parsed data (generated date, etc.).
    """

    project_name: str
    project_key: str
    tracking_system: str
    story_location: str
    epics: dict[str, str] = field(default_factory=dict)
    stories: dict[str, str] = field(default_factory=dict)
    retrospectives: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# File Discovery
# =============================================================================


def find_sprint_status_file(project_path: Path) -> Path | None:
    """Find BMAD sprint status file in project.

    Searches for the sprint status file at the primary location first,
    then falls back to legacy locations. Returns None if not found
    (graceful degradation per Critical Rule #5).

    Args:
        project_path: Root path of the project.

    Returns:
        Path to sprint status file, or None if not found.
    """
    # Check primary location
    primary = project_path / "_bmad-output" / "bmm-sprint-status.yaml"
    if primary.exists():
        logger.debug(f"Found sprint status at primary location: {primary}")
        return primary

    # Check legacy location
    legacy = project_path / "_bmad-output" / "sprint-status.yaml"
    if legacy.exists():
        logger.info(f"Using legacy sprint status location: {legacy}")
        return legacy

    logger.info("No sprint status file found, using defaults")
    return None


# =============================================================================
# Parsing Functions
# =============================================================================


def parse_sprint_status(file_path: Path) -> SprintStatus:
    """Parse BMAD sprint status YAML file.

    Extracts project metadata, epic statuses, story statuses, and
    retrospective statuses from the YAML file.

    Args:
        file_path: Path to sprint-status.yaml file.

    Returns:
        Parsed SprintStatus object.

    Raises:
        ParseError: If YAML is malformed or required fields are missing.
    """
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ParseError(f"Invalid YAML in {file_path}: {e}") from e
    except FileNotFoundError as e:
        raise ParseError(f"Sprint status file not found: {file_path}") from e

    if not data:
        raise ParseError(f"Empty sprint status file: {file_path}")

    # Extract development_status section
    dev_status = data.get("development_status", {})

    # Categorize entries
    epics: dict[str, str] = {}
    stories: dict[str, str] = {}
    retrospectives: dict[str, str] = {}

    for key, status in dev_status.items():
        if key.startswith("epic-") and "-retrospective" in key:
            retrospectives[key] = status
        elif key.startswith("epic-"):
            epics[key] = status
        else:
            # Story format: N-N-name (e.g., 1-1-create-adapter)
            stories[key] = status

    return SprintStatus(
        project_name=data.get("project", "Unknown"),
        project_key=data.get("project_key", "unknown"),
        tracking_system=data.get("tracking_system", "file-system"),
        story_location=data.get("story_location", "_bmad-output/stories"),
        epics=epics,
        stories=stories,
        retrospectives=retrospectives,
        metadata={
            "generated": data.get("generated"),
            "file_path": str(file_path),
        },
    )


def default_sprint_status() -> SprintStatus:
    """Create default empty sprint status.

    Used when no sprint status file is found (graceful degradation).

    Returns:
        SprintStatus with default values.
    """
    return SprintStatus(
        project_name="Unknown",
        project_key="unknown",
        tracking_system="file-system",
        story_location="_bmad-output/stories",
    )


# =============================================================================
# Status Conversion
# =============================================================================


def get_unified_epic_status(sprint_status: SprintStatus, epic_num: int) -> UnifiedStatus:
    """Get unified status for an epic.

    Args:
        sprint_status: Parsed sprint status.
        epic_num: Epic number (1, 2, etc.).

    Returns:
        UnifiedStatus enum value.
    """
    key = f"epic-{epic_num}"
    bmad_status = sprint_status.epics.get(key, "backlog")
    try:
        return map_bmad_status(bmad_status)
    except ValueError:
        logger.warning(f"Unknown BMAD status '{bmad_status}' for {key}, defaulting to PENDING")
        return UnifiedStatus.PENDING


def get_unified_story_status(sprint_status: SprintStatus, story_key: str) -> UnifiedStatus:
    """Get unified status for a story.

    Args:
        sprint_status: Parsed sprint status.
        story_key: Story key (e.g., '1-1-create-adapter').

    Returns:
        UnifiedStatus enum value.
    """
    bmad_status = sprint_status.stories.get(story_key, "backlog")
    try:
        return map_bmad_status(bmad_status)
    except ValueError:
        logger.warning(f"Unknown BMAD status '{bmad_status}' for {story_key}, defaulting to PENDING")
        return UnifiedStatus.PENDING


def get_unified_retrospective_status(sprint_status: SprintStatus, epic_num: int) -> str:
    """Get retrospective status for an epic.

    Note: Retrospective status is not mapped to UnifiedStatus as it has
    different semantics (optional/done vs task status).

    Args:
        sprint_status: Parsed sprint status.
        epic_num: Epic number (1, 2, etc.).

    Returns:
        Retrospective status string ('optional' or 'done').
    """
    key = f"epic-{epic_num}-retrospective"
    return sprint_status.retrospectives.get(key, "optional")


# =============================================================================
# Story Data Model
# =============================================================================


@dataclass
class BMADStory:
    """Parsed BMAD story file.

    Contains extracted information from a BMAD story markdown file including
    story metadata, acceptance criteria, and task checkboxes.

    Attributes:
        id: Story identifier (e.g., "1-2").
        key: Full story key from filename (e.g., "1-2-create-unified-data-model").
        title: Human-readable title from header.
        status: BMAD status string (e.g., "ready-for-dev").
        epic_num: Epic number extracted from filename.
        story_num: Story number within epic.
        user_story: Full "As a... I want... so that..." text.
        acceptance_criteria: List of AC strings.
        tasks: List of task dicts with text, completed, and subtasks.
        dev_notes: Raw dev notes section content.
        file_path: Source file path.
    """

    id: str
    key: str
    title: str
    status: str
    epic_num: int
    story_num: int
    user_story: str
    acceptance_criteria: list[str] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    dev_notes: str = ""
    file_path: Path | None = None


# =============================================================================
# Story File Discovery
# =============================================================================


def find_story_files(project_path: Path) -> list[Path]:
    """Find all BMAD story files in project.

    Searches the `_bmad-output/stories/` directory for markdown files
    matching the pattern `N-N-*.md` (e.g., `1-2-create-unified-data-model.md`).

    Args:
        project_path: Root path of the project.

    Returns:
        List of story file paths, sorted by epic/story number.
    """
    stories_dir = project_path / "_bmad-output" / "stories"
    if not stories_dir.exists():
        logger.info("No stories directory found")
        return []

    # Match pattern: N-N-name.md
    pattern = re.compile(r"^(\d+)-(\d+)-.+\.md$")
    story_files = []

    for file in stories_dir.iterdir():
        if file.is_file() and pattern.match(file.name):
            story_files.append(file)

    # Sort by epic number, then story number
    def sort_key(p: Path) -> tuple[int, int]:
        match = pattern.match(p.name)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0)

    return sorted(story_files, key=sort_key)


# =============================================================================
# Story Parsing Functions
# =============================================================================


def parse_story_file(file_path: Path) -> BMADStory:
    """Parse a BMAD story markdown file.

    Extracts story metadata, user story, acceptance criteria, and tasks
    from the markdown file structure.

    Args:
        file_path: Path to story markdown file.

    Returns:
        Parsed BMADStory object.

    Raises:
        ValueError: If filename doesn't match expected pattern.
        ParseError: If file cannot be read or is malformed.
    """
    # Extract epic and story numbers from filename
    filename_match = re.match(r"(\d+)-(\d+)-(.+)\.md", file_path.name)
    if not filename_match:
        raise ValueError(f"Invalid story filename format: {file_path.name}")

    epic_num = int(filename_match.group(1))
    story_num = int(filename_match.group(2))
    key = file_path.stem  # e.g., "1-2-create-unified-data-model"

    try:
        content = file_path.read_text()
    except OSError as e:
        raise ParseError(f"Cannot read story file {file_path}: {e}") from e

    # Extract title from header
    title_match = re.search(r"^# Story \d+\.\d+: (.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else key

    # Extract status
    status_match = re.search(r"^Status:\s*(.+)$", content, re.MULTILINE)
    status = status_match.group(1).strip() if status_match else "backlog"

    # Extract user story
    user_story = _extract_section(content, "## Story")

    # Extract acceptance criteria
    ac_section = _extract_section(content, "## Acceptance Criteria")
    acceptance_criteria = _parse_acceptance_criteria(ac_section)

    # Extract tasks
    tasks_section = _extract_section(content, "## Tasks / Subtasks")
    tasks = _parse_tasks(tasks_section)

    # Extract dev notes
    dev_notes = _extract_section(content, "## Dev Notes")

    return BMADStory(
        id=f"{epic_num}-{story_num}",
        key=key,
        title=title,
        status=status,
        epic_num=epic_num,
        story_num=story_num,
        user_story=user_story,
        acceptance_criteria=acceptance_criteria,
        tasks=tasks,
        dev_notes=dev_notes,
        file_path=file_path,
    )


def _extract_section(content: str, header: str) -> str:
    """Extract content between header and next ## header.

    Args:
        content: Full markdown content.
        header: Header to search for (e.g., "## Story").

    Returns:
        Section content between header and next header, stripped.
    """
    pattern = rf"{re.escape(header)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_acceptance_criteria(section: str) -> list[str]:
    """Parse acceptance criteria from section content.

    Extracts numbered criteria (1., 2., etc.) preserving multi-line
    content including BDD format (Given/When/Then).

    Args:
        section: Acceptance Criteria section content.

    Returns:
        List of AC strings.
    """
    criteria: list[str] = []
    current: list[str] = []

    for line in section.split("\n"):
        if re.match(r"^\d+\.", line):
            if current:
                criteria.append("\n".join(current).strip())
            current = [line]
        elif current:
            current.append(line)

    if current:
        criteria.append("\n".join(current).strip())

    return criteria


def _parse_tasks(section: str) -> list[dict[str, Any]]:
    """Parse task checkboxes from section content.

    Extracts top-level tasks and their subtasks with completion status.

    Args:
        section: Tasks / Subtasks section content.

    Returns:
        List of task dicts with text, completed, and subtasks.
    """
    tasks: list[dict[str, Any]] = []
    current_task: dict[str, Any] | None = None

    for line in section.split("\n"):
        # Top-level task
        if re.match(r"^- \[([ x])\]", line):
            if current_task:
                tasks.append(current_task)
            completed = "[x]" in line
            text = re.sub(r"^- \[[ x]\]\s*", "", line)
            current_task = {"text": text, "completed": completed, "subtasks": []}
        # Subtask (indented)
        elif re.match(r"^\s+- \[([ x])\]", line) and current_task:
            completed = "[x]" in line
            text = re.sub(r"^\s+- \[[ x]\]\s*", "", line)
            current_task["subtasks"].append({"text": text, "completed": completed})

    if current_task:
        tasks.append(current_task)

    return tasks


# =============================================================================
# Story to Task Conversion
# =============================================================================


def story_to_task(story: BMADStory) -> Task:
    """Convert BMAD story to unified Task model.

    Maps story fields to Task dataclass, converts acceptance criteria
    to checkpoints, and preserves BMAD-specific data in metadata.

    Args:
        story: Parsed BMAD story.

    Returns:
        Unified Task dataclass.
    """
    # Convert AC to checkpoints
    checkpoints = [
        Checkpoint(id=f"ac-{i+1}", description=ac, completed=False)
        for i, ac in enumerate(story.acceptance_criteria)
    ]

    # Map status with graceful fallback
    try:
        unified_status = map_bmad_status(story.status)
    except ValueError:
        logger.warning(f"Unknown BMAD status '{story.status}' for story {story.id}, defaulting to PENDING")
        unified_status = UnifiedStatus.PENDING

    return Task(
        id=story.id,
        title=story.title,
        description=story.user_story,
        status=unified_status,
        acceptance_criteria=story.acceptance_criteria,
        files=[],  # Populated from dev notes or git
        checkpoints=checkpoints,
        metadata={
            "key": story.key,
            "epic_num": story.epic_num,
            "story_num": story.story_num,
            "tasks": story.tasks,
            "dev_notes": story.dev_notes,
            "source_file": str(story.file_path) if story.file_path else None,
        },
    )


# =============================================================================
# Workflow Status Data Model
# =============================================================================


@dataclass
class WorkflowStatus:
    """Parsed BMAD workflow status.

    Contains extracted information from bmm-workflow-status.yaml including
    current workflow phase, step, and context.

    Attributes:
        workflow_name: Name of the workflow (e.g., "create-story").
        status: Current status ("active", "paused", "complete").
        current_step: Current step number in the workflow.
        steps_completed: List of completed step numbers.
        started_at: When the workflow was started.
        context: Workflow context dict (may include story_key, epic_num, etc.).
        blockers: List of blocker strings.
        next_action: Recommended next action string.
    """

    workflow_name: str
    status: str  # "active", "paused", "complete", "inactive"
    current_step: int
    steps_completed: list[int] = field(default_factory=list)
    started_at: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    next_action: str = ""


# =============================================================================
# Workflow File Discovery
# =============================================================================


def find_workflow_status_file(project_path: Path) -> Path | None:
    """Find BMAD workflow status file in project.

    Searches for the workflow status file at the expected location.
    Returns None if not found (graceful degradation - workflows are optional).

    Args:
        project_path: Root path of the project.

    Returns:
        Path to workflow status file, or None if not found.
    """
    workflow_file = project_path / "_bmad-output" / "bmm-workflow-status.yaml"
    if workflow_file.exists():
        logger.debug(f"Found workflow status at: {workflow_file}")
        return workflow_file

    logger.debug("No workflow status file found")
    return None


# =============================================================================
# Workflow Parsing Functions
# =============================================================================


def parse_workflow_status(file_path: Path) -> WorkflowStatus:
    """Parse BMAD workflow status YAML file.

    Extracts workflow metadata, current phase/step, and context information.

    Args:
        file_path: Path to workflow-status.yaml file.

    Returns:
        Parsed WorkflowStatus object.

    Raises:
        ParseError: If YAML is malformed.
    """
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ParseError(f"Invalid YAML in {file_path}: {e}") from e
    except FileNotFoundError as e:
        raise ParseError(f"Workflow status file not found: {file_path}") from e

    if not data:
        return WorkflowStatus(
            workflow_name="unknown",
            status="inactive",
            current_step=0,
            steps_completed=[],
        )

    # Parse started_at timestamp
    started_at = None
    if data.get("started_at"):
        try:
            timestamp = data["started_at"]
            if isinstance(timestamp, str):
                started_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif isinstance(timestamp, datetime):
                started_at = timestamp
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse started_at timestamp: {data.get('started_at')}")

    return WorkflowStatus(
        workflow_name=data.get("workflow", "unknown"),
        status=data.get("status", "inactive"),
        current_step=data.get("current_step", 0),
        steps_completed=data.get("steps_completed", []),
        started_at=started_at,
        context=data.get("context", {}),
        blockers=data.get("blockers", []),
        next_action=data.get("next_action", ""),
    )


def default_workflow_status() -> WorkflowStatus:
    """Create default empty workflow status.

    Used when no workflow status file is found (graceful degradation).

    Returns:
        WorkflowStatus with default inactive values.
    """
    return WorkflowStatus(
        workflow_name="none",
        status="inactive",
        current_step=0,
        steps_completed=[],
    )


# =============================================================================
# Workflow Integration Functions
# =============================================================================


def get_workflow_context_for_story(
    workflow_status: WorkflowStatus | None,
    story_key: str
) -> dict[str, Any] | None:
    """Get workflow context if it applies to the given story.

    Checks if the current workflow is related to the specified story
    and returns relevant context if so.

    Args:
        workflow_status: Current workflow status (or None).
        story_key: Story key to check (e.g., "1-2-create-unified-data-model").

    Returns:
        Workflow context dict if applicable, None otherwise.
    """
    if not workflow_status:
        return None

    if workflow_status.context.get("story_key") == story_key:
        return {
            "workflow": workflow_status.workflow_name,
            "status": workflow_status.status,
            "current_step": workflow_status.current_step,
            "steps_completed": workflow_status.steps_completed,
            "next_action": workflow_status.next_action,
            "blockers": workflow_status.blockers,
            "started_at": workflow_status.started_at.isoformat() if workflow_status.started_at else None,
        }

    return None


def get_active_workflow_info(
    workflow_status: WorkflowStatus | None
) -> dict[str, Any] | None:
    """Get summary info for display if there's an active workflow.

    Args:
        workflow_status: Current workflow status (or None).

    Returns:
        Dict with workflow summary if active, None otherwise.
    """
    if not workflow_status or workflow_status.status not in ("active", "paused"):
        return None

    return {
        "workflow_name": workflow_status.workflow_name,
        "status": workflow_status.status,
        "current_step": workflow_status.current_step,
        "total_completed": len(workflow_status.steps_completed),
        "next_action": workflow_status.next_action,
        "has_blockers": len(workflow_status.blockers) > 0,
        "blockers": workflow_status.blockers,
    }
