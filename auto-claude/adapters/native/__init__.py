"""Native adapter package.

Provides parsing for Auto Claude Native artifacts including:
- Spec files (spec.md)
- Implementation plans (implementation_plan.json)
- Context and requirements JSON files

Story 2.4: Native Artifact Parser (AC: #1)
"""

from adapters.native.parser import (
    # Data models
    NativeSubtask,
    NativePhase,
    NativeSpec,
    ParseError,
    # Discovery
    find_specs,
    # Parsing
    parse_spec,
    # Conversion
    spec_to_work_unit,
    subtask_to_task,
)

__all__ = [
    # Data models
    "NativeSubtask",
    "NativePhase",
    "NativeSpec",
    "ParseError",
    # Discovery
    "find_specs",
    # Parsing
    "parse_spec",
    # Conversion
    "spec_to_work_unit",
    "subtask_to_task",
]
