"""
Complexity-aware validation runner.

This module provides the unified entry point for running E2E validation
at the appropriate depth based on task complexity tier.

Story 6-3: Complexity-Aware Validation Depth
Acceptance Criteria #4: Validation time scales with tier
Acceptance Criteria #5: Logs depth choice and metrics
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .browser import BrowserMCPClient, E2EValidationResult
    from .models import E2ETestSuite

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Metrics from validation execution.

    Captures timing and results for logging and analysis.

    Attributes:
        tier: Complexity tier (simple/standard/complex)
        depth: Validation depth used (smoke/feature/full)
        test_count: Number of tests executed
        passed_count: Number of tests passed
        failed_count: Number of tests failed
        duration_seconds: Total execution time
        skipped_test_count: Number of tests skipped by filtering
        browser_count: Number of browsers tested (for cross-browser)
    """

    tier: str
    depth: str
    test_count: int
    passed_count: int
    failed_count: int
    duration_seconds: float
    skipped_test_count: int
    browser_count: int

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as fraction."""
        if self.test_count == 0:
            return 1.0  # No tests = passed
        return self.passed_count / self.test_count

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "tier": self.tier,
            "depth": self.depth,
            "test_count": self.test_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "pass_rate": self.pass_rate,
            "duration_seconds": self.duration_seconds,
            "skipped_test_count": self.skipped_test_count,
            "browser_count": self.browser_count,
        }


def log_validation_metrics(metrics: ValidationMetrics) -> None:
    """Log validation metrics for observability.

    Logs the depth choice, test counts, and timing information.

    Args:
        metrics: ValidationMetrics to log
    """
    logger.info(
        f"Validation completed: tier={metrics.tier} depth={metrics.depth} "
        f"tests={metrics.test_count} passed={metrics.passed_count} "
        f"failed={metrics.failed_count} duration={metrics.duration_seconds:.2f}s "
        f"browsers={metrics.browser_count}"
    )

    if metrics.skipped_test_count > 0:
        logger.info(
            f"Skipped {metrics.skipped_test_count} tests due to depth filtering"
        )

    if metrics.failed_count > 0:
        logger.warning(
            f"Validation FAILED: {metrics.failed_count}/{metrics.test_count} "
            f"tests failed ({(1-metrics.pass_rate)*100:.1f}% failure rate)"
        )
    else:
        logger.info(
            f"Validation PASSED: All {metrics.test_count} tests passed"
        )


async def run_complexity_aware_validation(
    tier: str,
    suite: "E2ETestSuite",
    project_path: Path,
    client_factory: Callable[[], "BrowserMCPClient"],
    changed_files: list[Path] | None = None,
) -> tuple["E2EValidationResult", ValidationMetrics]:
    """Run validation at appropriate depth for complexity tier.

    This is the main entry point for complexity-aware E2E validation.
    It automatically selects the correct validation strategy based on tier:
    - Simple: Smoke tests only (app loads, basic health)
    - Standard: Feature tests for changed areas + regression
    - Complex: Full suite with cross-browser testing

    Args:
        tier: Complexity tier (simple, standard, complex, or BMAD equivalents)
        suite: Complete E2E test suite
        project_path: Project root directory
        client_factory: Factory function to create browser clients
        changed_files: Optional list of changed files for feature filtering

    Returns:
        Tuple of (E2EValidationResult, ValidationMetrics)

    Examples:
        >>> result, metrics = await run_complexity_aware_validation(
        ...     tier="standard",
        ...     suite=suite,
        ...     project_path=Path("/project"),
        ...     client_factory=create_client,
        ...     changed_files=[Path("src/auth/login.ts")],
        ... )
        >>> print(f"Depth: {metrics.depth}, Passed: {metrics.passed_count}")
    """
    from .validation_depth import (
        ValidationDepth,
        get_validation_depth_for_tier,
        load_validation_config,
    )
    from .smoke_tests import run_smoke_tests, smoke_result_to_e2e_result
    from .feature_tests import (
        get_affected_features,
        filter_tests_by_features,
        load_feature_mappings,
    )
    from .full_suite import run_full_suite, FullSuiteConfig

    start_time = datetime.now()

    # Determine validation depth
    config = load_validation_config(project_path)
    depth = get_validation_depth_for_tier(tier, config)

    logger.info(f"Running {depth.value} validation for {tier} tier")

    original_test_count = len(suite.test_cases)
    skipped_count = 0
    browser_count = 1

    # Execute based on depth
    if depth == ValidationDepth.SMOKE:
        # Simple tier: smoke tests only
        client = client_factory()
        try:
            await client.connect()
            smoke_result = await run_smoke_tests(client, suite.app_url)
            result = smoke_result_to_e2e_result(smoke_result)
            # Smoke tests check 4 things, not the test suite
            skipped_count = original_test_count
        finally:
            await client.close()

    elif depth == ValidationDepth.FEATURE:
        # Standard tier: feature tests for changed areas
        feature_mappings = load_feature_mappings(project_path)

        if changed_files:
            affected_features = get_affected_features(changed_files, feature_mappings)
            filtered_suite = filter_tests_by_features(
                suite, affected_features, feature_mappings
            )
            skipped_count = original_test_count - len(filtered_suite.test_cases)
        else:
            # No changed files - run all tests
            filtered_suite = suite
            logger.info("No changed files specified, running all feature tests")

        client = client_factory()
        try:
            await client.connect()
            await client.launch_app(filtered_suite.app_url)

            # Run filtered tests
            from .validation import run_test_case
            from .browser import E2EValidationResult

            passed_count = 0
            failed_count = 0
            failures = []

            for test_case in filtered_suite.test_cases:
                test_result = await run_test_case(client, test_case)
                if test_result.get("passed", False):
                    passed_count += 1
                else:
                    failed_count += 1
                    failures.append(test_result)

            result = E2EValidationResult(
                passed=failed_count == 0,
                total_checks=len(filtered_suite.test_cases),
                passed_checks=passed_count,
                failed_checks=failed_count,
                failures=failures,
            )
        finally:
            await client.close()

    else:
        # Complex tier: full suite with cross-browser
        full_config = FullSuiteConfig(
            parallel_workers=4,
            cross_browser=True,
            browsers=["chromium", "firefox"],
        )
        browser_count = len(full_config.browsers)
        result = await run_full_suite(
            suite, project_path, client_factory, full_config
        )

    # Calculate metrics
    duration = (datetime.now() - start_time).total_seconds()

    metrics = ValidationMetrics(
        tier=tier,
        depth=depth.value,
        test_count=result.total_checks,
        passed_count=result.passed_checks,
        failed_count=result.failed_checks,
        duration_seconds=duration,
        skipped_test_count=skipped_count,
        browser_count=browser_count,
    )

    # Log metrics
    log_validation_metrics(metrics)

    return result, metrics
