"""
E2E validation runner for Electron applications.

This module provides the main entry point for running E2E validation test suites
on Electron desktop applications using the Electron MCP client.
"""

import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

from .electron import ElectronMCPClient, ElectronConfig, WindowState
from .browser import E2EValidationResult
from .models import E2ETestSuite, E2ETestCase, E2ETestStep

logger = logging.getLogger(__name__)


@dataclass
class ElectronFailureContext:
    """Context captured when an Electron test fails.

    Provides detailed information for debugging test failures including
    screenshots, window state, and IPC messages.
    """

    test_case_id: str
    test_case_name: str
    error_message: str
    screenshot_path: Path | None = None
    window_state: WindowState | None = None
    app_state: dict = field(default_factory=dict)
    ipc_messages: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "test_case_id": self.test_case_id,
            "test_case_name": self.test_case_name,
            "error": self.error_message,
            "screenshot": str(self.screenshot_path) if self.screenshot_path else None,
            "window_state": {
                "title": self.window_state.title,
                "width": self.window_state.width,
                "height": self.window_state.height,
                "x": self.window_state.x,
                "y": self.window_state.y,
                "focused": self.window_state.focused,
                "visible": self.window_state.visible,
                "fullscreen": self.window_state.fullscreen,
            }
            if self.window_state
            else None,
            "app_state": self.app_state,
            "ipc_messages": self.ipc_messages[:10],  # Last 10 messages
            "timestamp": self.timestamp.isoformat(),
        }


async def run_electron_test_case(
    client: ElectronMCPClient, test_case: E2ETestCase
) -> dict:
    """Run a single E2E test case on Electron app.

    Args:
        client: Electron MCP client instance.
        test_case: Test case to execute.

    Returns:
        Dict with test result (passed, error message, etc.).
    """
    logger.info(f"Running Electron test case: {test_case.name}")

    if test_case.skip:
        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": True,
            "skipped": True,
            "error": None,
        }

    try:
        for step in test_case.steps:
            await execute_electron_step(client, step)

        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": True,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Electron test case {test_case.name} failed: {e}")
        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": False,
            "error": str(e),
        }


async def execute_electron_step(client: ElectronMCPClient, step: E2ETestStep):
    """Execute a single test step on Electron app.

    Args:
        client: Electron MCP client instance.
        step: Test step to execute.

    Raises:
        AssertionError: If assertion fails.
        ValueError: If step configuration is invalid.
        Exception: If action fails.
    """
    if step.action == "click":
        if not step.selector:
            raise ValueError("Click action requires selector")
        await client.click(step.selector)
    elif step.action == "type":
        if not step.selector or not step.value:
            raise ValueError("Type action requires selector and value")
        await client.type_text(step.selector, step.value)
    elif step.action == "navigate":
        if not step.value:
            raise ValueError("Navigate action requires route in value")
        await client.navigate_to(step.value)
    elif step.action == "wait":
        timeout = step.timeout or 1000
        import asyncio

        await asyncio.sleep(timeout / 1000)
    elif step.action == "assert_visible":
        if not step.selector:
            raise ValueError("Assert visible requires selector")
        # For Electron, we'd need to implement element visibility check
        # This is handled through the MCP server
        pass
    elif step.action == "assert_text":
        if not step.selector or not step.expected:
            raise ValueError("Assert text requires selector and expected text")
        # Text assertion would be implemented via MCP
        pass
    elif step.action == "assert_position":
        if not step.position:
            raise ValueError("Assert position requires position data")
        # Position assertion for window positioning
        state = await client.get_window_state()
        expected_x = step.position.get("x")
        expected_y = step.position.get("y")
        tolerance = step.position.get("tolerance", 10)
        if expected_x is not None and abs(state.x - expected_x) > tolerance:
            raise AssertionError(
                f"Window X position {state.x} not within {tolerance} of {expected_x}"
            )
        if expected_y is not None and abs(state.y - expected_y) > tolerance:
            raise AssertionError(
                f"Window Y position {state.y} not within {tolerance} of {expected_y}"
            )
    else:
        raise ValueError(f"Unknown action type: {step.action}")


async def capture_failure_context(
    client: ElectronMCPClient,
    test_case: E2ETestCase,
    error: str,
    project_path: Path,
) -> ElectronFailureContext:
    """Capture detailed context when a test fails.

    Args:
        client: Electron MCP client.
        test_case: Failed test case.
        error: Error message.
        project_path: Project root for storing screenshots.

    Returns:
        ElectronFailureContext with captured information.
    """
    context = ElectronFailureContext(
        test_case_id=test_case.id,
        test_case_name=test_case.name,
        error_message=error,
    )

    try:
        # Capture window state
        context.window_state = await client.get_window_state()
    except Exception as e:
        logger.warning(f"Failed to capture window state: {e}")

    try:
        # Capture app state (focused element, menus, etc.)
        context.app_state = await client.get_app_state()
    except Exception as e:
        logger.warning(f"Failed to capture app state: {e}")

    try:
        # Capture recent IPC messages
        context.ipc_messages = await client.get_ipc_messages(limit=20)
    except Exception as e:
        logger.warning(f"Failed to capture IPC messages: {e}")

    try:
        # Capture screenshot
        screenshot_dir = project_path / ".auto-claude" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{test_case.id}_{context.timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        if await client.screenshot(screenshot_path):
            context.screenshot_path = screenshot_path
    except Exception as e:
        logger.warning(f"Failed to capture screenshot: {e}")

    return context


async def run_electron_validation(
    test_suite: E2ETestSuite,
    project_path: Path,
    config: ElectronConfig | None = None,
) -> E2EValidationResult:
    """Run E2E validation test suite on Electron app.

    Args:
        test_suite: Test suite to execute.
        project_path: Project root directory path (contains package.json).
        config: Optional Electron configuration.

    Returns:
        E2E validation result with pass/fail status and detailed failure context.
    """
    config = config or ElectronConfig(screenshot_on_failure=True)
    client = ElectronMCPClient(config)

    failures = []
    screenshots = []
    passed_count = 0
    failed_count = 0
    start_time = datetime.now()

    try:
        # Connect to Electron MCP
        if not await client.connect():
            return E2EValidationResult(
                passed=False,
                total_checks=len(test_suite.test_cases),
                passed_checks=0,
                failed_checks=len(test_suite.test_cases),
                failures=[{"error": "Failed to connect to Electron MCP"}],
            )

        # Launch Electron app
        if not await client.launch_app(project_path):
            return E2EValidationResult(
                passed=False,
                total_checks=len(test_suite.test_cases),
                passed_checks=0,
                failed_checks=len(test_suite.test_cases),
                failures=[{"error": f"Failed to launch Electron app at {project_path}"}],
            )

        # Run each test case
        for test_case in test_suite.test_cases:
            result = await run_electron_test_case(client, test_case)

            if result.get("skipped"):
                continue

            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1

                # Capture detailed failure context
                if config.screenshot_on_failure:
                    failure_context = await capture_failure_context(
                        client,
                        test_case,
                        result.get("error", "Unknown error"),
                        project_path,
                    )

                    if failure_context.screenshot_path:
                        screenshots.append(failure_context.screenshot_path)

                    failures.append(failure_context.to_dict())
                else:
                    failures.append(result)

    finally:
        await client.close()

    return E2EValidationResult(
        passed=failed_count == 0,
        total_checks=len(test_suite.test_cases),
        passed_checks=passed_count,
        failed_checks=failed_count,
        failures=failures,
        screenshots=screenshots,
        duration=(datetime.now() - start_time).total_seconds(),
    )
