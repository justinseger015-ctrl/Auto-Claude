"""
Smoke test suite for Simple tier validation.

This module provides lightweight smoke tests that verify basic application
health without running full E2E test suites. Used for Simple complexity tier.

Story 6-3: Complexity-Aware Validation Depth
Acceptance Criteria #1: Simple tier runs smoke tests only
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .browser import BrowserMCPClient, E2EValidationResult
    from .electron import ElectronMCPClient

logger = logging.getLogger(__name__)


@dataclass
class SmokeTestResult:
    """Result of smoke test execution.

    Smoke tests verify:
    1. App loads without errors
    2. Main page renders
    3. No console errors
    4. Basic health check (if available)

    Attributes:
        app_loads: Whether the app successfully loaded
        main_page_renders: Whether the main page rendered expected elements
        no_console_errors: Whether there were no console errors
        health_check_passed: Whether health endpoint responded (if available)
        errors: List of error messages for failures
    """

    app_loads: bool
    main_page_renders: bool
    no_console_errors: bool
    health_check_passed: bool
    errors: list[str] = field(default_factory=list)


async def run_smoke_tests(
    client: "BrowserMCPClient | ElectronMCPClient",
    app_url_or_path: str | Path,
) -> SmokeTestResult:
    """Run smoke tests for app.

    Performs quick validation checks suitable for Simple tier:
    - App loads without crashing
    - Main page renders basic elements
    - No JavaScript errors in console
    - Health check endpoint responds (if available)

    Args:
        client: Browser or Electron MCP client
        app_url_or_path: URL for web apps or path for Electron apps

    Returns:
        SmokeTestResult with check outcomes
    """
    errors: list[str] = []

    # Test 1: App loads
    app_loads = False
    try:
        # Handle both string URLs and Path objects
        if isinstance(app_url_or_path, Path):
            app_loads = await client.launch_app(app_url_or_path)
        else:
            app_loads = await client.launch_app(str(app_url_or_path))
        if app_loads:
            logger.info("Smoke test: App loaded successfully")
        else:
            errors.append("App failed to load")
    except Exception as e:
        app_loads = False
        errors.append(f"App failed to load: {e}")
        logger.error(f"Smoke test: App load failed - {e}")

    # Test 2: Main page renders
    main_page_renders = False
    if app_loads:
        try:
            # Check for common root elements
            # Try multiple selectors that might indicate a rendered page
            for selector in ["body", "#root", "#app", "[data-testid='app']", "main"]:
                try:
                    visible = await client.assert_visible(selector)
                    if visible:
                        main_page_renders = True
                        logger.info(f"Smoke test: Main page rendered (found {selector})")
                        break
                except Exception:
                    continue

            if not main_page_renders:
                errors.append("Main page did not render expected elements")
                logger.warning("Smoke test: Main page render check failed")
        except Exception as e:
            errors.append(f"Main page render check failed: {e}")
            logger.error(f"Smoke test: Main page render error - {e}")

    # Test 3: No console errors
    no_console_errors = True
    try:
        console_errors = await client._mcp_call("getConsoleErrors", {})
        if console_errors:
            no_console_errors = False
            # Limit to first 5 errors to avoid spam
            for error in console_errors[:5]:
                errors.append(f"Console error: {error}")
            logger.warning(f"Smoke test: Found {len(console_errors)} console errors")
    except Exception:
        # Console check is optional - don't fail if not supported
        logger.debug("Smoke test: Console error check not available")
        pass

    # Test 4: Health check (optional)
    health_check_passed = True
    try:
        # Only check health for web apps with URL
        if isinstance(app_url_or_path, str) and app_url_or_path.startswith("http"):
            base_url = app_url_or_path.rstrip("/")
            health_response = await client._mcp_call("fetch", {
                "url": f"{base_url}/health"
            })
            if isinstance(health_response, dict):
                status = health_response.get("status", 0)
                health_check_passed = status == 200
                if health_check_passed:
                    logger.info("Smoke test: Health check passed")
                else:
                    logger.debug(f"Smoke test: Health check returned status {status}")
    except Exception:
        # Health check is optional - don't fail if not available
        logger.debug("Smoke test: Health check endpoint not available")
        pass

    return SmokeTestResult(
        app_loads=app_loads,
        main_page_renders=main_page_renders,
        no_console_errors=no_console_errors,
        health_check_passed=health_check_passed,
        errors=errors,
    )


def smoke_result_to_e2e_result(smoke: SmokeTestResult) -> "E2EValidationResult":
    """Convert smoke test result to E2E validation result.

    This allows smoke test results to be used in the same pipeline
    as full E2E validation results.

    Args:
        smoke: SmokeTestResult from smoke tests

    Returns:
        E2EValidationResult with converted data
    """
    from .browser import E2EValidationResult

    checks = [
        smoke.app_loads,
        smoke.main_page_renders,
        smoke.no_console_errors,
        smoke.health_check_passed,
    ]
    passed_count = sum(1 for c in checks if c)
    failed_count = len(checks) - passed_count

    # Build failures list for failed checks
    failures: list[dict] = []
    if not smoke.app_loads:
        failures.append({"check": "app_loads", "error": "App failed to load"})
    if not smoke.main_page_renders:
        failures.append({"check": "main_page_renders", "error": "Main page did not render"})
    if not smoke.no_console_errors:
        failures.append({"check": "console_errors", "error": "Console errors detected"})
    if not smoke.health_check_passed:
        failures.append({"check": "health_check", "error": "Health check failed"})

    return E2EValidationResult(
        passed=failed_count == 0,
        total_checks=len(checks),
        passed_checks=passed_count,
        failed_checks=failed_count,
        failures=failures,
    )
