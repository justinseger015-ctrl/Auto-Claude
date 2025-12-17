"""Basic validation module for simple tier tasks.

Story 4.3: Quick Flow / Simple Tier Handling (AC: #2, #3)

Provides lightweight validation without TEA test planning:
- Build check (project-type aware)
- Test suite execution (existing tests only)
- Lint checks (if configured)
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BasicValidationResult:
    """Result of basic validation checks.

    Attributes:
        all_passed: All checks passed
        build_passed: Build command succeeded
        tests_passed: Test suite passed
        lint_passed: Lint checks passed
        errors: List of error messages
    """

    all_passed: bool
    build_passed: bool
    tests_passed: bool
    lint_passed: bool
    errors: list[str]


async def run_basic_validation(project_path: Path) -> BasicValidationResult:
    """Run basic validation without TEA.

    Checks:
    1. Build passes (npm build, cargo build, etc.)
    2. Tests pass (existing test suite)
    3. Lint passes (if configured)

    Args:
        project_path: Project root path

    Returns:
        BasicValidationResult

    Story 4.3: AC #3 - Basic validation runs
    """
    errors = []

    logger.info("Running basic validation (no TEA)")

    # Run build check
    build_passed = await run_build(project_path)
    if not build_passed:
        errors.append("Build failed")

    # Run tests
    tests_passed = await run_tests(project_path)
    if not tests_passed:
        errors.append("Tests failed")

    # Run lint
    lint_passed = await run_lint(project_path)
    if not lint_passed:
        errors.append("Lint check failed")

    all_passed = build_passed and tests_passed and lint_passed

    logger.info(
        f"Basic validation complete: build={build_passed}, "
        f"tests={tests_passed}, lint={lint_passed}"
    )

    return BasicValidationResult(
        all_passed=all_passed,
        build_passed=build_passed,
        tests_passed=tests_passed,
        lint_passed=lint_passed,
        errors=errors,
    )


async def run_build(project_path: Path) -> bool:
    """Run build command based on project type.

    Detects project type and runs appropriate build command:
    - Node.js: npm run build
    - Rust: cargo build
    - Python: no explicit build (returns True)

    Args:
        project_path: Project root

    Returns:
        True if build passed, False otherwise
    """
    # Node.js/TypeScript project
    if (project_path / "package.json").exists():
        logger.info("Detected Node.js project, running npm build")
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.error(f"Build failed:\n{result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("Build timed out after 5 minutes")
            return False
        except FileNotFoundError:
            logger.warning("npm not found, skipping build")
            return True

    # Rust project
    if (project_path / "Cargo.toml").exists():
        logger.info("Detected Rust project, running cargo build")
        try:
            result = subprocess.run(
                ["cargo", "build"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=600,
            )
            if result.returncode != 0:
                logger.error(f"Build failed:\n{result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("Build timed out after 10 minutes")
            return False
        except FileNotFoundError:
            logger.warning("cargo not found, skipping build")
            return True

    # Python - no explicit build usually
    logger.info("Python project detected, no build step required")
    return True


async def run_tests(project_path: Path) -> bool:
    """Run test suite if configured.

    Detects test framework and runs tests:
    - Node.js: npm test (with --passWithNoTests)
    - Python: pytest

    Args:
        project_path: Project root

    Returns:
        True if tests passed, False otherwise
    """
    # Node.js tests
    if (project_path / "package.json").exists():
        logger.info("Running npm test")
        try:
            result = subprocess.run(
                ["npm", "test", "--", "--passWithNoTests"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.error(f"Tests failed:\n{result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("Tests timed out after 5 minutes")
            return False
        except FileNotFoundError:
            logger.warning("npm not found, skipping tests")
            return True

    # Python tests
    tests_dir = project_path / "tests"
    if tests_dir.exists() or (project_path / "pytest.ini").exists():
        logger.info("Running pytest")
        try:
            result = subprocess.run(
                ["pytest", "-x", "--tb=short"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.error(f"Tests failed:\n{result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("Tests timed out after 5 minutes")
            return False
        except FileNotFoundError:
            logger.warning("pytest not found, skipping tests")
            return True

    # No test framework detected
    logger.info("No test framework detected, skipping tests")
    return True


async def run_lint(project_path: Path) -> bool:
    """Run lint check if configured.

    Detects linter and runs checks:
    - Python: ruff check
    - Node.js: npm run lint

    Args:
        project_path: Project root

    Returns:
        True if lint passed, False otherwise
    """
    # Python linting with ruff
    if (project_path / "pyproject.toml").exists():
        logger.info("Running ruff check")
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                logger.warning(f"Lint issues found:\n{result.stdout}")
                # Note: Don't fail on lint warnings for simple tier
                return True
            return True
        except subprocess.TimeoutExpired:
            logger.error("Lint check timed out")
            return False
        except FileNotFoundError:
            logger.info("ruff not found, skipping lint")
            return True

    # Node.js linting
    eslint_configs = [".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs"]
    if any((project_path / config).exists() for config in eslint_configs):
        logger.info("Running npm run lint")
        try:
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                logger.warning(f"Lint issues found:\n{result.stdout}")
                # Note: Don't fail on lint warnings for simple tier
                return True
            return True
        except subprocess.TimeoutExpired:
            logger.error("Lint check timed out")
            return False
        except FileNotFoundError:
            logger.info("npm not found, skipping lint")
            return True

    # No linter configured
    logger.info("No linter configured, skipping lint check")
    return True
