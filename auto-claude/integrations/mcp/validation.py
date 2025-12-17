"""
E2E validation runner for web applications.

This module provides the main entry point for running E2E validation test suites
using the Browser MCP client.
"""

import logging
from pathlib import Path
from datetime import datetime
from .browser import BrowserMCPClient, BrowserConfig, E2EValidationResult
from .models import E2ETestSuite, E2ETestCase, E2ETestStep

logger = logging.getLogger(__name__)


async def run_test_case(client: BrowserMCPClient, test_case: E2ETestCase) -> dict:
    """Run a single E2E test case.

    Args:
        client: Browser MCP client instance.
        test_case: Test case to execute.

    Returns:
        Dict with test result (passed, error message, interaction history, etc.).
    """
    logger.info(f"Running test case: {test_case.name}")

    if test_case.skip:
        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": True,
            "skipped": True,
            "error": None,
            "interaction_history": [],
        }

    interaction_history = []
    try:
        for i, step in enumerate(test_case.steps):
            interaction_history.append({
                "step": i + 1,
                "action": step.action,
                "selector": step.selector,
                "value": step.value,
                "status": "executing",
            })
            await execute_step(client, step)
            interaction_history[-1]["status"] = "completed"

        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": True,
            "error": None,
            "interaction_history": interaction_history,
        }
    except Exception as e:
        logger.error(f"Test case {test_case.name} failed: {e}")
        if interaction_history:
            interaction_history[-1]["status"] = "failed"
            interaction_history[-1]["error"] = str(e)

        # Capture DOM state on failure
        dom_snapshot = ""
        try:
            dom_snapshot = await client.get_dom_snapshot()
        except Exception:
            logger.warning("Failed to capture DOM snapshot on error")

        return {
            "id": test_case.id,
            "name": test_case.name,
            "passed": False,
            "error": str(e),
            "interaction_history": interaction_history,
            "dom_snapshot": dom_snapshot[:10000] if dom_snapshot else None,  # Limit size
        }


async def execute_step(client: BrowserMCPClient, step: E2ETestStep):
    """Execute a single test step.

    Args:
        client: Browser MCP client instance.
        step: Test step to execute.

    Raises:
        AssertionError: If assertion fails.
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
            raise ValueError("Navigate action requires URL in value")
        await client.launch_app(step.value)
    elif step.action == "wait":
        timeout = step.timeout or 1000
        await client.wait(timeout)
    elif step.action == "wait_for_selector":
        if not step.selector:
            raise ValueError("Wait for selector requires selector")
        await client.wait_for_selector(step.selector, step.timeout)
    elif step.action == "select":
        if not step.selector or not step.value:
            raise ValueError("Select action requires selector and value")
        await client.select(step.selector, step.value)
    elif step.action == "check":
        if not step.selector:
            raise ValueError("Check action requires selector")
        checked = step.value != "false" if step.value else True
        await client.check(step.selector, checked)
    elif step.action == "submit":
        if not step.selector:
            raise ValueError("Submit action requires selector")
        await client.submit(step.selector)
    elif step.action == "assert_visible":
        if not step.selector:
            raise ValueError("Assert visible requires selector")
        is_visible = await client.assert_visible(step.selector)
        if not is_visible:
            raise AssertionError(f"Element not visible: {step.selector}")
    elif step.action == "assert_text":
        if not step.selector or not step.expected:
            raise ValueError("Assert text requires selector and expected text")
        matches = await client.assert_text(step.selector, step.expected)
        if not matches:
            raise AssertionError(
                f"Element {step.selector} does not contain text: {step.expected}"
            )
    elif step.action == "assert_position":
        if not step.selector or not step.position:
            raise ValueError("Assert position requires selector and position")
        matches = await client.assert_position(step.selector, step.position)
        if not matches:
            raise AssertionError(
                f"Element {step.selector} position does not match expected: {step.position}"
            )
    else:
        raise ValueError(f"Unknown action type: {step.action}")


async def run_e2e_validation(
    test_suite: E2ETestSuite,
    project_path: Path,
    app_url: str | None = None,
) -> E2EValidationResult:
    """Run E2E validation test suite.

    Args:
        test_suite: Test suite to execute.
        project_path: Project root directory path.
        app_url: Application URL (uses test_suite.app_url if not provided).

    Returns:
        E2E validation result with pass/fail status and details.
    """
    url = app_url or test_suite.app_url
    config = BrowserConfig(screenshot_on_failure=True)
    client = BrowserMCPClient(config)

    failures = []
    screenshots = []
    passed_count = 0
    failed_count = 0
    start_time = datetime.now()

    try:
        # Connect to Browser MCP
        if not await client.connect():
            return E2EValidationResult(
                passed=False,
                total_checks=len(test_suite.test_cases),
                passed_checks=0,
                failed_checks=len(test_suite.test_cases),
                failures=[{"error": "Failed to connect to Browser MCP"}],
            )

        # Launch application
        if not await client.launch_app(url):
            return E2EValidationResult(
                passed=False,
                total_checks=len(test_suite.test_cases),
                passed_checks=0,
                failed_checks=len(test_suite.test_cases),
                failures=[{"error": f"Failed to launch app at {url}"}],
            )

        # Run each test case
        for test_case in test_suite.test_cases:
            result = await run_test_case(client, test_case)

            if result.get("skipped"):
                continue

            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1
                # Capture screenshot on failure
                if config.screenshot_on_failure:
                    screenshot_path = (
                        project_path
                        / ".auto-claude"
                        / "screenshots"
                        / f"{test_case.id}.png"
                    )
                    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                    await client.screenshot(screenshot_path)
                    screenshots.append(screenshot_path)
                    result["screenshot"] = str(screenshot_path)
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
