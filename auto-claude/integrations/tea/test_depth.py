"""Test depth configuration for complexity-aware TEA integration."""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TestDepth(Enum):
    """Test depth levels."""
    NONE = "none"           # No TEA, basic validation only
    STANDARD = "standard"   # test-design + atdd
    FULL = "full"           # Full suite including trace + nfr


@dataclass
class TestDepthConfig:
    """Test depth configuration."""
    simple_depth: TestDepth = TestDepth.NONE
    standard_depth: TestDepth = TestDepth.STANDARD
    complex_depth: TestDepth = TestDepth.FULL
    # Override - forces specific depth regardless of tier
    force_depth: TestDepth | None = None


def get_test_depth_for_tier(tier: str, config: TestDepthConfig | None = None) -> TestDepth:
    """Get test depth for complexity tier.

    Args:
        tier: Complexity tier ('simple', 'standard', 'complex', etc.)
        config: Optional test depth configuration

    Returns:
        TestDepth for the tier
    """
    # Force override takes precedence
    if config and config.force_depth:
        logger.info(f"Using forced test depth: {config.force_depth.value}")
        return config.force_depth

    # Default tier mappings
    tier_map = {
        # Simple tiers - no TEA involvement
        "simple": TestDepth.NONE,
        "quick-flow": TestDepth.NONE,
        # Standard tiers - test-design + atdd
        "standard": TestDepth.STANDARD,
        "method": TestDepth.STANDARD,
        # Complex tiers - full TEA suite
        "complex": TestDepth.FULL,
        "enterprise": TestDepth.FULL,
    }

    # Apply config overrides if provided
    if config:
        tier_map.update({
            "simple": config.simple_depth,
            "quick-flow": config.simple_depth,
            "standard": config.standard_depth,
            "method": config.standard_depth,
            "complex": config.complex_depth,
            "enterprise": config.complex_depth,
        })

    depth = tier_map.get(tier.lower(), TestDepth.STANDARD)
    logger.info(f"Test depth for tier '{tier}': {depth.value}")
    return depth


def load_test_depth_config(project_path: Path) -> TestDepthConfig:
    """Load test depth config from project.

    Args:
        project_path: Project root path

    Returns:
        TestDepthConfig (defaults if no config found)
    """
    config_file = project_path / ".auto-claude" / "test-config.json"

    if not config_file.exists():
        logger.debug("No test depth config found, using defaults")
        return TestDepthConfig()

    try:
        with open(config_file) as f:
            data = json.load(f)

        config = TestDepthConfig(
            simple_depth=TestDepth(data.get("simple_depth", "none")),
            standard_depth=TestDepth(data.get("standard_depth", "standard")),
            complex_depth=TestDepth(data.get("complex_depth", "full")),
            force_depth=TestDepth(data["force_depth"]) if data.get("force_depth") else None,
        )
        logger.info(f"Loaded test depth config from {config_file}")
        return config

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse test depth config: {e}")
        return TestDepthConfig()


def save_test_depth_config(config: TestDepthConfig, project_path: Path) -> None:
    """Save test depth config to project.

    Args:
        config: Test depth configuration
        project_path: Project root path
    """
    config_dir = project_path / ".auto-claude"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "test-config.json"

    data = {
        "simple_depth": config.simple_depth.value,
        "standard_depth": config.standard_depth.value,
        "complex_depth": config.complex_depth.value,
    }

    if config.force_depth:
        data["force_depth"] = config.force_depth.value

    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved test depth config to {config_file}")
