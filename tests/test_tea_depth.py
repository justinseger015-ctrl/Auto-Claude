"""Tests for TEA test depth configuration."""
import pytest
import json
from pathlib import Path


def test_test_depth_enum():
    """Test TestDepth enum values."""
    from integrations.tea import TestDepth

    assert TestDepth.NONE.value == "none"
    assert TestDepth.STANDARD.value == "standard"
    assert TestDepth.FULL.value == "full"


def test_simple_tier_gets_none_depth():
    """Test simple tier maps to NONE depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("simple")
    assert depth == TestDepth.NONE


def test_quick_flow_tier_gets_none_depth():
    """Test quick-flow tier maps to NONE depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("quick-flow")
    assert depth == TestDepth.NONE


def test_standard_tier_gets_standard_depth():
    """Test standard tier maps to STANDARD depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("standard")
    assert depth == TestDepth.STANDARD


def test_method_tier_gets_standard_depth():
    """Test method tier maps to STANDARD depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("method")
    assert depth == TestDepth.STANDARD


def test_complex_tier_gets_full_depth():
    """Test complex tier maps to FULL depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("complex")
    assert depth == TestDepth.FULL


def test_enterprise_tier_gets_full_depth():
    """Test enterprise tier maps to FULL depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("enterprise")
    assert depth == TestDepth.FULL


def test_config_override():
    """Test config can override tier defaults."""
    from integrations.tea import get_test_depth_for_tier, TestDepth, TestDepthConfig

    config = TestDepthConfig(
        simple_depth=TestDepth.STANDARD,  # Override simple to run tests
    )
    depth = get_test_depth_for_tier("simple", config)
    assert depth == TestDepth.STANDARD


def test_force_depth_overrides_all():
    """Test force_depth overrides tier mapping."""
    from integrations.tea import get_test_depth_for_tier, TestDepth, TestDepthConfig

    config = TestDepthConfig(force_depth=TestDepth.FULL)
    depth = get_test_depth_for_tier("simple", config)
    assert depth == TestDepth.FULL


def test_load_test_depth_config_default(tmp_path):
    """Test loading config returns defaults when file missing."""
    from integrations.tea import load_test_depth_config, TestDepth

    config = load_test_depth_config(tmp_path)

    assert config.simple_depth == TestDepth.NONE
    assert config.standard_depth == TestDepth.STANDARD
    assert config.complex_depth == TestDepth.FULL
    assert config.force_depth is None


def test_load_test_depth_config_from_file(tmp_path):
    """Test loading config from file."""
    from integrations.tea import load_test_depth_config, TestDepth

    # Create config file
    config_dir = tmp_path / ".auto-claude"
    config_dir.mkdir()
    config_file = config_dir / "test-config.json"
    config_file.write_text(json.dumps({
        "simple_depth": "standard",
        "standard_depth": "full",
        "complex_depth": "full",
    }))

    config = load_test_depth_config(tmp_path)

    assert config.simple_depth == TestDepth.STANDARD
    assert config.standard_depth == TestDepth.FULL


def test_save_test_depth_config(tmp_path):
    """Test saving config to file."""
    from integrations.tea import save_test_depth_config, load_test_depth_config, TestDepth, TestDepthConfig

    config = TestDepthConfig(
        simple_depth=TestDepth.STANDARD,
        standard_depth=TestDepth.FULL,
        complex_depth=TestDepth.FULL,
    )

    save_test_depth_config(config, tmp_path)

    # Verify file was created
    config_file = tmp_path / ".auto-claude" / "test-config.json"
    assert config_file.exists()

    # Verify can load it back
    loaded = load_test_depth_config(tmp_path)
    assert loaded.simple_depth == TestDepth.STANDARD


def test_unknown_tier_defaults_to_standard():
    """Test unknown tier defaults to STANDARD depth."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    depth = get_test_depth_for_tier("unknown-tier")
    assert depth == TestDepth.STANDARD


def test_case_insensitive_tier():
    """Test tier matching is case insensitive."""
    from integrations.tea import get_test_depth_for_tier, TestDepth

    assert get_test_depth_for_tier("SIMPLE") == TestDepth.NONE
    assert get_test_depth_for_tier("Simple") == TestDepth.NONE
    assert get_test_depth_for_tier("COMPLEX") == TestDepth.FULL
