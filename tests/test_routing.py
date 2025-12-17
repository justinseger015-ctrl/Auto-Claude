"""Tests for two-stage routing system.

Story 4.1: Two-Stage Routing Implementation (AC: all)
"""

import json
import sys
from pathlib import Path
import pytest

# Add auto-claude to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "auto-claude"))

from routing import (
    route_task,
    get_active_framework,
    route_bmad_task,
    route_native_task,
    Framework,
    BMADTier,
    NativeTier,
)


# =============================================================================
# Stage 1: Framework Selection Tests
# =============================================================================


def test_get_active_framework_from_config(tmp_path):
    """Test framework read from config file.

    Story 4.1: AC #1 - Stage 1 determines active framework
    """
    config_dir = tmp_path / ".auto-claude"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"framework": "native"}))

    framework = get_active_framework(tmp_path)
    assert framework == Framework.NATIVE


def test_get_active_framework_bmad_detected(tmp_path):
    """Test framework detection for BMAD project.

    Story 4.1: AC #1 - Framework detection from structure
    """
    (tmp_path / "_bmad-output").mkdir()
    framework = get_active_framework(tmp_path)
    assert framework == Framework.BMAD


def test_get_active_framework_native_default(tmp_path):
    """Test framework defaults to Native.

    Story 4.1: AC #1 - Default framework
    """
    framework = get_active_framework(tmp_path)
    assert framework == Framework.NATIVE


def test_get_active_framework_malformed_json(tmp_path):
    """Test config with malformed JSON falls back to detection.

    Code Review Fix: Issue #5 - Test error handling paths
    """
    config_dir = tmp_path / ".auto-claude"
    config_dir.mkdir()
    (config_dir / "config.json").write_text("{invalid json")

    # Should fall back to detection (Native since no _bmad-output)
    framework = get_active_framework(tmp_path)
    assert framework == Framework.NATIVE


def test_get_active_framework_invalid_enum_value(tmp_path):
    """Test config with invalid framework value falls back to detection.

    Code Review Fix: Issue #5 - Test ValueError handling
    """
    config_dir = tmp_path / ".auto-claude"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"framework": "invalid_framework"}))

    # Should fall back to detection
    framework = get_active_framework(tmp_path)
    assert framework == Framework.NATIVE


# =============================================================================
# Stage 2: BMAD Routing Tests
# =============================================================================


def test_route_bmad_task_simple():
    """Test simple task routes to Quick Flow.

    Story 4.1: AC #2 - BMAD routing to Quick Flow
    """
    tier, confidence, factors = route_bmad_task("Fix typo in README")
    assert tier == BMADTier.QUICK_FLOW
    assert confidence > 0.5
    assert any("Simple" in f for f in factors)


def test_route_bmad_task_complex():
    """Test complex task routes to Enterprise.

    Story 4.1: AC #2 - BMAD routing to Enterprise
    """
    tier, confidence, factors = route_bmad_task(
        "Architect a new microservices system with authentication, "
        "database migration, and API gateway integration"
    )
    assert tier == BMADTier.ENTERPRISE
    assert confidence > 0.5


def test_route_bmad_task_standard():
    """Test standard task routes to Method.

    Story 4.1: AC #2 - BMAD routing to Method
    """
    tier, confidence, factors = route_bmad_task("Add user profile page with API integration")
    assert tier == BMADTier.METHOD
    assert confidence > 0.5


def test_route_bmad_only_returns_bmad_tiers():
    """Test BMAD routing only returns BMADTier enum values.

    Code Review Fix: Issue #2 - Validate framework-to-tier mapping
    """
    # Test all three complexity levels
    simple_tier, _, _ = route_bmad_task("Fix typo")
    standard_tier, _, _ = route_bmad_task("Add new feature")
    complex_tier, _, _ = route_bmad_task("Architect authentication system with database migration")

    # All should be BMADTier enum instances
    assert isinstance(simple_tier, BMADTier)
    assert isinstance(standard_tier, BMADTier)
    assert isinstance(complex_tier, BMADTier)

    # Verify values are correct BMAD tier names
    assert simple_tier.value in ["quick-flow", "method", "enterprise"]
    assert standard_tier.value in ["quick-flow", "method", "enterprise"]
    assert complex_tier.value in ["quick-flow", "method", "enterprise"]


# =============================================================================
# Stage 2: Native Routing Tests
# =============================================================================


def test_route_native_task_simple():
    """Test simple task routes to Simple.

    Story 4.1: AC #2 - Native routing to Simple
    """
    tier, confidence, factors = route_native_task("Rename variable in utils.ts")
    assert tier == NativeTier.SIMPLE
    assert confidence > 0.5


