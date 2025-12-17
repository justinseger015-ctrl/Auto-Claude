"""TEA orchestrator for complexity-aware test workflow execution."""

import logging
from pathlib import Path
from dataclasses import dataclass, field

from .test_depth import TestDepth, get_test_depth_for_tier, load_test_depth_config
from .test_design import invoke_tea_test_design
from .atdd import generate_atdd_tests
from .trace import generate_traceability_matrix, TraceabilityMatrix
from .nfr_assess import run_nfr_assessment, NFRAssessment
from .models import TestPlan

logger = logging.getLogger(__name__)


@dataclass
class TEAResult:
    """Result of TEA workflow execution."""
    depth: str
    tier: str
    test_plan: TestPlan | None = None
    test_files: list[str] = field(default_factory=list)
    traceability: TraceabilityMatrix | None = None
    nfr_assessment: NFRAssessment | None = None
    success: bool = True
    error: str | None = None


async def run_tea_for_tier(
    tier: str,
    story_path: Path,
    project_path: Path,
) -> TEAResult:
    """Run appropriate TEA workflows for complexity tier.

    Args:
        tier: Complexity tier ('simple', 'standard', 'complex', etc.)
        story_path: Path to story file
        project_path: Project root

    Returns:
        TEAResult with test artifacts
    """
    config = load_test_depth_config(project_path)
    depth = get_test_depth_for_tier(tier, config)

    logger.info(f"Running TEA with depth '{depth.value}' for tier '{tier}'")

    result = TEAResult(
        depth=depth.value,
        tier=tier,
    )

    try:
        # NONE depth - skip TEA entirely
        if depth == TestDepth.NONE:
            logger.info("Skipping TEA for simple tier - using basic validation only")
            return result

        # STANDARD and FULL depth - run test-design + atdd
        if depth in (TestDepth.STANDARD, TestDepth.FULL):
            # Generate test plan
            logger.info("Running TEA test-design workflow...")
            test_plan = await invoke_tea_test_design(story_path, project_path)
            result.test_plan = test_plan

            # Generate ATDD tests (failing tests for red phase)
            logger.info("Running TEA ATDD workflow - generating failing tests...")
            test_files = await generate_atdd_tests(test_plan, project_path)
            result.test_files = [str(f) for f in test_files]

            logger.info(
                f"TEA generated {len(test_plan.test_cases)} test cases "
                f"in {len(test_files)} files"
            )

        # FULL depth only - add trace + nfr assessment
        if depth == TestDepth.FULL:
            # Generate traceability matrix for quality gate
            logger.info("Running TEA trace workflow - generating traceability matrix...")
            traceability = await generate_traceability_matrix(
                story_path=story_path,
                test_plan=result.test_plan,
                project_path=project_path,
            )
            result.traceability = traceability

            # Run NFR assessment for release validation
            logger.info("Running TEA NFR assessment workflow...")
            nfr_result = await run_nfr_assessment(
                story_path=story_path,
                project_path=project_path,
            )
            result.nfr_assessment = nfr_result

            # Log quality gate status
            if traceability.quality_gate_passed:
                logger.info("✅ Traceability quality gate PASSED")
            else:
                logger.warning("❌ Traceability quality gate FAILED")

            if nfr_result.passed:
                logger.info("✅ NFR assessment PASSED")
            else:
                logger.warning(f"❌ NFR assessment FAILED: {len(nfr_result.issues)} issues")

    except Exception as e:
        logger.error(f"TEA workflow failed: {e}")
        result.success = False
        result.error = str(e)

    return result


def should_run_tea(tier: str, project_path: Path | None = None) -> bool:
    """Check if TEA should run for a given tier.

    Args:
        tier: Complexity tier
        project_path: Optional project path for config

    Returns:
        True if TEA should run
    """
    config = None
    if project_path:
        config = load_test_depth_config(project_path)

    depth = get_test_depth_for_tier(tier, config)
    return depth != TestDepth.NONE


def get_tea_workflows_for_tier(tier: str, project_path: Path | None = None) -> list[str]:
    """Get list of TEA workflows that will run for a tier.

    Args:
        tier: Complexity tier
        project_path: Optional project path for config

    Returns:
        List of workflow names
    """
    config = None
    if project_path:
        config = load_test_depth_config(project_path)

    depth = get_test_depth_for_tier(tier, config)

    if depth == TestDepth.NONE:
        return []
    elif depth == TestDepth.STANDARD:
        return ["test-design", "atdd"]
    elif depth == TestDepth.FULL:
        return ["test-design", "atdd", "trace", "nfr-assess"]

    return []


def format_tea_summary(result: TEAResult) -> str:
    """Format TEA result as human-readable summary.

    Args:
        result: TEA execution result

    Returns:
        Formatted summary string
    """
    lines = [
        "# TEA Execution Summary",
        "",
        f"**Tier:** {result.tier}",
        f"**Test Depth:** {result.depth}",
        f"**Status:** {'✅ Success' if result.success else '❌ Failed'}",
        "",
    ]

    if result.error:
        lines.append(f"**Error:** {result.error}")
        lines.append("")

    if result.test_plan:
        lines.append(f"**Test Cases Generated:** {len(result.test_plan.test_cases)}")
        lines.append(f"**Framework:** {result.test_plan.framework.value}")
        lines.append("")

    if result.test_files:
        lines.append("**Test Files:**")
        for f in result.test_files:
            lines.append(f"- {f}")
        lines.append("")

    if result.traceability:
        t = result.traceability
        lines.append(f"**Coverage:** {t.coverage_percentage:.1f}%")
        lines.append(f"**Quality Gate:** {'✅ PASSED' if t.quality_gate_passed else '❌ FAILED'}")
        if t.uncovered_requirements:
            lines.append(f"**Uncovered Requirements:** {len(t.uncovered_requirements)}")
        lines.append("")

    if result.nfr_assessment:
        n = result.nfr_assessment
        lines.append(f"**NFR Assessment:** {'✅ PASSED' if n.passed else '❌ FAILED'}")
        if n.issues:
            lines.append(f"**NFR Issues:** {len(n.issues)}")
        lines.append("")

    return "\n".join(lines)
