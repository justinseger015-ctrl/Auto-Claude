"""Native artifact parser.

Parses Auto Claude Native spec.md and implementation_plan.json files.
Converts Native-specific data to unified models while maintaining
100% backward compatibility with existing specs.

Story 2.4: Native Artifact Parser (AC: #1, #2, #3, #4)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from models import UnifiedStatus, WorkUnit, Task, Checkpoint, map_native_status
from adapters.exceptions import ParseError  # Shared exception from adapters base

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class NativeSubtask:
    """Native subtask from implementation plan.

    Attributes:
        id: Subtask identifier (e.g., "1.1", "2.3").
        description: Human-readable subtask description.
        status: Native status string.
        files: List of file paths affected by this subtask.
    """

    id: str
    description: str
    status: str
    files: list[str] = field(default_factory=list)


@dataclass
class NativePhase:
    """Native phase from implementation plan.

    Attributes:
        id: Phase number (1, 2, etc.).
        name: Human-readable phase name.
        status: Native status string.
        subtasks: List of subtasks in this phase.
    """

    id: int
    name: str
    status: str
    subtasks: list[NativeSubtask] = field(default_factory=list)


@dataclass
class NativeSpec:
    """Parsed Native spec.

    Contains extracted information from spec.md and implementation_plan.json.

    Attributes:
        id: Spec ID (e.g., "001").
        name: Spec name from directory (e.g., "feature-name").
        description: Overview section from spec.md.
        status: Overall spec status.
        requirements: List of requirements from spec.md.
        acceptance_criteria: List of AC from spec.md.
        phases: List of phases from implementation plan.
        spec_dir: Path to spec directory.
        metadata: Additional parsed data.
    """

    id: str
    name: str
    description: str
    status: str
    requirements: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    phases: list[NativePhase] = field(default_factory=list)
    spec_dir: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Spec Discovery
# =============================================================================


def find_specs(project_path: Path) -> list[Path]:
    """Find all Native spec directories.

    Searches the `.auto-claude/specs/` directory for spec folders
    matching the pattern `NNN-name` (e.g., `001-feature-name`).

    Args:
        project_path: Root path of the project.

    Returns:
        List of spec directory paths, sorted by spec ID.
    """
    specs_dir = project_path / ".auto-claude" / "specs"
    if not specs_dir.exists():
        logger.debug("No .auto-claude/specs directory found")
        return []

    # Match pattern: NNN-name
    pattern = re.compile(r"^(\d{3})-.+$")
    spec_dirs = []

    for item in specs_dir.iterdir():
        if item.is_dir() and pattern.match(item.name):
            spec_dirs.append(item)

    logger.debug(f"Found {len(spec_dirs)} spec directories")
    return sorted(spec_dirs, key=lambda p: p.name)


# =============================================================================
# Spec Parsing
# =============================================================================


def parse_spec(spec_dir: Path) -> NativeSpec:
    """Parse a Native spec directory.

    Extracts data from spec.md and implementation_plan.json files.

    Args:
        spec_dir: Path to spec directory (e.g., .auto-claude/specs/001-feature/).

    Returns:
        Parsed NativeSpec object.

    Raises:
        ValueError: If directory name doesn't match expected pattern.
        ParseError: If required files are malformed.
    """
    # Extract ID and name from directory name
    dir_name = spec_dir.name
    match = re.match(r"^(\d{3})-(.+)$", dir_name)
    if not match:
        raise ValueError(f"Invalid spec directory name: {dir_name}")

    spec_id = match.group(1)
    spec_name = match.group(2)

    # Parse spec.md
    spec_md = spec_dir / "spec.md"
    description = ""
    requirements: list[str] = []
    acceptance_criteria: list[str] = []

    if spec_md.exists():
        try:
            content = spec_md.read_text()
            description = _extract_overview(content)
            requirements = _extract_requirements(content)
            acceptance_criteria = _extract_acceptance_criteria(content)
        except OSError as e:
            logger.warning(f"Could not read spec.md: {e}")

    # Parse implementation_plan.json
    plan_file = spec_dir / "implementation_plan.json"
    phases: list[NativePhase] = []
    status = "pending"
    metadata: dict[str, Any] = {}

    if plan_file.exists():
        try:
            with open(plan_file) as f:
                plan_data = json.load(f)
            status = plan_data.get("status", "pending")
            phases = _parse_phases(plan_data.get("phases", []))
            # Preserve additional metadata
            metadata = {
                k: v for k, v in plan_data.items()
                if k not in ("phases", "status")
            }
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in {plan_file}: {e}") from e
        except OSError as e:
            logger.warning(f"Could not read implementation_plan.json: {e}")

    return NativeSpec(
        id=spec_id,
        name=spec_name,
        description=description,
        status=status,
        requirements=requirements,
        acceptance_criteria=acceptance_criteria,
        phases=phases,
        spec_dir=spec_dir,
        metadata=metadata,
    )


def _extract_overview(content: str) -> str:
    """Extract overview section from spec.md.

    Args:
        content: Full spec.md content.

    Returns:
        Overview section content, stripped.
    """
    match = re.search(r"## Overview\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_requirements(content: str) -> list[str]:
    """Extract requirements from spec.md.

    Args:
        content: Full spec.md content.

    Returns:
        List of requirement strings.
    """
    match = re.search(r"## Requirements\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return []
    section = match.group(1)
    return re.findall(r"^\d+\.\s+(.+)$", section, re.MULTILINE)


def _extract_acceptance_criteria(content: str) -> list[str]:
    """Extract acceptance criteria from spec.md.

    Args:
        content: Full spec.md content.

    Returns:
        List of AC strings.
    """
    match = re.search(r"## Acceptance Criteria\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        return []
    section = match.group(1)
    return re.findall(r"^- \[[ x]\]\s+(.+)$", section, re.MULTILINE)


def _parse_phases(phases_data: list[dict[str, Any]]) -> list[NativePhase]:
    """Parse phases from implementation plan JSON.

    Args:
        phases_data: List of phase dicts from JSON.

    Returns:
        List of NativePhase objects.
    """
    phases = []
    for phase_data in phases_data:
        subtasks = [
            NativeSubtask(
                id=str(st.get("id", "")),
                description=st.get("description", ""),
                status=st.get("status", "pending"),
                files=st.get("files", []),
            )
            for st in phase_data.get("subtasks", [])
        ]
        phases.append(NativePhase(
            id=int(phase_data.get("id", 0)),
            name=phase_data.get("name", ""),
            status=phase_data.get("status", "pending"),
            subtasks=subtasks,
        ))
    return phases


# =============================================================================
# Spec to Unified Model Conversion
# =============================================================================


def spec_to_work_unit(spec: NativeSpec) -> WorkUnit:
    """Convert Native spec to unified WorkUnit.

    A Native spec becomes a WorkUnit (Phase in glossary terms), with
    subtasks as Tasks. Phases from the implementation plan provide
    grouping metadata.

    Args:
        spec: Parsed Native spec.

    Returns:
        Unified WorkUnit dataclass.
    """
    tasks = []
    for phase in spec.phases:
        for subtask in phase.subtasks:
            # Map status with graceful fallback
            try:
                unified_status = map_native_status(subtask.status)
            except ValueError:
                logger.warning(f"Unknown Native status '{subtask.status}' for subtask {subtask.id}, defaulting to PENDING")
                unified_status = UnifiedStatus.PENDING

            tasks.append(Task(
                id=subtask.id,
                title=subtask.description,
                description=f"Phase {phase.id}: {phase.name}",
                status=unified_status,
                files=subtask.files,
                checkpoints=[],
                metadata={
                    "phase_id": phase.id,
                    "phase_name": phase.name,
                    "phase_status": phase.status,
                },
            ))

    # Convert spec acceptance criteria to checkpoints
    checkpoints = [
        Checkpoint(id=f"ac-{i+1}", description=ac, completed=False)
        for i, ac in enumerate(spec.acceptance_criteria)
    ]

    # Map overall status with graceful fallback
    try:
        unified_status = map_native_status(spec.status)
    except ValueError:
        logger.warning(f"Unknown Native status '{spec.status}' for spec {spec.id}, defaulting to PENDING")
        unified_status = UnifiedStatus.PENDING

    return WorkUnit(
        id=spec.id,
        title=spec.name.replace("-", " ").title(),
        description=spec.description,
        status=unified_status,
        tasks=tasks,
        metadata={
            "requirements": spec.requirements,
            "acceptance_criteria": spec.acceptance_criteria,
            "checkpoints": [{"id": c.id, "description": c.description} for c in checkpoints],
            "spec_dir": str(spec.spec_dir) if spec.spec_dir else None,
            **spec.metadata,
        },
    )


def subtask_to_task(subtask: NativeSubtask, phase: NativePhase) -> Task:
    """Convert a single Native subtask to unified Task.

    Args:
        subtask: Native subtask to convert.
        phase: Parent phase for context.

    Returns:
        Unified Task dataclass.
    """
    # Map status with graceful fallback
    try:
        unified_status = map_native_status(subtask.status)
    except ValueError:
        logger.warning(f"Unknown Native status '{subtask.status}' for subtask {subtask.id}, defaulting to PENDING")
        unified_status = UnifiedStatus.PENDING

    return Task(
        id=subtask.id,
        title=subtask.description,
        description=f"Phase {phase.id}: {phase.name}",
        status=unified_status,
        files=subtask.files,
        checkpoints=[],
        metadata={
            "phase_id": phase.id,
            "phase_name": phase.name,
            "phase_status": phase.status,
        },
    )
