"""
Tests for feature test selection for Standard tier.

Story 6-3: Complexity-Aware Validation Depth
Task 3: Tests for feature test implementation for Standard tier
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
import sys

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")


class TestFeatureMapping:
    """Test FeatureMapping dataclass."""

    def test_feature_mapping_creation(self):
        """Test creating a feature mapping."""
        from integrations.mcp.feature_tests import FeatureMapping

        mapping = FeatureMapping(
            feature_name="auth",
            code_paths=["src/auth/*", "src/login/*"],
            test_ids=["auth-1", "auth-2", "auth-3"],
        )

        assert mapping.feature_name == "auth"
        assert len(mapping.code_paths) == 2
        assert len(mapping.test_ids) == 3


class TestGetAffectedFeatures:
    """Test feature detection from changed files."""

    def test_single_file_single_feature(self):
        """Test detecting feature from single changed file."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            get_affected_features,
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1", "auth-2"],
            ),
            FeatureMapping(
                feature_name="dashboard",
                code_paths=["src/dashboard/*"],
                test_ids=["dash-1"],
            ),
        ]

        changed_files = [Path("src/auth/login.ts")]
        affected = get_affected_features(changed_files, mappings)

        assert "auth" in affected
        assert "dashboard" not in affected

    def test_multiple_files_multiple_features(self):
        """Test detecting multiple features from multiple changed files."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            get_affected_features,
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1"],
            ),
            FeatureMapping(
                feature_name="dashboard",
                code_paths=["src/dashboard/*"],
                test_ids=["dash-1"],
            ),
            FeatureMapping(
                feature_name="settings",
                code_paths=["src/settings/*"],
                test_ids=["settings-1"],
            ),
        ]

        changed_files = [
            Path("src/auth/login.ts"),
            Path("src/dashboard/widgets.tsx"),
        ]
        affected = get_affected_features(changed_files, mappings)

        assert "auth" in affected
        assert "dashboard" in affected
        assert "settings" not in affected

    def test_no_matching_features(self):
        """Test when changed files don't match any feature."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            get_affected_features,
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1"],
            ),
        ]

        changed_files = [Path("src/utils/helpers.ts")]
        affected = get_affected_features(changed_files, mappings)

        assert len(affected) == 0

    def test_glob_pattern_matching(self):
        """Test that glob patterns work correctly."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            get_affected_features,
        )

        mappings = [
            FeatureMapping(
                feature_name="components",
                code_paths=["src/components/**/*"],
                test_ids=["comp-1"],
            ),
        ]

        # Should match nested files
        changed_files = [Path("src/components/buttons/Primary.tsx")]
        affected = get_affected_features(changed_files, mappings)

        assert "components" in affected


class TestFilterTestsByFeatures:
    """Test test filtering based on affected features."""

    def test_filter_to_single_feature(self):
        """Test filtering test suite to single affected feature."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            filter_tests_by_features,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        full_suite = E2ETestSuite(
            name="full",
            description="Full suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="auth-1", name="Login", description="Login test", steps=[]),
                E2ETestCase(id="auth-2", name="Logout", description="Logout test", steps=[]),
                E2ETestCase(id="dash-1", name="Dashboard", description="Dashboard test", steps=[]),
            ],
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1", "auth-2"],
            ),
        ]

        filtered = filter_tests_by_features(full_suite, ["auth"], mappings)

        assert len(filtered.test_cases) == 2
        assert all(tc.id.startswith("auth") for tc in filtered.test_cases)

    def test_filter_to_multiple_features(self):
        """Test filtering test suite to multiple affected features."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            filter_tests_by_features,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        full_suite = E2ETestSuite(
            name="full",
            description="Full suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="auth-1", name="Login", description="Login test", steps=[]),
                E2ETestCase(id="dash-1", name="Dashboard", description="Dashboard test", steps=[]),
                E2ETestCase(id="settings-1", name="Settings", description="Settings test", steps=[]),
            ],
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1"],
            ),
            FeatureMapping(
                feature_name="dashboard",
                code_paths=["src/dashboard/*"],
                test_ids=["dash-1"],
            ),
        ]

        filtered = filter_tests_by_features(full_suite, ["auth", "dashboard"], mappings)

        assert len(filtered.test_cases) == 2
        test_ids = [tc.id for tc in filtered.test_cases]
        assert "auth-1" in test_ids
        assert "dash-1" in test_ids

    def test_critical_tests_always_included(self):
        """Test that critical tests are always included."""
        from integrations.mcp.feature_tests import (
            FeatureMapping,
            filter_tests_by_features,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        full_suite = E2ETestSuite(
            name="full",
            description="Full suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="auth-1", name="Login", description="Login test", steps=[]),
                E2ETestCase(id="smoke-1", name="App Loads", description="Critical", steps=[], critical=True),
            ],
        )

        mappings = [
            FeatureMapping(
                feature_name="auth",
                code_paths=["src/auth/*"],
                test_ids=["auth-1"],
            ),
        ]

        filtered = filter_tests_by_features(full_suite, ["auth"], mappings)

        # Should include both auth test and critical smoke test
        assert len(filtered.test_cases) == 2
        test_ids = [tc.id for tc in filtered.test_cases]
        assert "auth-1" in test_ids
        assert "smoke-1" in test_ids


class TestLoadFeatureMappings:
    """Test loading feature mappings from project config."""

    def test_load_from_missing_file(self, tmp_path):
        """Test loading mappings when config file doesn't exist."""
        from integrations.mcp.feature_tests import load_feature_mappings

        mappings = load_feature_mappings(tmp_path)

        # Should return default mappings (may be empty or auto-generated)
        assert isinstance(mappings, list)

    def test_load_from_config_file(self, tmp_path):
        """Test loading mappings from JSON config file."""
        import json
        from integrations.mcp.feature_tests import load_feature_mappings

        # Create config file
        config_dir = tmp_path / ".auto-claude"
        config_dir.mkdir()
        config_file = config_dir / "feature-mappings.json"
        config_file.write_text(json.dumps({
            "mappings": [
                {
                    "feature": "auth",
                    "code_paths": ["src/auth/*"],
                    "test_ids": ["auth-1", "auth-2"],
                },
                {
                    "feature": "dashboard",
                    "code_paths": ["src/dashboard/*"],
                    "test_ids": ["dash-1"],
                },
            ]
        }))

        mappings = load_feature_mappings(tmp_path)

        assert len(mappings) == 2
        assert mappings[0].feature_name == "auth"
        assert mappings[1].feature_name == "dashboard"
