"""
Tests for complexity-aware validation depth configuration.

Story 6-3: Complexity-Aware Validation Depth
Task 1: Tests for validation depth configuration
"""

import pytest
from pathlib import Path
import json
import sys

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")

from integrations.mcp.validation_depth import (
    ValidationDepth,
    ValidationDepthConfig,
    get_validation_depth_for_tier,
    get_timeout_for_depth,
    load_validation_config,
)


class TestValidationDepthEnum:
    """Test ValidationDepth enum values."""

    def test_smoke_depth_value(self):
        """Test SMOKE depth has correct value."""
        assert ValidationDepth.SMOKE.value == "smoke"

    def test_feature_depth_value(self):
        """Test FEATURE depth has correct value."""
        assert ValidationDepth.FEATURE.value == "feature"

    def test_full_depth_value(self):
        """Test FULL depth has correct value."""
        assert ValidationDepth.FULL.value == "full"


class TestValidationDepthConfig:
    """Test ValidationDepthConfig dataclass."""

    def test_default_config_values(self):
        """Test default configuration values."""
        config = ValidationDepthConfig()

        assert config.simple_depth == ValidationDepth.SMOKE
        assert config.standard_depth == ValidationDepth.FEATURE
        assert config.complex_depth == ValidationDepth.FULL
        assert config.force_depth is None
        assert config.smoke_timeout == 60
        assert config.feature_timeout == 300
        assert config.full_timeout == 1800

    def test_custom_config_values(self):
        """Test custom configuration values."""
        config = ValidationDepthConfig(
            simple_depth=ValidationDepth.FEATURE,
            standard_depth=ValidationDepth.FULL,
            complex_depth=ValidationDepth.FULL,
            force_depth=ValidationDepth.SMOKE,
            smoke_timeout=30,
            feature_timeout=120,
            full_timeout=900,
        )

        assert config.simple_depth == ValidationDepth.FEATURE
        assert config.standard_depth == ValidationDepth.FULL
        assert config.force_depth == ValidationDepth.SMOKE
        assert config.smoke_timeout == 30


class TestGetValidationDepthForTier:
    """Test tier to depth mapping function."""

    def test_simple_tier_gets_smoke_depth(self):
        """Test simple tier maps to SMOKE depth."""
        depth = get_validation_depth_for_tier("simple")
        assert depth == ValidationDepth.SMOKE

    def test_quickflow_tier_gets_smoke_depth(self):
        """Test quick-flow tier maps to SMOKE depth (BMAD equivalent)."""
        depth = get_validation_depth_for_tier("quick-flow")
        assert depth == ValidationDepth.SMOKE

    def test_standard_tier_gets_feature_depth(self):
        """Test standard tier maps to FEATURE depth."""
        depth = get_validation_depth_for_tier("standard")
        assert depth == ValidationDepth.FEATURE

    def test_method_tier_gets_feature_depth(self):
        """Test method tier maps to FEATURE depth (BMAD equivalent)."""
        depth = get_validation_depth_for_tier("method")
        assert depth == ValidationDepth.FEATURE

    def test_complex_tier_gets_full_depth(self):
        """Test complex tier maps to FULL depth."""
        depth = get_validation_depth_for_tier("complex")
        assert depth == ValidationDepth.FULL

    def test_enterprise_tier_gets_full_depth(self):
        """Test enterprise tier maps to FULL depth (BMAD equivalent)."""
        depth = get_validation_depth_for_tier("enterprise")
        assert depth == ValidationDepth.FULL

    def test_unknown_tier_gets_feature_depth(self):
        """Test unknown tier defaults to FEATURE depth."""
        depth = get_validation_depth_for_tier("unknown")
        assert depth == ValidationDepth.FEATURE

    def test_config_override_simple_depth(self):
        """Test config can override simple tier default."""
        config = ValidationDepthConfig(simple_depth=ValidationDepth.FEATURE)
        depth = get_validation_depth_for_tier("simple", config)
        assert depth == ValidationDepth.FEATURE

    def test_config_override_standard_depth(self):
        """Test config can override standard tier default."""
        config = ValidationDepthConfig(standard_depth=ValidationDepth.FULL)
        depth = get_validation_depth_for_tier("standard", config)
        assert depth == ValidationDepth.FULL

    def test_force_depth_overrides_all_tiers(self):
        """Test force_depth overrides all tier mappings."""
        config = ValidationDepthConfig(force_depth=ValidationDepth.FULL)

        assert get_validation_depth_for_tier("simple", config) == ValidationDepth.FULL
        assert get_validation_depth_for_tier("standard", config) == ValidationDepth.FULL
        assert get_validation_depth_for_tier("complex", config) == ValidationDepth.FULL


class TestLoadValidationConfig:
    """Test config loading from project file."""

    def test_load_missing_config_returns_defaults(self, tmp_path):
        """Test loading config when file doesn't exist returns defaults."""
        config = load_validation_config(tmp_path)

        assert config.simple_depth == ValidationDepth.SMOKE
        assert config.standard_depth == ValidationDepth.FEATURE
        assert config.complex_depth == ValidationDepth.FULL

    def test_load_config_from_file(self, tmp_path):
        """Test loading config from JSON file."""
        # Create config file
        config_dir = tmp_path / ".auto-claude"
        config_dir.mkdir()
        config_file = config_dir / "validation-config.json"
        config_file.write_text(json.dumps({
            "simple_depth": "feature",
            "standard_depth": "full",
            "smoke_timeout": 30,
            "feature_timeout": 120,
        }))

        config = load_validation_config(tmp_path)

        assert config.simple_depth == ValidationDepth.FEATURE
        assert config.standard_depth == ValidationDepth.FULL
        assert config.smoke_timeout == 30
        assert config.feature_timeout == 120

    def test_load_config_with_force_depth(self, tmp_path):
        """Test loading config with force_depth set."""
        config_dir = tmp_path / ".auto-claude"
        config_dir.mkdir()
        config_file = config_dir / "validation-config.json"
        config_file.write_text(json.dumps({
            "force_depth": "smoke",
        }))

        config = load_validation_config(tmp_path)

        assert config.force_depth == ValidationDepth.SMOKE


class TestGetTimeoutForDepth:
    """Test timeout retrieval for validation depths."""

    def test_smoke_timeout(self):
        """Test SMOKE depth returns smoke_timeout."""
        config = ValidationDepthConfig(smoke_timeout=45)
        timeout = get_timeout_for_depth(ValidationDepth.SMOKE, config)
        assert timeout == 45

    def test_feature_timeout(self):
        """Test FEATURE depth returns feature_timeout."""
        config = ValidationDepthConfig(feature_timeout=200)
        timeout = get_timeout_for_depth(ValidationDepth.FEATURE, config)
        assert timeout == 200

    def test_full_timeout(self):
        """Test FULL depth returns full_timeout."""
        config = ValidationDepthConfig(full_timeout=1000)
        timeout = get_timeout_for_depth(ValidationDepth.FULL, config)
        assert timeout == 1000
