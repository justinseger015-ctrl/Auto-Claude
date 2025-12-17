"""Abstract base class for framework adapters.

This module defines the FrameworkAdapter ABC that all concrete adapters
(BMAD, Native, future frameworks) must implement. It ensures a consistent
interface for parsing work units, tasks, and project status across different
planning methodologies.

Story 1.1: Create Adapter Infrastructure (AC: #2)
Updated in Story 1.2: Replaced stub types with real imports from models.unified
Updated: Added exception imports for proper error documentation
"""

from abc import ABC, abstractmethod
from pathlib import Path

from models import WorkUnit, Task, ProjectStatus
from adapters.exceptions import ParseError, AdapterError  # noqa: F401 - exported for subclasses


class FrameworkAdapter(ABC):
    """Abstract base class for planning framework adapters.

    Each supported planning framework (BMAD Method, Native track, etc.)
    implements this interface to provide consistent access to its artifacts.
    The adapter is responsible for:
    - Parsing framework-specific files
    - Translating to unified data model
    - Providing framework terminology (glossary)

    Example:
        ```python
        adapter = get_adapter("bmad")
        work_units = adapter.parse_work_units(project_path)
        for unit in work_units:
            tasks = adapter.parse_tasks(unit.id)
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return framework identifier (e.g., 'bmad', 'native').

        This name is used for adapter registration and lookup.
        Must be unique across all registered adapters.

        Returns:
            Framework identifier string (lowercase, alphanumeric).
        """
        pass

    @property
    @abstractmethod
    def glossary(self) -> dict[str, str]:
        """Return terminology mapping for this framework.

        Provides display terminology for UI layer. Keys are unified
        concepts, values are framework-specific display names.

        Returns:
            Dictionary with keys: workUnit, task, checkpoint
        """
        pass

    @abstractmethod
    def parse_work_units(self, project_path: Path) -> list[WorkUnit]:
        """Parse and return all work units (epics/phases) from project.

        Scans project artifacts to discover and parse all high-level
        work groupings appropriate for this framework.

        Args:
            project_path: Root path of the project to scan.

        Returns:
            List of WorkUnit objects representing discovered work groups.

        Raises:
            adapters.exceptions.ParseError: If framework artifacts are malformed.
        """
        pass

    @abstractmethod
    def parse_tasks(self, work_unit_id: str) -> list[Task]:
        """Parse and return all tasks (stories/subtasks) for a work unit.

        Retrieves all child tasks belonging to the specified work unit.

        Args:
            work_unit_id: Identifier of the parent work unit.

        Returns:
            List of Task objects belonging to the work unit.

        Raises:
            adapters.exceptions.ParseError: If task artifacts are malformed.
            ValueError: If work_unit_id is not found.
        """
        pass

    @abstractmethod
    def get_status(self, project_path: Path) -> ProjectStatus:
        """Return current project status from framework artifacts.

        Aggregates status information from framework-specific files
        (e.g., sprint-status.yaml for BMAD, spec status for Native).

        Args:
            project_path: Root path of the project to analyze.

        Returns:
            ProjectStatus object with aggregated status information.
        """
        pass
