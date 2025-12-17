"""BMAD Method adapter implementation.

Implements the FrameworkAdapter interface for BMAD Method projects.
Parses BMAD artifacts and translates them to the unified data model.

Story 2.5: BMAD Adapter Implementation (AC: #1, #2, #3, #4, #5)
"""

import logging
from pathlib import Path

from adapters.base import FrameworkAdapter
from adapters.glossary import BMAD_GLOSSARY, GlossaryTerms
from models import WorkUnit, Task, ProjectStatus, UnifiedStatus, map_bmad_status

from .parser import (
    find_sprint_status_file,
    parse_sprint_status,
    default_sprint_status,
    find_story_files,
    parse_story_file,
    story_to_task,
    find_workflow_status_file,
    parse_workflow_status,
)

logger = logging.getLogger(__name__)


class BMADAdapter(FrameworkAdapter):
    """Adapter for BMAD Method planning framework.

    Parses BMAD artifacts (sprint-status.yaml, story files, workflow-status.yaml)
    and translates them to the unified data model.

    This adapter treats:
    - Epics as WorkUnits
    - Stories as Tasks
    - Story Tasks as Checkpoints

    Example:
        ```python
        adapter = BMADAdapter()
        work_units = adapter.parse_work_units(project_path)
        status = adapter.get_status(project_path)
        ```
    """

    def __init__(self) -> None:
        """Initialize BMAD adapter."""
        self._project_path: Path | None = None
        self._cached_work_units: list[WorkUnit] | None = None

    @property
    def name(self) -> str:
        """Return framework identifier."""
        return "bmad"

    @property
    def glossary(self) -> GlossaryTerms:
        """Return BMAD terminology mapping."""
        return BMAD_GLOSSARY

    def parse_work_units(self, project_path: Path) -> list[WorkUnit]:
        """Parse all epics as WorkUnits.

        Reads sprint status to discover epics and their statuses,
        then loads all story files and groups them by epic.

        Args:
            project_path: Root path of the project.

        Returns:
            List of epics as WorkUnit objects, sorted by epic number.
        """
        self._project_path = project_path

        # Load sprint status
        status_file = find_sprint_status_file(project_path)
        if not status_file:
            logger.info("No sprint status file found, returning empty work units")
            self._cached_work_units = []
            return []

        try:
            sprint_status = parse_sprint_status(status_file)
        except Exception as e:
            logger.error(f"Failed to parse sprint status: {e}")
            self._cached_work_units = []
            return []

        # Load all stories and group by epic
        story_files = find_story_files(project_path)
        stories_by_epic: dict[int, list[Task]] = {}

        for story_file in story_files:
            try:
                story = parse_story_file(story_file)
                task = story_to_task(story)
                if story.epic_num not in stories_by_epic:
                    stories_by_epic[story.epic_num] = []
                stories_by_epic[story.epic_num].append(task)
            except Exception as e:
                logger.warning(f"Failed to parse story {story_file}: {e}")

        # Build WorkUnits for each epic
        work_units = []
        for epic_key, epic_status in sprint_status.epics.items():
            try:
                # Extract epic number from key (e.g., "epic-1" -> 1)
                epic_num = int(epic_key.split("-")[1])

                # Map status with graceful fallback
                try:
                    unified_status = map_bmad_status(epic_status)
                except ValueError:
                    logger.warning(f"Unknown BMAD status '{epic_status}' for {epic_key}, defaulting to PENDING")
                    unified_status = UnifiedStatus.PENDING

                work_units.append(WorkUnit(
                    id=str(epic_num),
                    title=f"Epic {epic_num}",
                    description="",
                    status=unified_status,
                    tasks=stories_by_epic.get(epic_num, []),
                    metadata={
                        "epic_key": epic_key,
                        "retrospective_status": sprint_status.retrospectives.get(
                            f"epic-{epic_num}-retrospective", "optional"
                        ),
                    },
                ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse epic key '{epic_key}': {e}")

        # Sort by epic number
        work_units.sort(key=lambda w: int(w.id))
        self._cached_work_units = work_units
        return work_units

    def parse_tasks(self, work_unit_id: str) -> list[Task]:
        """Parse stories for a specific epic.

        Returns all stories (as Tasks) that belong to the specified
        epic (work unit).

        Args:
            work_unit_id: Epic ID (e.g., "1").

        Returns:
            List of stories as Task objects.

        Raises:
            ValueError: If work_unit_id is not found.
        """
        # Use cached work units if available
        if self._cached_work_units is not None:
            for work_unit in self._cached_work_units:
                if work_unit.id == work_unit_id:
                    return work_unit.tasks

        # If no cache, need to parse first
        if self._project_path:
            work_units = self.parse_work_units(self._project_path)
            for work_unit in work_units:
                if work_unit.id == work_unit_id:
                    return work_unit.tasks

        raise ValueError(f"Work unit not found: {work_unit_id}")

    def get_status(self, project_path: Path) -> ProjectStatus:
        """Get aggregated project status.

        Aggregates status information from sprint status and optionally
        workflow status to provide overall project progress.

        Args:
            project_path: Root path of the project.

        Returns:
            ProjectStatus with aggregated data including progress.
        """
        # Parse work units (will also populate cache)
        work_units = self.parse_work_units(project_path)

        # Count tasks
        total_tasks = sum(len(wu.tasks) for wu in work_units)
        completed_tasks = sum(
            1 for wu in work_units
            for task in wu.tasks
            if task.status == UnifiedStatus.COMPLETED
        )

        # Check for active workflow
        active_task = None
        workflow_file = find_workflow_status_file(project_path)
        if workflow_file:
            try:
                workflow = parse_workflow_status(workflow_file)
                if workflow.status == "active":
                    story_key = workflow.context.get("story_key")
                    if story_key:
                        for wu in work_units:
                            for task in wu.tasks:
                                if task.metadata.get("key") == story_key:
                                    active_task = task
                                    break
                            if active_task:
                                break
            except Exception as e:
                logger.warning(f"Failed to parse workflow status: {e}")

        # Calculate progress percentage
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        return ProjectStatus(
            framework="bmad",
            work_units=work_units,
            active_task=active_task,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            progress_percentage=progress,
        )
