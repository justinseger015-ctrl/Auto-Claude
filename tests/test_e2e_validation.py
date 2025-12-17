"""
Tests for E2E validation runner.

Tests the validation module that orchestrates E2E test execution.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Import from integrations package directly
import sys

sys.path.insert(0, "auto-claude")
from integrations.mcp.models import E2ETestSuite, E2ETestCase, E2ETestStep
from integrations.mcp.validation import run_e2e_validation, run_test_case, execute_step
from integrations.mcp.browser import BrowserMCPClient, E2EValidationResult


class TestE2EModels:
    """Test E2E data models."""

    def test_test_step_creation(self):
        """Test creating a test step."""
        step = E2ETestStep(action="click", selector="#submit")
        assert step.action == "click"
        assert step.selector == "#submit"
        assert step.value is None
        assert step.expected is None

    def test_test_case_creation(self):
        """Test creating a test case."""
        steps = [
            E2ETestStep(action="click", selector="#login"),
            E2ETestStep(action="type", selector="#username", value="testuser"),
        ]
        test_case = E2ETestCase(
            id="test-1", name="Login test", description="Test login flow", steps=steps
        )
        assert test_case.id == "test-1"
        assert test_case.name == "Login test"
        assert len(test_case.steps) == 2
        assert test_case.skip is False

    def test_test_suite_creation(self):
        """Test creating a test suite."""
        test_case = E2ETestCase(
            id="test-1",
            name="Test",
            description="Test",
            steps=[E2ETestStep(action="click", selector="#button")],
        )
        suite = E2ETestSuite(
            name="Login Suite",
            description="Test suite for login",
            app_url="http://localhost:3000",
            test_cases=[test_case],
        )
        assert suite.name == "Login Suite"
        assert suite.app_url == "http://localhost:3000"
        assert len(suite.test_cases) == 1


@pytest.mark.asyncio
class TestExecuteStep:
    """Test step execution."""

    async def test_execute_click_step(self):
        """Test executing a click step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="click", selector="#submit")

        with patch.object(client, "click", new_callable=AsyncMock) as mock_click:
            await execute_step(client, step)
            mock_click.assert_called_once_with("#submit")

    async def test_execute_type_step(self):
        """Test executing a type step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="type", selector="#username", value="testuser")

        with patch.object(client, "type_text", new_callable=AsyncMock) as mock_type:
            await execute_step(client, step)
            mock_type.assert_called_once_with("#username", "testuser")

    async def test_execute_navigate_step(self):
        """Test executing a navigate step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="navigate", value="http://localhost:3000")

        with patch.object(client, "launch_app", new_callable=AsyncMock) as mock_nav:
            await execute_step(client, step)
            mock_nav.assert_called_once_with("http://localhost:3000")

    async def test_execute_assert_visible_success(self):
        """Test executing assert_visible step (success)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="assert_visible", selector="#login-form")

        with patch.object(
            client, "assert_visible", new_callable=AsyncMock, return_value=True
        ):
            await execute_step(client, step)  # Should not raise

    async def test_execute_assert_visible_failure(self):
        """Test executing assert_visible step (failure)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="assert_visible", selector="#missing")

        with patch.object(
            client, "assert_visible", new_callable=AsyncMock, return_value=False
        ):
            with pytest.raises(AssertionError, match="Element not visible"):
                await execute_step(client, step)

    async def test_execute_assert_text_success(self):
        """Test executing assert_text step (success)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="assert_text", selector="#greeting", expected="Welcome")

        with patch.object(
            client, "assert_text", new_callable=AsyncMock, return_value=True
        ):
            await execute_step(client, step)  # Should not raise

    async def test_execute_assert_text_failure(self):
        """Test executing assert_text step (failure)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(
            action="assert_text", selector="#message", expected="Expected text"
        )

        with patch.object(
            client, "assert_text", new_callable=AsyncMock, return_value=False
        ):
            with pytest.raises(AssertionError, match="does not contain text"):
                await execute_step(client, step)

    async def test_execute_unknown_action(self):
        """Test executing unknown action raises error."""
        client = BrowserMCPClient()
        step = E2ETestStep(action="unknown", selector="#test")  # type: ignore

        with pytest.raises(ValueError, match="Unknown action type"):
            await execute_step(client, step)

    async def test_click_without_selector(self):
        """Test click action without selector raises error."""
        client = BrowserMCPClient()
        step = E2ETestStep(action="click")

        with pytest.raises(ValueError, match="Click action requires selector"):
            await execute_step(client, step)

    async def test_type_without_value(self):
        """Test type action without value raises error."""
        client = BrowserMCPClient()
        step = E2ETestStep(action="type", selector="#input")

        with pytest.raises(ValueError, match="Type action requires selector and value"):
            await execute_step(client, step)

    async def test_execute_wait_step(self):
        """Test executing a wait step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="wait", timeout=1000)

        with patch.object(client, "wait", new_callable=AsyncMock) as mock_wait:
            await execute_step(client, step)
            mock_wait.assert_called_once_with(1000)

    async def test_execute_wait_for_selector_step(self):
        """Test executing a wait_for_selector step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="wait_for_selector", selector="#loading", timeout=5000)

        with patch.object(client, "wait_for_selector", new_callable=AsyncMock) as mock:
            await execute_step(client, step)
            mock.assert_called_once_with("#loading", 5000)

    async def test_execute_select_step(self):
        """Test executing a select step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="select", selector="#country", value="US")

        with patch.object(client, "select", new_callable=AsyncMock) as mock:
            await execute_step(client, step)
            mock.assert_called_once_with("#country", "US")

    async def test_execute_check_step(self):
        """Test executing a check step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="check", selector="#agree")

        with patch.object(client, "check", new_callable=AsyncMock) as mock:
            await execute_step(client, step)
            mock.assert_called_once_with("#agree", True)

    async def test_execute_submit_step(self):
        """Test executing a submit step."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(action="submit", selector="#form")

        with patch.object(client, "submit", new_callable=AsyncMock) as mock:
            await execute_step(client, step)
            mock.assert_called_once_with("#form")

    async def test_execute_assert_position_success(self):
        """Test executing assert_position step (success)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(
            action="assert_position",
            selector="#button",
            position={"x": 100, "y": 200}
        )

        with patch.object(
            client, "assert_position", new_callable=AsyncMock, return_value=True
        ):
            await execute_step(client, step)  # Should not raise

    async def test_execute_assert_position_failure(self):
        """Test executing assert_position step (failure)."""
        client = BrowserMCPClient()
        client._connected = True
        step = E2ETestStep(
            action="assert_position",
            selector="#button",
            position={"x": 100, "y": 200}
        )

        with patch.object(
            client, "assert_position", new_callable=AsyncMock, return_value=False
        ):
            with pytest.raises(AssertionError, match="position does not match"):
                await execute_step(client, step)


