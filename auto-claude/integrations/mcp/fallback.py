"""
MCP fallback behavior.

This module provides fallback handling when MCP is unavailable,
allowing builds to continue with reduced validation.

Story 6-4: MCP Graceful Degradation
Acceptance Criteria #3: Build can continue with reduced validation
Acceptance Criteria #4: MCP unavailable is logged, not treated as test failure
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .availability import MCPAvailability
    from .browser import E2EValidationResult

logger = logging.getLogger(__name__)


class FallbackMode(Enum):
    """Fallback behavior when MCP unavailable."""

    FAIL = "fail"  # Fail the build
    WARN = "warn"  # Warn and continue
    SKIP = "skip"  # Skip E2E silently
    REDUCED = "reduced"  # Run reduced validation


@dataclass
class FallbackConfig:
    """Fallback behavior configuration.

    Attributes:
        mode: How to handle MCP unavailable
        run_unit_tests: Run unit tests in reduced mode
        run_lint: Run linter in reduced mode
        mark_as_partial: Mark build as partial validation
    """

    mode: FallbackMode = FallbackMode.WARN
    run_unit_tests: bool = True
    run_lint: bool = True
    mark_as_partial: bool = True


@dataclass
class FallbackResult:
    """Result when using fallback validation.

    Attributes:
        used_fallback: Whether fallback was used
        reason: Why fallback was used
        validation_run: Type of validation run (full/reduced/none)
        unit_tests_passed: Unit test result if run
        lint_passed: Lint result if run
    """

    used_fallback: bool
    reason: str
    validation_run: str  # "full", "reduced", "none"
    unit_tests_passed: bool | None = None
    lint_passed: bool | None = None


def load_fallback_config(project_path: Path) -> FallbackConfig:
    """Load fallback config from project.

    Looks for `.auto-claude/mcp-fallback.json`.

    Args:
        project_path: Project root directory

    Returns:
        FallbackConfig instance

    Config file format:
        {
            "mode": "warn|fail|skip|reduced",
            "run_unit_tests": true,
            "run_lint": true,
            "mark_as_partial": true
        }
    """
    config_file = project_path / ".auto-claude" / "mcp-fallback.json"

    if not config_file.exists():
        logger.debug(f"No fallback config at {config_file}, using defaults")
        return FallbackConfig()

    try:
        with open(config_file) as f:
            data = json.load(f)

        return FallbackConfig(
            mode=FallbackMode(data.get("mode", "warn")),
            run_unit_tests=data.get("run_unit_tests", True),
            run_lint=data.get("run_lint", True),
            mark_as_partial=data.get("mark_as_partial", True),
        )
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Invalid fallback config: {e}, using defaults")
        return FallbackConfig()


async def handle_mcp_unavailable(
    availability: "MCPAvailability",
    project_path: Path,
    config: FallbackConfig | None = None,
) -> tuple["E2EValidationResult | None", FallbackResult]:
    """Handle MCP unavailable scenario.

    Applies the configured fallback behavior when MCP is not available.
    Logs the issue as a warning (not error) per AC #4.

    Args:
        availability: MCP availability status
        project_path: Project root
        config: Fallback configuration

    Returns:
        Tuple of (validation result, fallback result)
    """
    from .browser import E2EValidationResult
    from .errors import format_error_message

    config = config or load_fallback_config(project_path)

    # Log the issue as WARNING, not ERROR (AC #4)
    logger.warning(
        f"MCP unavailable: {availability.message}. "
        f"Using fallback mode: {config.mode.value}"
    )

    if config.mode == FallbackMode.FAIL:
        return None, FallbackResult(
            used_fallback=False,
            reason=availability.message,
            validation_run="none",
        )

    if config.mode == FallbackMode.SKIP:
        return E2EValidationResult(
            passed=True,  # Don't fail build
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            raw_output="E2E validation skipped - MCP unavailable",
        ), FallbackResult(
            used_fallback=True,
            reason=availability.message,
            validation_run="none",
        )

    # WARN or REDUCED mode
    fallback_result = FallbackResult(
        used_fallback=True,
        reason=availability.message,
        validation_run="reduced" if config.mode == FallbackMode.REDUCED else "none",
    )

    if config.mode == FallbackMode.REDUCED:
        # Run reduced validation
        if config.run_unit_tests:
            fallback_result.unit_tests_passed = await _run_unit_tests(project_path)

        if config.run_lint:
            fallback_result.lint_passed = await _run_lint(project_path)

    # Create result that doesn't fail the build (AC #4)
    validation_result = E2EValidationResult(
        passed=True,  # MCP unavailable is not a test failure
        total_checks=0,
        passed_checks=0,
        failed_checks=0,
        raw_output=format_error_message(availability.reason, include_remediation=False),
    )

    return validation_result, fallback_result


async def _run_unit_tests(project_path: Path) -> bool:
    """Run unit tests as fallback.

    Detects the test framework and runs tests.

    Args:
        project_path: Project root

    Returns:
        True if tests passed
    """
    import subprocess

    # Detect test framework and run
    if (project_path / "pytest.ini").exists() or (project_path / "tests").exists():
        result = subprocess.run(
            ["pytest", "-x", "-q"],
            cwd=project_path,
            capture_output=True,
        )
        return result.returncode == 0

    if (project_path / "package.json").exists():
        result = subprocess.run(
            ["npm", "test"],
            cwd=project_path,
            capture_output=True,
        )
        return result.returncode == 0

    return True  # No tests to run


async def _run_lint(project_path: Path) -> bool:
    """Run linter as fallback.

    Detects the linter and runs it.

    Args:
        project_path: Project root

    Returns:
        True if lint passed
    """
    import subprocess

    if (project_path / "package.json").exists():
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=project_path,
            capture_output=True,
        )
        return result.returncode == 0

    if (project_path / "pyproject.toml").exists():
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_path,
            capture_output=True,
        )
        return result.returncode == 0

    return True  # No linter configured
