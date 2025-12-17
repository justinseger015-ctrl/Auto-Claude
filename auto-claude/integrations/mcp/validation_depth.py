"""
Validation depth configuration for complexity-aware E2E testing.

This module provides the mapping between task complexity tiers and
E2E validation depth levels, enabling appropriate test coverage
based on change scope.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationDepth(Enum):
    """E2E validation depth levels.

    Attributes:
        SMOKE: App loads, basic health check (Simple tier)
        FEATURE: Affected features + regression tests (Standard tier)
        FULL: Complete E2E suite, cross-browser/platform (Complex tier)
    """

    SMOKE = "smoke"
    FEATURE = "feature"
    FULL = "full"


@dataclass
class ValidationDepthConfig:
    """Validation depth configuration.

    Attributes:
        simple_depth: Validation depth for simple complexity tier
        standard_depth: Validation depth for standard complexity tier
        complex_depth: Validation depth for complex complexity tier
        force_depth: If set, overrides all tier mappings
        smoke_timeout: Timeout in seconds for smoke tests (default: 60)
        feature_timeout: Timeout in seconds for feature tests (default: 300)
        full_timeout: Timeout in seconds for full suite (default: 1800)
    """

    simple_depth: ValidationDepth = ValidationDepth.SMOKE
    standard_depth: ValidationDepth = ValidationDepth.FEATURE
    complex_depth: ValidationDepth = ValidationDepth.FULL
    force_depth: ValidationDepth | None = None
    smoke_timeout: int = 60  # seconds
    feature_timeout: int = 300  # seconds
    full_timeout: int = 1800  # seconds


# Tier mapping: Maps complexity tier names to validation depths
# Includes both Native track (simple, standard, complex) and
# BMAD track (quick-flow, method, enterprise) naming conventions
DEFAULT_TIER_MAP = {
    # Native track tiers
    "simple": ValidationDepth.SMOKE,
    "standard": ValidationDepth.FEATURE,
    "complex": ValidationDepth.FULL,
    # BMAD track tiers (equivalent mappings)
    "quick-flow": ValidationDepth.SMOKE,
    "method": ValidationDepth.FEATURE,
    "enterprise": ValidationDepth.FULL,
}


def get_validation_depth_for_tier(
    tier: str,
    config: ValidationDepthConfig | None = None,
) -> ValidationDepth:
    """Get validation depth for complexity tier.

    Maps a complexity tier name to the appropriate validation depth,
    taking into account any configuration overrides.

    Args:
        tier: Complexity tier name ('simple', 'standard', 'complex',
              or BMAD equivalents 'quick-flow', 'method', 'enterprise')
        config: Optional configuration with overrides

    Returns:
        ValidationDepth for the tier

    Examples:
        >>> get_validation_depth_for_tier("simple")
        ValidationDepth.SMOKE

        >>> config = ValidationDepthConfig(force_depth=ValidationDepth.FULL)
        >>> get_validation_depth_for_tier("simple", config)
        ValidationDepth.FULL
    """
    # Force depth overrides everything
    if config and config.force_depth:
        return config.force_depth

    # Build tier map with config overrides
    tier_map = DEFAULT_TIER_MAP.copy()

    if config:
        # Apply config overrides
        tier_map["simple"] = config.simple_depth
        tier_map["quick-flow"] = config.simple_depth
        tier_map["standard"] = config.standard_depth
        tier_map["method"] = config.standard_depth
        tier_map["complex"] = config.complex_depth
        tier_map["enterprise"] = config.complex_depth

    # Return mapped depth or default to FEATURE for unknown tiers
    return tier_map.get(tier.lower(), ValidationDepth.FEATURE)


def get_timeout_for_depth(
    depth: ValidationDepth,
    config: ValidationDepthConfig | None = None,
) -> int:
    """Get timeout in seconds for validation depth.

    Args:
        depth: Validation depth level
        config: Optional configuration with timeout overrides

    Returns:
        Timeout in seconds for the depth level
    """
    if config is None:
        config = ValidationDepthConfig()

    timeout_map = {
        ValidationDepth.SMOKE: config.smoke_timeout,
        ValidationDepth.FEATURE: config.feature_timeout,
        ValidationDepth.FULL: config.full_timeout,
    }

    return timeout_map.get(depth, config.feature_timeout)


def load_validation_config(project_path: Path) -> ValidationDepthConfig:
    """Load validation config from project.

    Looks for configuration in `.auto-claude/validation-config.json`.
    Returns default configuration if file doesn't exist.

    Args:
        project_path: Project root directory

    Returns:
        ValidationDepthConfig instance

    Config file format:
        {
            "simple_depth": "smoke|feature|full",
            "standard_depth": "smoke|feature|full",
            "complex_depth": "smoke|feature|full",
            "force_depth": "smoke|feature|full" (optional),
            "smoke_timeout": 60,
            "feature_timeout": 300,
            "full_timeout": 1800
        }
    """
    config_file = project_path / ".auto-claude" / "validation-config.json"

    if not config_file.exists():
        logger.debug(f"No validation config found at {config_file}, using defaults")
        return ValidationDepthConfig()

    try:
        with open(config_file) as f:
            data = json.load(f)

        return ValidationDepthConfig(
            simple_depth=ValidationDepth(data.get("simple_depth", "smoke")),
            standard_depth=ValidationDepth(data.get("standard_depth", "feature")),
            complex_depth=ValidationDepth(data.get("complex_depth", "full")),
            force_depth=(
                ValidationDepth(data["force_depth"])
                if data.get("force_depth")
                else None
            ),
            smoke_timeout=data.get("smoke_timeout", 60),
            feature_timeout=data.get("feature_timeout", 300),
            full_timeout=data.get("full_timeout", 1800),
        )
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {config_file}: {e}, using defaults")
        return ValidationDepthConfig()
    except ValueError as e:
        logger.warning(f"Invalid config value in {config_file}: {e}, using defaults")
        return ValidationDepthConfig()