@pytest.mark.asyncio
class TestRunTestCase:
    """Test running individual test cases."""

    async def test_run_successful_test_case(self):
        """Test running a test case that passes."""
        client = BrowserMCPClient()
        client._connected = True
        test_case = E2ETestCase(
            id="test-1",
            name="Success test",
            description="Test that succeeds",
            steps=[E2ETestStep(action="click", selector="#button")],
        )

        with patch.object(client, "click", new_callable=AsyncMock):
            result = await run_test_case(client, test_case)

        assert result["passed"] is True
        assert result["id"] == "test-1"
        assert result["name"] == "Success test"
        assert result["error"] is None

    async def test_run_failed_test_case(self):
        """Test running a test case that fails."""
        client = BrowserMCPClient()
        client._connected = True
        test_case = E2ETestCase(
            id="test-2",
            name="Failure test",
            description="Test that fails",
            steps=[E2ETestStep(action="click", selector="#missing")],
        )

        with patch.object(
            client, "click", new_callable=AsyncMock, side_effect=Exception("Element not found")
        ):
            result = await run_test_case(client, test_case)

        assert result["passed"] is False
        assert result["id"] == "test-2"
        assert "Element not found" in result["error"]

    async def test_run_skipped_test_case(self):
        """Test running a skipped test case."""
        client = BrowserMCPClient()
        test_case = E2ETestCase(
            id="test-3",
            name="Skipped test",
            description="Test that is skipped",
            steps=[],
            skip=True,
        )

        result = await run_test_case(client, test_case)

        assert result["passed"] is True
        assert result["skipped"] is True
        assert result["id"] == "test-3"


