"""TEA traceability matrix generation for complex tier."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .models import TestPlan

logger = logging.getLogger(__name__)


@dataclass
class TraceabilityMatrix:
    """Requirements to tests traceability."""
    requirement_coverage: dict[str, list[str]] = field(default_factory=dict)  # AC_id -> [test_ids]
    uncovered_requirements: list[str] = field(default_factory=list)
    tests_without_requirement: list[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    quality_gate_passed: bool = False


async def generate_traceability_matrix(
    story_path: Path,
    test_plan: TestPlan,
    project_path: Path,
) -> TraceabilityMatrix:
    """Generate traceability matrix for coverage verification.

    Args:
        story_path: Path to story file
        test_plan: Generated test plan
        project_path: Project root

    Returns:
        TraceabilityMatrix with coverage analysis
    """
    from .test_design import extract_acceptance_criteria

    # Extract ACs from story
    story_content = story_path.read_text()
    acceptance_criteria = extract_acceptance_criteria(story_content)

    ac_ids = {ac["id"] for ac in acceptance_criteria}
    covered_acs = set(test_plan.coverage_map.keys())
    test_ids = {tc.id for tc in test_plan.test_cases}

    # Find uncovered requirements
    uncovered = ac_ids - covered_acs

    # Find tests without AC mapping (orphan tests)
    tests_with_ac = set()
    for test_list in test_plan.coverage_map.values():
        tests_with_ac.update(test_list)
    orphan_tests = test_ids - tests_with_ac

    # Calculate coverage percentage
    coverage = len(covered_acs) / len(ac_ids) * 100 if ac_ids else 100.0

    # Determine quality gate status (100% coverage required for complex tier)
    quality_gate_passed = coverage >= 100.0 and len(uncovered) == 0

    matrix = TraceabilityMatrix(
        requirement_coverage=test_plan.coverage_map,
        uncovered_requirements=list(uncovered),
        tests_without_requirement=list(orphan_tests),
        coverage_percentage=coverage,
        quality_gate_passed=quality_gate_passed,
    )

    logger.info(
        f"Traceability matrix: {coverage:.1f}% coverage, "
        f"{len(uncovered)} uncovered, {len(orphan_tests)} orphan tests"
    )

    if not quality_gate_passed:
        logger.warning(f"Quality gate FAILED: {len(uncovered)} uncovered requirements")

    return matrix


def format_traceability_report(matrix: TraceabilityMatrix) -> str:
    """Format traceability matrix as human-readable report.

    Args:
        matrix: Traceability matrix

    Returns:
        Formatted report string
    """
    lines = [
        "# Traceability Matrix Report",
        "",
        f"## Coverage: {matrix.coverage_percentage:.1f}%",
        "",
        f"**Quality Gate:** {'✅ PASSED' if matrix.quality_gate_passed else '❌ FAILED'}",
        "",
    ]

    if matrix.requirement_coverage:
        lines.append("## Requirement Coverage")
        lines.append("")
        for ac_id, test_ids in matrix.requirement_coverage.items():
            lines.append(f"- **{ac_id}**: {', '.join(test_ids)}")
        lines.append("")

    if matrix.uncovered_requirements:
        lines.append("## ⚠️ Uncovered Requirements")
        lines.append("")
        for ac_id in matrix.uncovered_requirements:
            lines.append(f"- {ac_id} - NO TESTS")
        lines.append("")

    if matrix.tests_without_requirement:
        lines.append("## ℹ️ Tests Without Requirements")
        lines.append("")
        for test_id in matrix.tests_without_requirement:
            lines.append(f"- {test_id}")
        lines.append("")

    return "\n".join(lines)
