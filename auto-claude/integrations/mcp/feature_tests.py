"""
Feature test selection for Standard tier validation.

This module provides feature-based test filtering that runs only tests
related to changed code. Used for Standard complexity tier.

Story 6-3: Complexity-Aware Validation Depth
Acceptance Criteria #2: Standard tier runs feature tests + regression
"""

import fnmatch
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import E2ETestSuite

logger = logging.getLogger(__name__)


@dataclass
class FeatureMapping:
    """Maps code paths to test suites.

    Used to determine which tests should run when specific files change.

    Attributes:
        feature_name: Name of the feature (e.g., "auth", "dashboard")
        code_paths: Glob patterns for code files (e.g., ["src/auth/*"])
        test_ids: Test case IDs that verify this feature
    """

    feature_name: str
    code_paths: list[str]
    test_ids: list[str]


def get_affected_features(
    changed_files: list[Path],
    feature_mappings: list[FeatureMapping],
) -> list[str]:
    """Get features affected by changed files.

    Analyzes which code files were modified and determines which
    features those files belong to.

    Args:
        changed_files: List of changed file paths
        feature_mappings: Feature to code mappings

    Returns:
        List of affected feature names (deduplicated)

    Examples:
        >>> mappings = [FeatureMapping("auth", ["src/auth/*"], ["auth-1"])]
        >>> get_affected_features([Path("src/auth/login.ts")], mappings)
        ["auth"]
    """
    affected: set[str] = set()

    for file in changed_files:
        file_str = str(file)
        for mapping in feature_mappings:
            for pattern in mapping.code_paths:
                if fnmatch.fnmatch(file_str, pattern):
                    affected.add(mapping.feature_name)
                    logger.debug(
                        f"File {file_str} matches pattern {pattern} "
                        f"-> feature {mapping.feature_name}"
                    )
                    break  # Found match for this file, move to next mapping

    logger.info(f"Identified {len(affected)} affected features from {len(changed_files)} files")
    return list(affected)


def filter_tests_by_features(
    full_suite: "E2ETestSuite",
    affected_features: list[str],
    feature_mappings: list[FeatureMapping],
) -> "E2ETestSuite":
    """Filter test suite to only affected features.

    Reduces the test suite to only tests that verify affected features,
    plus any critical regression tests.

    Args:
        full_suite: Complete test suite
        affected_features: Features affected by code changes
        feature_mappings: Feature to test mappings

    Returns:
        Filtered test suite with only relevant tests

    Examples:
        >>> filtered = filter_tests_by_features(suite, ["auth"], mappings)
        >>> # Returns suite with only auth-related tests + critical tests
    """
    from .models import E2ETestSuite

    # Collect test IDs for affected features
    relevant_test_ids: set[str] = set()
    for feature in affected_features:
        for mapping in feature_mappings:
            if mapping.feature_name == feature:
                relevant_test_ids.update(mapping.test_ids)
                logger.debug(f"Feature {feature} adds tests: {mapping.test_ids}")

    # Filter test cases
    filtered_cases = [
        tc for tc in full_suite.test_cases
        if tc.id in relevant_test_ids
    ]

    # Always include critical regression tests
    critical_tests = [
        tc for tc in full_suite.test_cases
        if getattr(tc, 'critical', False) and tc.id not in relevant_test_ids
    ]
    filtered_cases.extend(critical_tests)

    logger.info(
        f"Filtered to {len(filtered_cases)} tests from {len(full_suite.test_cases)} total "
        f"({len(critical_tests)} critical tests included)"
    )

    return E2ETestSuite(
        name=f"{full_suite.name}-filtered",
        description=f"Filtered suite for features: {', '.join(affected_features)}",
        app_url=full_suite.app_url,
        test_cases=filtered_cases,
    )


def load_feature_mappings(project_path: Path) -> list[FeatureMapping]:
    """Load feature mappings from project config.

    Looks for configuration in `.auto-claude/feature-mappings.json`.
    Falls back to auto-generated mappings based on directory structure.

    Args:
        project_path: Project root directory

    Returns:
        List of FeatureMapping objects

    Config file format:
        {
            "mappings": [
                {
                    "feature": "auth",
                    "code_paths": ["src/auth/*", "src/login/*"],
                    "test_ids": ["auth-1", "auth-2"]
                }
            ]
        }
    """
    config_file = project_path / ".auto-claude" / "feature-mappings.json"

    if not config_file.exists():
        logger.debug(f"No feature mappings found at {config_file}, generating defaults")
        return _generate_default_mappings(project_path)

    try:
        with open(config_file) as f:
            data = json.load(f)

        mappings = [
            FeatureMapping(
                feature_name=m["feature"],
                code_paths=m["code_paths"],
                test_ids=m.get("test_ids", []),
            )
            for m in data.get("mappings", [])
        ]
        logger.info(f"Loaded {len(mappings)} feature mappings from config")
        return mappings

    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {config_file}: {e}, generating defaults")
        return _generate_default_mappings(project_path)


def _generate_default_mappings(project_path: Path) -> list[FeatureMapping]:
    """Generate default feature mappings from directory structure.

    Creates mappings based on common directory patterns:
    - src/{feature}/* -> feature
    - app/{feature}/* -> feature
    - components/{feature}/* -> feature

    Args:
        project_path: Project root directory

    Returns:
        Auto-generated feature mappings
    """
    mappings: list[FeatureMapping] = []

    # Common source directories
    src_dirs = [
        project_path / "src",
        project_path / "app",
        project_path / "lib",
    ]

    for src_dir in src_dirs:
        if src_dir.exists() and src_dir.is_dir():
            for feature_dir in src_dir.iterdir():
                if feature_dir.is_dir() and not feature_dir.name.startswith(("_", ".")):
                    mappings.append(FeatureMapping(
                        feature_name=feature_dir.name,
                        code_paths=[f"{src_dir.name}/{feature_dir.name}/**/*"],
                        test_ids=[],  # Will match by convention
                    ))
                    logger.debug(f"Generated default mapping for feature: {feature_dir.name}")

    return mappings


def get_changed_files_from_git(project_path: Path, base_branch: str = "main") -> list[Path]:
    """Get list of changed files from git diff.

    Compares current branch to base branch to find changed files.

    Args:
        project_path: Project root directory (git repo)
        base_branch: Base branch to compare against (default: main)

    Returns:
        List of changed file paths relative to project root
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_branch],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,
        )

        changed_files = [
            Path(f.strip())
            for f in result.stdout.strip().split("\n")
            if f.strip()
        ]
        logger.info(f"Found {len(changed_files)} changed files from git diff")
        return changed_files

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git diff failed: {e}")
        return []
    except FileNotFoundError:
        logger.warning("Git not found")
        return []
