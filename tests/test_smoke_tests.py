"""
Tests for smoke test suite implementation.

Story 6-3: Complexity-Aware Validation Depth
Task 2: Tests for smoke test implementation for Simple tier
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")


class TestSmokeTestResult:
    """Test SmokeTestResult dataclass."""

    def test_smoke_test_result_all_passed(self):
        """Test SmokeTestResult with all checks passed."""
        from integrations.mcp.smoke_tests import SmokeTestResult

        result = SmokeTestResult(
            app_loads=True,
            main_page_renders=True,
            no_console_errors=True,
            health_check_passed=True,
            errors=[],
        )

        assert result.app_loads is True
        assert result.main_page_renders is True
        assert result.no_console_errors is True
        assert result.health_check_passed is True
        assert len(result.errors) == 0

    def test_smoke_test_result_with_failures(self):
        """Test SmokeTestResult with failures."""
        from integrations.mcp.smoke_tests import SmokeTestResult

        result = SmokeTestResult(
            app_loads=True,
            main_page_renders=False,
            no_console_errors=False,
            health_check_passed=True,
            errors=["Main page did not render", "Console error: TypeError"],
        )

        assert result.app_loads is True
        assert result.main_page_renders is False
        assert result.no_console_errors is False
        assert len(result.errors) == 2


@pytest.mark.asyncio
class TestRunSmokeTests:
    """Test smoke test execution."""

    async def test_run_smoke_tests_all_pass(self):
        """Test smoke tests when all checks pass."""
        from integrations.mcp.smoke_tests import run_smoke_tests, SmokeTestResult
        from integrations.mcp.browser import BrowserMCPClient

        # Create mock client
        client = MagicMock(spec=BrowserMCPClient)
        client.launch_app = AsyncMock(return_value=True)
        client.assert_visible = AsyncMock(return_value=True)
        client._mcp_call = AsyncMock(return_value=None)

        result = await run_smoke_tests(client, "http://localhost:3000")

        assert isinstance(result, SmokeTestResult)
        assert result.app_loads is True
        assert result.main_page_renders is True

    async def test_run_smoke_tests_app_fails_to_load(self):
        """Test smoke tests when app fails to load."""
        from integrations.mcp.smoke_tests import run_smoke_tests, SmokeTestResult
        from integrations.mcp.browser import BrowserMCPClient

        # Create mock client that fails to launch
        client = MagicMock(spec=BrowserMCPClient)
        client.launch_app = AsyncMock(side_effect=Exception("Connection refused"))

        result = await run_smoke_tests(client, "http://localhost:3000")

        assert isinstance(result, SmokeTestResult)
        assert result.app_loads is False
        assert len(result.errors) > 0

    async def test_run_smoke_tests_main_page_not_visible(self):
        """Test smoke tests when main page doesn't render."""
        from integrations.mcp.smoke_tests import run_smoke_tests, SmokeTestResult
        from integrations.mcp.browser import BrowserMCPClient

        client = MagicMock(spec=BrowserMCPClient)
        client.launch_app = AsyncMock(return_value=True)
        client.assert_visible = AsyncMock(return_value=False)
        client._mcp_call = AsyncMock(return_value=None)

        result = await run_smoke_tests(client, "http://localhost:3000")

        assert result.app_loads is True
        assert result.main_page_renders is False

    async def test_run_smoke_tests_with_console_errors(self):
        """Test smoke tests when console has errors."""
        from integrations.mcp.smoke_tests import run_smoke_tests, SmokeTestResult
        from integrations.mcp.browser import BrowserMCPClient

        client = MagicMock(spec=BrowserMCPClient)
        client.launch_app = AsyncMock(return_value=True)
        client.assert_visible = AsyncMock(return_value=True)
        # Return console errors
        client._mcp_call = AsyncMock(side_effect=lambda method, params:
            ["TypeError: undefined is not a function", "ReferenceError: x is not defined"]
            if method == "getConsoleErrors" else None
        )

        result = await run_smoke_tests(client, "http://localhost:3000")

        assert result.app_loads is True
        assert result.no_console_errors is False


class TestSmokeResultConversion:
    """Test conversion of smoke test results to E2E validation results."""

    def test_convert_passing_smoke_result(self):
        """Test converting passing smoke result to E2E result."""
        from integrations.mcp.smoke_tests import (
            SmokeTestResult,
            smoke_result_to_e2e_result,
        )

        smoke = SmokeTestResult(
            app_loads=True,
            main_page_renders=True,
            no_console_errors=True,
            health_check_passed=True,
            errors=[],
        )

        e2e_result = smoke_result_to_e2e_result(smoke)

        assert e2e_result.passed is True
        assert e2e_result.total_checks == 4
        assert e2e_result.passed_checks == 4
        assert e2e_result.failed_checks == 0
        assert len(e2e_result.failures) == 0

    def test_convert_failing_smoke_result(self):
        """Test converting failing smoke result to E2E result."""
        from integrations.mcp.smoke_tests import (
            SmokeTestResult,
            smoke_result_to_e2e_result,
        )

        smoke = SmokeTestResult(
            app_loads=True,
            main_page_renders=False,
            no_console_errors=False,
            health_check_passed=True,
            errors=["Main page error", "Console error"],
        )

        e2e_result = smoke_result_to_e2e_result(smoke)

        assert e2e_result.passed is False
        assert e2e_result.total_checks == 4
        assert e2e_result.passed_checks == 2  # app_loads + health_check
        assert e2e_result.failed_checks == 2  # main_page + console
        assert len(e2e_result.failures) == 2

    def test_convert_complete_failure(self):
        """Test converting complete failure smoke result."""
        from integrations.mcp.smoke_tests import (
            SmokeTestResult,
            smoke_result_to_e2e_result,
        )

        smoke = SmokeTestResult(
            app_loads=False,
            main_page_renders=False,
            no_console_errors=False,
            health_check_passed=False,
            errors=["App failed to load"],
        )

        e2e_result = smoke_result_to_e2e_result(smoke)

        assert e2e_result.passed is False
        assert e2e_result.failed_checks == 4
        assert len(e2e_result.failures) >= 1  # At least app_loads failure