@pytest.mark.asyncio
class TestRunE2EValidation:
    """Test running full E2E validation."""

    async def test_validation_connection_failure(self, tmp_path):
        """Test validation handles connection failure."""
        test_suite = E2ETestSuite(
            name="Test Suite",
            description="Test",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(
                    id="test-1",
                    name="Test",
                    description="Test",
                    steps=[E2ETestStep(action="click", selector="#button")],
                )
            ],
        )

        with patch(
            "integrations.mcp.validation.BrowserMCPClient.connect",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await run_e2e_validation(test_suite, tmp_path)

        assert result.passed is False
        assert result.failed_checks == 1
        assert "Failed to connect" in result.failures[0]["error"]

    async def test_validation_app_launch_failure(self, tmp_path):
        """Test validation handles app launch failure."""
        test_suite = E2ETestSuite(
            name="Test Suite",
            description="Test",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(
                    id="test-1",
                    name="Test",
                    description="Test",
                    steps=[E2ETestStep(action="click", selector="#button")],
                )
            ],
        )

        with patch(
            "integrations.mcp.validation.BrowserMCPClient.connect",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.launch_app",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.close", new_callable=AsyncMock
        ):
            result = await run_e2e_validation(test_suite, tmp_path)

        assert result.passed is False
        assert "Failed to launch app" in result.failures[0]["error"]

    async def test_validation_successful(self, tmp_path):
        """Test successful E2E validation."""
        test_suite = E2ETestSuite(
            name="Test Suite",
            description="Test",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(
                    id="test-1",
                    name="Test 1",
                    description="First test",
                    steps=[E2ETestStep(action="click", selector="#button")],
                ),
                E2ETestCase(
                    id="test-2",
                    name="Test 2",
                    description="Second test",
                    steps=[E2ETestStep(action="type", selector="#input", value="test")],
                ),
            ],
        )

        with patch(
            "integrations.mcp.validation.BrowserMCPClient.connect",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.launch_app",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "integrations.mcp.validation.run_test_case",
            new_callable=AsyncMock,
            side_effect=[
                {"id": "test-1", "name": "Test 1", "passed": True, "error": None},
                {"id": "test-2", "name": "Test 2", "passed": True, "error": None},
            ],
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.close", new_callable=AsyncMock
        ):
            result = await run_e2e_validation(test_suite, tmp_path)

        assert result.passed is True
        assert result.total_checks == 2
        assert result.passed_checks == 2
        assert result.failed_checks == 0

    async def test_validation_with_failures_captures_screenshots(self, tmp_path):
        """Test validation captures screenshots on failure."""
        test_suite = E2ETestSuite(
            name="Test Suite",
            description="Test",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(
                    id="test-fail",
                    name="Failing test",
                    description="Test that fails",
                    steps=[E2ETestStep(action="click", selector="#button")],
                )
            ],
        )

        with patch(
            "integrations.mcp.validation.BrowserMCPClient.connect",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.launch_app",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "integrations.mcp.validation.run_test_case",
            new_callable=AsyncMock,
            return_value={"id": "test-fail", "name": "Failing test", "passed": False, "error": "Failed"},
        ), patch(
            "integrations.mcp.validation.BrowserMCPClient.screenshot",
            new_callable=AsyncMock,
        ) as mock_screenshot, patch(
            "integrations.mcp.validation.BrowserMCPClient.close", new_callable=AsyncMock
        ):
            result = await run_e2e_validation(test_suite, tmp_path)

        assert result.passed is False
        assert result.failed_checks == 1
        assert len(result.screenshots) == 1
        assert len(result.failures) == 1
        mock_screenshot.assert_called_once()