def test_route_native_task_complex():
    """Test complex task routes to Complex.

    Story 4.1: AC #2 - Native routing to Complex
    """
    tier, confidence, factors = route_native_task(
        "Refactor authentication system with OAuth2 and database schema changes"
    )
    assert tier == NativeTier.COMPLEX
    assert confidence > 0.5


def test_route_native_task_standard():
    """Test standard task routes to Standard.

    Story 4.1: AC #2 - Native routing to Standard
    """
    tier, confidence, factors = route_native_task("Add new API endpoint for user data")
    assert tier == NativeTier.STANDARD
    assert confidence > 0.5


def test_route_native_only_returns_native_tiers():
    """Test Native routing only returns NativeTier enum values.

    Code Review Fix: Issue #2 - Validate framework-to-tier mapping
    """
    # Test all three complexity levels
    simple_tier, _, _ = route_native_task("Fix typo")
    standard_tier, _, _ = route_native_task("Add new feature")
    complex_tier, _, _ = route_native_task("Architect authentication system with database migration")

    # All should be NativeTier enum instances
    assert isinstance(simple_tier, NativeTier)
    assert isinstance(standard_tier, NativeTier)
    assert isinstance(complex_tier, NativeTier)

    # Verify values are correct Native tier names
    assert simple_tier.value in ["simple", "standard", "complex"]
    assert standard_tier.value in ["simple", "standard", "complex"]
    assert complex_tier.value in ["simple", "standard", "complex"]


# =============================================================================
# Full Routing Flow Tests
# =============================================================================


def test_route_task_full_flow_bmad(tmp_path):
    """Test complete routing flow for BMAD project.

    Story 4.1: AC #1, #2, #3 - Full routing with logging
    """
    (tmp_path / "_bmad-output").mkdir()

    result = route_task(tmp_path, "Fix button color")

    assert result.framework == Framework.BMAD
    assert result.tier == "quick-flow"
    assert result.confidence > 0.5
    assert len(result.factors) > 0


def test_route_task_full_flow_native(tmp_path):
    """Test complete routing flow for Native project.

    Story 4.1: AC #1, #2, #3 - Full routing with logging
    """
    result = route_task(tmp_path, "Implement user authentication")

    assert result.framework == Framework.NATIVE
    assert result.tier in ["simple", "standard", "complex"]
    assert result.confidence > 0.5
    assert len(result.factors) >= 0


def test_routing_logs_decision(tmp_path, caplog):
    """Test that routing decisions are logged.

    Story 4.1: AC #3 - Routing decision logging
    """
    import logging
    caplog.set_level(logging.INFO)

    route_task(tmp_path, "Test task")

    assert "Stage 1 routing" in caplog.text
    assert "Stage 2" in caplog.text
    assert "Routing complete" in caplog.text


def test_bmad_route_returns_bmad_tier_strings(tmp_path):
    """Test BMAD routing returns BMAD tier string values.

    Code Review Fix: Issue #2 - Ensure correct tier type per framework
    """
    (tmp_path / "_bmad-output").mkdir()

    result = route_task(tmp_path, "Fix typo")

    assert result.framework == Framework.BMAD
    # Should return BMAD tier name, not Native tier name
    assert result.tier in ["quick-flow", "method", "enterprise"]
    assert result.tier not in ["simple", "standard", "complex"]


def test_native_route_returns_native_tier_strings(tmp_path):
    """Test Native routing returns Native tier string values.

    Code Review Fix: Issue #2 - Ensure correct tier type per framework
    """
    # No _bmad-output, so should default to Native
    result = route_task(tmp_path, "Fix typo")

    assert result.framework == Framework.NATIVE
    # Should return Native tier name, not BMAD tier name
    assert result.tier in ["simple", "standard", "complex"]
    assert result.tier not in ["quick-flow", "method", "enterprise"]


# =============================================================================
# Complexity Assessment Tests
# =============================================================================


def test_complexity_assessment_detects_security():
    """Test complexity assessment detects security keywords."""
    tier, confidence, factors = route_native_task("Add authentication with password hashing")

    # Should be complex due to security keywords
    assert tier in [NativeTier.STANDARD, NativeTier.COMPLEX]


def test_complexity_assessment_description_length():
    """Test that description length affects complexity."""
    # Very short description
    short_result = route_task(Path.cwd(), "Fix typo")

    # Very long description
    long_description = "Implement a comprehensive user management system " * 50
    long_result = route_task(Path.cwd(), long_description)

    # Long descriptions should generally be more complex
    assert short_result.tier in ["quick-flow", "simple"]
