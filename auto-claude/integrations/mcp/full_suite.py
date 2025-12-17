"""
Full test suite execution for Complex tier validation.

This module provides comprehensive E2E testing with cross-browser/platform
support and parallel execution. Used for Complex complexity tier.

Story 6-3: Complexity-Aware Validation Depth
Acceptance Criteria #3: Complex tier runs full E2E suite with cross-browser
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .browser import BrowserMCPClient, E2EValidationResult
    from .models import E2ETestSuite, E2ETestCase

logger = logging.getLogger(__name__)


@dataclass
class FullSuiteConfig:
    """Configuration for full suite execution.

    Attributes:
        parallel_workers: Number of parallel test workers (default: 4)
        cross_browser: Whether to test across multiple browsers
        cross_platform: Whether to test across platforms (desktop)
        browsers: List of browsers to test (default: chromium only)
    """

    parallel_workers: int = 4
    cross_browser: bool = True
    cross_platform: bool = False  # Desktop-only for Electron apps
    browsers: list[str] = field(default_factory=lambda: ["chromium"])


def create_browser_matrix(browsers: list[str]) -> dict[str, dict]:
    """Create browser configuration matrix.

    Args:
        browsers: List of browser names

    Returns:
        Dict mapping browser name to configuration

    Examples:
        >>> create_browser_matrix(["chromium", "firefox"])
        {"chromium": {"headless": True, ...}, "firefox": {...}}
    """
    matrix = {}

    for browser in browsers:
        if browser == "chromium":
            matrix["chromium"] = {
                "headless": True,
                "channel": None,  # Use default Chromium
            }
        elif browser == "firefox":
            matrix["firefox"] = {
                "headless": True,
                "firefox_user_prefs": {},
            }
        elif browser == "webkit":
            matrix["webkit"] = {
                "headless": True,
            }
        else:
            logger.warning(f"Unknown browser: {browser}, using default config")
            matrix[browser] = {"headless": True}

    logger.info(f"Created browser matrix with {len(matrix)} browsers")
    return matrix


def expand_test_cases_for_browsers(
    test_cases: list["E2ETestCase"],
    browsers: list[str],
) -> list["E2ETestCase"]:
    """Expand test cases for cross-browser testing.

    Creates a copy of each test case for each browser, with unique IDs.

    Args:
        test_cases: Original test cases
        browsers: List of browsers to test

    Returns:
        Expanded test cases with browser-specific IDs

    Examples:
        >>> expand_test_cases_for_browsers([tc1], ["chromium", "firefox"])
        [tc1-chromium, tc1-firefox]
    """
    from .models import E2ETestCase

    expanded = []

    for tc in test_cases:
        for browser in browsers:
            # Create copy with browser-specific ID
            expanded.append(E2ETestCase(
                id=f"{tc.id}-{browser}",
                name=f"{tc.name} ({browser})",
                description=tc.description,
                steps=tc.steps.copy(),
                skip=tc.skip,
                critical=tc.critical,
            ))

    logger.info(
        f"Expanded {len(test_cases)} tests to {len(expanded)} "
        f"across {len(browsers)} browsers"
    )
    return expanded


async def run_full_suite(
    suite: "E2ETestSuite",
    project_path: Path,
    client_factory: Callable[[], "BrowserMCPClient"],
    config: FullSuiteConfig | None = None,
) -> "E2EValidationResult":
    """Run full test suite with parallel execution.

    Executes all tests in the suite across configured browsers
    using parallel workers for faster execution.

    Args:
        suite: Complete test suite
        project_path: Project root directory
        client_factory: Factory function to create browser clients
        config: Full suite configuration

    Returns:
        Aggregated E2E validation result
    """
    from .validation import run_test_case

    config = config or FullSuiteConfig()

    # Expand test cases for cross-browser if enabled
    if config.cross_browser and len(config.browsers) > 1:
        test_cases = expand_test_cases_for_browsers(
            suite.test_cases,
            config.browsers,
        )
    else:
        test_cases = suite.test_cases

    logger.info(
        f"Running full suite: {len(test_cases)} tests "
        f"with {config.parallel_workers} workers"
    )

    # Create worker pool
    semaphore = asyncio.Semaphore(config.parallel_workers)

    async def run_with_semaphore(test_case: "E2ETestCase") -> dict:
        async with semaphore:
            client = client_factory()
            try:
                await client.connect()
                await client.launch_app(suite.app_url)
                result = await run_test_case(client, test_case)
                return result
            except Exception as e:
                logger.error(f"Test {test_case.id} failed: {e}")
                return {
                    "id": test_case.id,
                    "name": test_case.name,
                    "passed": False,
                    "error": str(e),
                }
            finally:
                await client.close()

    # Run all tests in parallel (limited by semaphore)
    tasks = [run_with_semaphore(tc) for tc in test_cases]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert results to E2EValidationResult
    from .browser import E2EValidationResult

    passed_count = 0
    failed_count = 0
    failures = []

    for result in results:
        if isinstance(result, Exception):
            failed_count += 1
            failures.append({"error": str(result)})
        elif isinstance(result, dict):
            if result.get("passed", False):
                passed_count += 1
            else:
                failed_count += 1
                failures.append(result)

    return E2EValidationResult(
        passed=failed_count == 0,
        total_checks=len(results),
        passed_checks=passed_count,
        failed_checks=failed_count,
        failures=failures,
    )


def aggregate_results(
    results: list["E2EValidationResult"],
) -> "E2EValidationResult":
    """Aggregate multiple validation results into one.

    Combines results from parallel workers or cross-browser runs.

    Args:
        results: List of validation results to aggregate

    Returns:
        Combined E2EValidationResult
    """
    from .browser import E2EValidationResult

    if not results:
        return E2EValidationResult(
            passed=True,
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            failures=[],
        )

    total = sum(r.total_checks for r in results)
    passed = sum(r.passed_checks for r in results)
    failed = sum(r.failed_checks for r in results)
    all_failures: list[dict] = []

    for r in results:
        all_failures.extend(r.failures)

    logger.info(f"Aggregated {len(results)} results: {passed}/{total} passed")

    return E2EValidationResult(
        passed=failed == 0,
        total_checks=total,
        passed_checks=passed,
        failed_checks=failed,
        failures=all_failures,
    )
