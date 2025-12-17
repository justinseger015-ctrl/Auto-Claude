"""Two-stage task routing implementation.

Story 4.1: Two-Stage Routing Implementation (AC: all)

Implements ADR-004 two-stage routing architecture:
1. Stage 1: Determine active framework (BMAD/Native)
2. Stage 2: Route to complexity tier within framework
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Story 4.2: Import enhanced complexity assessment
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from spec.complexity import assess_task_complexity as enhanced_assess

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class Framework(Enum):
    """Planning framework options."""

    BMAD = "bmad"
    NATIVE = "native"


class BMADTier(Enum):
    """BMAD Method complexity tiers."""

    QUICK_FLOW = "quick-flow"
    METHOD = "method"
    ENTERPRISE = "enterprise"


class NativeTier(Enum):
    """Auto Claude Native complexity tiers."""

    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


@dataclass
class RoutingResult:
    """Result of task routing decision.

    Attributes:
        framework: Selected framework (BMAD or Native)
        tier: Complexity tier within framework
        confidence: Confidence score (0.0-1.0)
        factors: List of reasons for the decision
    """

    framework: Framework
    tier: str
    confidence: float
    factors: list[str]


# =============================================================================
# Stage 1: Framework Selection
# =============================================================================


def get_active_framework(project_path: Path) -> Framework:
    """Stage 1: Determine active framework from project config.

    Checks in order:
    1. Explicit config in .auto-claude/config.json
    2. Presence of _bmad-output directory
    3. Defaults to Native

    Args:
        project_path: Root path of the project

    Returns:
        Framework enum value

    Story 4.1: AC #1 - Stage 1 determines active framework
    """
    config_file = project_path / ".auto-claude" / "config.json"

    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            framework_str = config.get("framework", "bmad")
            framework = Framework(framework_str)
            logger.info(
                f"Stage 1 routing: framework={framework.value} (from config)"
            )
            return framework
        except json.JSONDecodeError as e:
            logger.warning(f"Config JSON parse error: {e}, falling back to detection")
        except ValueError as e:
            logger.warning(f"Invalid framework value in config: {e}, falling back to detection")
        except Exception as e:
            logger.warning(f"Config read error: {e}, falling back to detection")

    # Detect from project structure
    bmad_output = project_path / "_bmad-output"
    if bmad_output.exists():
        framework = Framework.BMAD
        logger.info(
            f"Stage 1 routing: framework={framework.value} (detected from _bmad-output)"
        )
    else:
        framework = Framework.NATIVE
        logger.info(
            f"Stage 1 routing: framework={framework.value} (default)"
        )

    return framework


# =============================================================================
# Complexity Assessment
# =============================================================================


def assess_complexity(
    task_description: str,
    project_path: Path | None = None,
    use_enhanced: bool = True
) -> tuple[str, float, list[str]]:
    """Assess task complexity based on description analysis.

    Story 4.2: Enhanced with scope and risk evaluation when project_path provided.
    Falls back to keyword-based assessment if enhanced assessment unavailable.

    Scoring algorithm (basic mode):
    - Simple keywords (fix, typo, rename): -2 points
    - Complex keywords (architect, refactor, migrate): +3 points
    - Critical components (api, database, auth): +2 points
    - Multiple components (3+ mentions): +2 points
    - Description length >500 chars: +1 point
    - Description length <100 chars: -1 point

    Tier thresholds:
    - score <= -1: simple (confidence 0.8)
    - score <= 2: standard (confidence 0.7)
    - score > 2: complex (confidence 0.75)

    Args:
        task_description: Natural language task description
        project_path: Optional project root for codebase analysis (Story 4.2)
        use_enhanced: Whether to use enhanced assessment with scope/risk eval

    Returns:
        Tuple of (complexity_level, confidence, factors)

    Story 4.1: Used by Stage 2 routing
    Story 4.2: AC #2 - Integrated with enhanced assessment
    """
    # Story 4.2: Try enhanced assessment first if enabled
    if use_enhanced:
        try:
            assessment = enhanced_assess(task_description, project_path)
            # Convert EnhancedComplexityAssessment to tuple format
            # Enhance factors with scope and risk scores
            enhanced_factors = assessment.factors.copy()
            enhanced_factors.append(f"Scope score: {assessment.scope_score}/10")
            enhanced_factors.append(f"Risk score: {assessment.risk_score}/10")
            if assessment.affected_files:
                enhanced_factors.append(f"Files detected: {len(assessment.affected_files)}")

            logger.info(
                f"Enhanced complexity assessment: tier={assessment.tier}, "
                f"scope={assessment.scope_score}, risk={assessment.risk_score}"
            )
            return (assessment.tier, assessment.confidence, enhanced_factors)
        except Exception as e:
            logger.warning(f"Enhanced assessment failed, falling back to basic: {e}")

    # Fall back to basic keyword-based assessment (Story 4.1 logic)
    logger.info("Using basic keyword-based complexity assessment")
    factors = []
    score = 0

    description_lower = task_description.lower()

    # Simple indicators (reduce complexity)
    simple_keywords = [
        "fix",
        "typo",
        "rename",
        "update text",
        "change label",
        "adjust",
    ]
    if any(word in description_lower for word in simple_keywords):
        factors.append("Simple fix indicator detected")
        score -= 2

    # Complex indicators (increase complexity)
    complex_keywords = [
        "architect",
        "refactor",
        "redesign",
        "migrate",
        "rewrite",
        "overhaul",
    ]
    if any(word in description_lower for word in complex_keywords):
        factors.append("Major change indicator detected")
        score += 3

    # System-critical components
    critical_keywords = [
        "api",
        "database",
        "security",
        "authentication",
        "auth",
        "migration",
    ]
    if any(word in description_lower for word in critical_keywords):
        factors.append("System-critical component involved")
        score += 2

    # Multiple components mentioned
    component_keywords = ["component", "module", "service", "endpoint", "system"]
    component_count = sum(
        1 for keyword in component_keywords if keyword in description_lower
    )
    if component_count >= 3:
        factors.append("Multiple system components involved")
        score += 2

    # Description length as proxy for complexity
    if len(task_description) > 500:
        factors.append("Detailed requirements suggest complexity")
        score += 1
    elif len(task_description) < 100:
        score -= 1

    # Determine tier based on score
    if score <= -1:
        return ("simple", 0.8, factors)
    elif score <= 2:
        return ("standard", 0.7, factors)
    else:
        return ("complex", 0.75, factors)


# =============================================================================
# Stage 2: Framework-Specific Routing
# =============================================================================


def route_bmad_task(
    task_description: str,
    project_path: Path | None = None
) -> tuple[BMADTier, float, list[str]]:
    """Stage 2: Route task to BMAD tier.

    Maps complexity assessment to BMAD tiers:
    - simple → Quick Flow
    - standard → Method
    - complex → Enterprise

    Args:
        task_description: Task description text
        project_path: Optional project root for enhanced assessment (Story 4.2)

    Returns:
        Tuple of (tier, confidence, factors)

    Story 4.1: AC #2 - BMAD routing to Quick Flow/Method/Enterprise
    Story 4.2: AC #2 - Uses enhanced assessment with project_path
    """
    complexity, confidence, factors = assess_complexity(task_description, project_path)

    tier_map = {
        "simple": BMADTier.QUICK_FLOW,
        "standard": BMADTier.METHOD,
        "complex": BMADTier.ENTERPRISE,
    }

    tier = tier_map[complexity]
    logger.info(
        f"Stage 2 BMAD routing: tier={tier.value}, "
        f"confidence={confidence:.2f}, complexity={complexity}"
    )

    return (tier, confidence, factors)


def route_native_task(
    task_description: str,
    project_path: Path | None = None
) -> tuple[NativeTier, float, list[str]]:
    """Stage 2: Route task to Native tier.

    Maps complexity assessment to Native tiers:
    - simple → Simple
    - standard → Standard
    - complex → Complex

    Args:
        task_description: Task description text
        project_path: Optional project root for enhanced assessment (Story 4.2)

    Returns:
        Tuple of (tier, confidence, factors)

    Story 4.1: AC #2 - Native routing to Simple/Standard/Complex
    Story 4.2: AC #2 - Uses enhanced assessment with project_path
    """
    complexity, confidence, factors = assess_complexity(task_description, project_path)

    tier_map = {
        "simple": NativeTier.SIMPLE,
        "standard": NativeTier.STANDARD,
        "complex": NativeTier.COMPLEX,
    }

    tier = tier_map[complexity]
    logger.info(
        f"Stage 2 Native routing: tier={tier.value}, "
        f"confidence={confidence:.2f}, complexity={complexity}"
    )

    return (tier, confidence, factors)


# =============================================================================
# Main Routing Function
# =============================================================================


def route_task(project_path: Path, task_description: str) -> RoutingResult:
    """Main routing function - combines Stage 1 and Stage 2.

    Full two-stage routing flow:
    1. Determine framework from project config/structure
    2. Assess complexity and route to appropriate tier

    Args:
        project_path: Root path of the project
        task_description: Task description text

    Returns:
        RoutingResult with framework, tier, and decision factors

    Story 4.1: AC #1, #2, #3 - Complete routing with logging
    Story 4.2: AC #2 - Passes project_path for enhanced complexity assessment
    """
    # Stage 1: Framework selection
    framework = get_active_framework(project_path)

    # Stage 2: Complexity routing within framework
    # Story 4.2: Pass project_path for codebase analysis
    if framework == Framework.BMAD:
        tier_enum, confidence, factors = route_bmad_task(task_description, project_path)
        tier = tier_enum.value
    else:
        tier_enum, confidence, factors = route_native_task(task_description, project_path)
        tier = tier_enum.value

    result = RoutingResult(
        framework=framework,
        tier=tier,
        confidence=confidence,
        factors=factors,
    )

    # Story 4.1: AC #3 - Routing decision logging
    logger.info(
        f"Routing complete: framework={result.framework.value}, "
        f"tier={result.tier}, confidence={result.confidence:.2f}, "
        f"factors={result.factors}"
    )

    return result
