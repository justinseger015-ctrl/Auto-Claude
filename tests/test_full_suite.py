"""
Tests for full test suite implementation for Complex tier.

Story 6-3: Complexity-Aware Validation Depth
Task 4: Tests for full suite implementation for Complex tier
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import sys

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")


class TestFullSuiteConfig:
    """Test FullSuiteConfig dataclass."""

    def test_full_suite_config_defaults(self):
        """Test default full suite configuration."""
        from integrations.mcp.full_suite import FullSuiteConfig

        config = FullSuiteConfig()

        assert config.parallel_workers == 4
        assert config.cross_browser is True
        assert config.cross_platform is False  # Desktop only for Electron
        assert len(config.browsers) > 0
        assert "chromium" in config.browsers

    def test_full_suite_config_custom(self):
        """Test custom full suite configuration."""
        from integrations.mcp.full_suite import FullSuiteConfig

        config = FullSuiteConfig(
            parallel_workers=8,
            cross_browser=True,
            cross_platform=True,
            browsers=["chromium", "firefox", "webkit"],
        )

        assert config.parallel_workers == 8
        assert config.cross_browser is True
        assert config.cross_platform is True
        assert len(config.browsers) == 3


class TestFullSuiteRunner:
    """Test full suite execution."""

    def test_create_browser_matrix(self):
        """Test browser matrix creation for cross-browser testing."""
        from integrations.mcp.full_suite import create_browser_matrix

        matrix = create_browser_matrix(["chromium", "firefox", "webkit"])

        assert len(matrix) == 3
        assert "chromium" in matrix
        assert "firefox" in matrix
        assert "webkit" in matrix

    def test_expand_test_cases_for_browsers(self):
        """Test expanding test cases for multiple browsers."""
        from integrations.mcp.full_suite import expand_test_cases_for_browsers
        from integrations.mcp.models import E2ETestCase

        test_cases = [
            E2ETestCase(id="tc-1", name="Login", description="Login test", steps=[]),
            E2ETestCase(id="tc-2", name="Logout", description="Logout test", steps=[]),
        ]

        expanded = expand_test_cases_for_browsers(
            test_cases,
            ["chromium", "firefox"],
        )

        # 2 tests × 2 browsers = 4 expanded tests
        assert len(expanded) == 4

        # Check that browser is included in test ID
        test_ids = [tc.id for tc in expanded]
        assert "tc-1-chromium" in test_ids
        assert "tc-1-firefox" in test_ids
        assert "tc-2-chromium" in test_ids
        assert "tc-2-firefox" in test_ids


@pytest.mark.asyncio
class TestFullSuiteExecution:
    """Test full suite execution with parallel workers."""

    async def test_run_full_suite_basic(self):
        """Test running full suite with basic config."""
        from integrations.mcp.full_suite import run_full_suite, FullSuiteConfig
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        suite = E2ETestSuite(
            name="full",
            description="Full suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="tc-1", name="Test 1", description="Test", steps=[]),
            ],
        )

        # Create mock client factory
        def create_mock_client():
            client = MagicMock()
            client.connect = AsyncMock(return_value=True)
            client.launch_app = AsyncMock(return_value=True)
            client.close = AsyncMock()
            return client

        config = FullSuiteConfig(
            parallel_workers=2,
            cross_browser=False,
        )

        result = await run_full_suite(
            suite,
            Path("/tmp"),
            create_mock_client,
            config,
        )

        assert result.total_checks > 0

    async def test_run_full_suite_cross_browser(self):
        """Test running full suite with cross-browser testing."""
        from integrations.mcp.full_suite import run_full_suite, FullSuiteConfig
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        suite = E2ETestSuite(
            name="full",
            description="Full suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="tc-1", name="Test 1", description="Test", steps=[]),
            ],
        )

        # Create mock client factory
        def create_mock_client():
            client = MagicMock()
            client.connect = AsyncMock(return_value=True)
            client.launch_app = AsyncMock(return_value=True)
            client.close = AsyncMock()
            return client

        config = FullSuiteConfig(
            parallel_workers=2,
            cross_browser=True,
            browsers=["chromium", "firefox"],
        )

        result = await run_full_suite(
            suite,
            Path("/tmp"),
            create_mock_client,
            config,
        )

        # Cross-browser should expand test count
        assert result.total_checks >= 2  # 1 test × 2 browsers


class TestFullSuiteAggregation:
    """Test result aggregation across parallel workers."""

    def test_aggregate_empty_results(self):
        """Test aggregating empty results list."""
        from integrations.mcp.full_suite import aggregate_results
        from integrations.mcp.browser import E2EValidationResult

        aggregated = aggregate_results([])

        assert aggregated.passed is True  # No tests = passed
        assert aggregated.total_checks == 0

    def test_aggregate_all_passed(self):
        """Test aggregating all passed results."""
        from integrations.mcp.full_suite import aggregate_results
        from integrations.mcp.browser import E2EValidationResult

        results = [
            E2EValidationResult(
                passed=True, total_checks=5, passed_checks=5, failed_checks=0
            ),
            E2EValidationResult(
                passed=True, total_checks=3, passed_checks=3, failed_checks=0
            ),
        ]

        aggregated = aggregate_results(results)

        assert aggregated.passed is True
        assert aggregated.total_checks == 8
        assert aggregated.passed_checks == 8
        assert aggregated.failed_checks == 0

    def test_aggregate_with_failures(self):
        """Test aggregating results with some failures."""
        from integrations.mcp.full_suite import aggregate_results
        from integrations.mcp.browser import E2EValidationResult

        results = [
            E2EValidationResult(
                passed=True, total_checks=5, passed_checks=5, failed_checks=0
            ),
            E2EValidationResult(
                passed=False,
                total_checks=3,
                passed_checks=1,
                failed_checks=2,
                failures=[{"error": "Test failed"}],
            ),
        ]

        aggregated = aggregate_results(results)

        assert aggregated.passed is False
        assert aggregated.total_checks == 8
        assert aggregated.passed_checks == 6
        assert aggregated.failed_checks == 2
        assert len(aggregated.failures) == 1
