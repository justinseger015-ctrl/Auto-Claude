"""Unified data models for cross-framework compatibility.

This module provides dataclasses that represent work items in a
framework-agnostic way. Adapters translate framework-specific data
into these unified models.

Story 1.2: Create Unified Data Model (AC: #1, #4, #5)
"""

from dataclasses import dataclass, field
from typing import Any

from models.enums import UnifiedStatus


# =============================================================================
# Core Data Models
# =============================================================================


@dataclass
class Checkpoint:
    """Unified representation of Task (BMAD) or Verification (Native).

    A checkpoint is a specific verification point within a task that
    can be marked as completed.

    Attributes:
        id: Unique checkpoint identifier.
        description: Human-readable description of what to verify.
        completed: Whether this checkpoint has been completed.
    """

    id: str
    description: str
    completed: bool = False


@dataclass
class Task:
    """Unified representation of Story (BMAD) or Subtask (Native).

    A task is a discrete piece of work that belongs to a work unit.
    It may contain multiple checkpoints for verification.

    Attributes:
        id: Unique task identifier (e.g., "1-2" for story 1.2).
        title: Human-readable title.
        description: Full task description.
        status: Current unified status.
        acceptance_criteria: List of AC strings (from BDD scenarios).
        files: List of file paths affected by this task.
        checkpoints: List of verification checkpoints.
        metadata: Framework-specific additional data.
    """

    id: str
    title: str
    description: str = ""
    status: UnifiedStatus = UnifiedStatus.PENDING
    acceptance_criteria: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkUnit:
    """Unified representation of Epic (BMAD) or Phase (Native).

    A work unit is a high-level grouping of related tasks that
    represents a major piece of functionality.

    Attributes:
        id: Unique work unit identifier (e.g., "1" for epic 1).
        title: Human-readable title.
        description: Full description including goals.
        status: Current unified status.
        tasks: List of tasks within this work unit.
        metadata: Framework-specific additional data.
    """

    id: str
    title: str
    description: str = ""
    status: UnifiedStatus = UnifiedStatus.PENDING
    tasks: list[Task] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectStatus:
    """Aggregated project status from framework artifacts.

    Provides a high-level view of project progress across all
    work units and tasks.

    Attributes:
        framework: Active framework name ('bmad' or 'native').
        work_units: All work units in project.
        active_task: Currently active task (if any).
        total_tasks: Total number of tasks.
        completed_tasks: Number of completed tasks.
        progress_percentage: Overall completion percentage (0-100).
    """

    framework: str
    work_units: list[WorkUnit] = field(default_factory=list)
    active_task: Task | None = None
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0


# =============================================================================
# Status Mapping Tables
# =============================================================================

BMAD_STATUS_MAP: dict[str, UnifiedStatus] = {
    "backlog": UnifiedStatus.PENDING,
    "ready-for-dev": UnifiedStatus.PENDING,
    "in-progress": UnifiedStatus.IN_PROGRESS,
    "review": UnifiedStatus.REVIEW,
    "blocked": UnifiedStatus.BLOCKED,
    "done": UnifiedStatus.COMPLETED,
    "optional": UnifiedStatus.PENDING,  # For retrospective status
}

NATIVE_STATUS_MAP: dict[str, UnifiedStatus] = {
    "pending": UnifiedStatus.PENDING,
    "in_progress": UnifiedStatus.IN_PROGRESS,
    "ai_review": UnifiedStatus.REVIEW,
    "human_review": UnifiedStatus.REVIEW,
    "done": UnifiedStatus.COMPLETED,
    "failed": UnifiedStatus.FAILED,
}


# =============================================================================
# Status Mapping Functions
# =============================================================================


def map_bmad_status(status: str) -> UnifiedStatus:
    """Map BMAD status string to UnifiedStatus.

    Args:
        status: BMAD status string (e.g., "in-progress", "done").

    Returns:
        Corresponding UnifiedStatus enum value.

    Raises:
        ValueError: If status is not a recognized BMAD status.

    Example:
        >>> map_bmad_status("in-progress")
        <UnifiedStatus.IN_PROGRESS: 'in_progress'>
    """
    if status not in BMAD_STATUS_MAP:
        raise ValueError(
            f"Unknown BMAD status: {status}. "
            f"Valid: {list(BMAD_STATUS_MAP.keys())}"
        )
    return BMAD_STATUS_MAP[status]


def map_native_status(status: str) -> UnifiedStatus:
    """Map Native status string to UnifiedStatus.

    Args:
        status: Native status string (e.g., "in_progress", "done").

    Returns:
        Corresponding UnifiedStatus enum value.

    Raises:
        ValueError: If status is not a recognized Native status.

    Example:
        >>> map_native_status("ai_review")
        <UnifiedStatus.REVIEW: 'review'>
    """
    if status not in NATIVE_STATUS_MAP:
        raise ValueError(
            f"Unknown Native status: {status}. "
            f"Valid: {list(NATIVE_STATUS_MAP.keys())}"
        )
    return NATIVE_STATUS_MAP[status]
