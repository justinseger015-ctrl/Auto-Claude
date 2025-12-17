"""Test framework detection for TEA integration."""

import json
import logging
from pathlib import Path

from .models import TestFramework

logger = logging.getLogger(__name__)


def detect_test_framework(project_path: Path) -> TestFramework:
    """Detect test framework from project files.

    Args:
        project_path: Project root path

    Returns:
        Detected TestFramework enum value
    """
    # Python - pytest
    if (project_path / "pytest.ini").exists() or \
       (project_path / "pyproject.toml").exists() or \
       (project_path / "tests").exists():
        logger.info("Detected pytest framework")
        return TestFramework.PYTEST

    # JavaScript/TypeScript
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            # Prefer vitest over jest if both present
            if "vitest" in deps:
                logger.info("Detected vitest framework")
                return TestFramework.VITEST
            if "jest" in deps:
                logger.info("Detected jest framework")
                return TestFramework.JEST
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not parse package.json: {e}")

    # Go - Check for go.mod first (most reliable)
    if (project_path / "go.mod").exists():
        logger.info("Detected go test framework")
        return TestFramework.GO_TEST

    # Rust - Cargo
    if (project_path / "Cargo.toml").exists():
        logger.info("Detected cargo test framework")
        return TestFramework.CARGO_TEST

    # Go fallback - Check for test files in root only (avoid expensive glob)
    go_test_files = list(project_path.glob("*_test.go"))
    if go_test_files:
        logger.info("Detected go test framework")
        return TestFramework.GO_TEST

    logger.warning("Could not detect test framework")
    return TestFramework.UNKNOWN
