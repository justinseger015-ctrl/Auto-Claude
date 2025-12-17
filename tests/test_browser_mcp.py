"""
Tests for Browser MCP integration.

Following TDD red-green-refactor:
1. RED: Write failing tests
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve structure while keeping tests green
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Import from integrations package directly (tests run from auto-claude/ directory)
import sys
sys.path.insert(0, "auto-claude")
from integrations.mcp.browser import (
    BrowserMCPClient,
    BrowserConfig,
    E2EValidationResult,
)


class TestBrowserConfig:
    """Test browser configuration."""

    def test_default_config(self):
        """Test default browser configuration values."""
        config = BrowserConfig()
        assert config.headless is True
        assert config.viewport_width == 1280
        assert config.viewport_height == 720
        assert config.timeout == 30000
        assert config.screenshot_on_failure is True

    def test_custom_config(self):
        """Test custom browser configuration."""
        config = BrowserConfig(
            headless=False,
            viewport_width=1920,
            viewport_height=1080,
            timeout=60000,
            screenshot_on_failure=False,
        )
        assert config.headless is False
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.timeout == 60000
        assert config.screenshot_on_failure is False


class TestE2EValidationResult:
    """Test E2E validation result dataclass."""

    def test_validation_result_defaults(self):
        """Test E2E validation result default values."""
        result = E2EValidationResult(
            passed=True, total_checks=5, passed_checks=5, failed_checks=0
        )
        assert result.passed is True
        assert result.total_checks == 5
        assert result.passed_checks == 5
        assert result.failed_checks == 0
        assert result.failures == []
        assert result.screenshots == []
        assert result.duration == 0.0
        assert result.raw_output == ""


@pytest.mark.asyncio
class TestBrowserMCPClient:
    """Test Browser MCP client functionality."""

    async def test_browser_client_initialization(self):
        """Test browser client initializes with config."""
        config = BrowserConfig(headless=False)
        client = BrowserMCPClient(config)
        assert client.config == config
        assert client._connected is False

    async def test_browser_client_default_config(self):
        """Test browser client uses default config when none provided."""
        client = BrowserMCPClient()
        assert client.config is not None
        assert isinstance(client.config, BrowserConfig)
        assert client._connected is False

    async def test_browser_client_connect_success(self):
        """Test browser client connection success."""
        client = BrowserMCPClient()
        with patch.object(client, "_mcp_call", new_callable=AsyncMock):
            result = await client.connect()
            assert result is True
            assert client._connected is True

    async def test_browser_client_connect_failure(self):
        """Test browser client connection failure."""
        client = BrowserMCPClient()
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock, side_effect=Exception("Connection failed")
        ):
            result = await client.connect()
            assert result is False
            assert client._connected is False

    async def test_browser_client_launch_app_success(self):
        """Test app launch success."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            result = await client.launch_app("http://localhost:3000")
            assert result is True
            mock.assert_called_once_with("navigate", {"url": "http://localhost:3000"})

    async def test_browser_client_launch_app_not_connected(self):
        """Test app launch fails when not connected."""
        client = BrowserMCPClient()
        with pytest.raises(RuntimeError, match="Not connected to Browser MCP"):
            await client.launch_app("http://localhost:3000")

    async def test_browser_client_click(self):
        """Test click action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.click("#submit-button")
            assert result is True
            mock.assert_called_once_with("click", {"selector": "#submit-button"})

    async def test_browser_client_type_text(self):
        """Test type text action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.type_text("#username", "testuser")
            assert result is True
            mock.assert_called_once_with(
                "type", {"selector": "#username", "text": "testuser"}
            )

    async def test_browser_client_assert_visible_true(self):
        """Test element visibility assertion (visible)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock, return_value={"visible": True}
        ) as mock:
            result = await client.assert_visible("#login-form")
            assert result is True
            mock.assert_called_once_with("isVisible", {"selector": "#login-form"})

    async def test_browser_client_assert_visible_false(self):
        """Test element visibility assertion (not visible)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock, return_value={"visible": False}
        ) as mock:
            result = await client.assert_visible("#hidden-element")
            assert result is False
            mock.assert_called_once_with("isVisible", {"selector": "#hidden-element"})

    async def test_browser_client_assert_text_match(self):
        """Test text assertion (matching)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock, return_value={"text": "Welcome back!"}
        ) as mock:
            result = await client.assert_text("#greeting", "Welcome")
            assert result is True
            mock.assert_called_once_with("getText", {"selector": "#greeting"})

    async def test_browser_client_assert_text_no_match(self):
        """Test text assertion (not matching)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock, return_value={"text": "Hello world"}
        ) as mock:
            result = await client.assert_text("#message", "Goodbye")
            assert result is False
            mock.assert_called_once_with("getText", {"selector": "#message"})

    async def test_browser_client_screenshot(self, tmp_path):
        """Test screenshot capture."""
        client = BrowserMCPClient()
        client._connected = True
        screenshot_path = tmp_path / "test.png"
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.screenshot(screenshot_path)
            assert result is True
            mock.assert_called_once_with("screenshot", {"path": str(screenshot_path)})

    async def test_browser_client_close(self):
        """Test browser connection close."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            await client.close()
            assert client._connected is False
            mock.assert_called_once_with("close", {})

    async def test_browser_client_close_when_not_connected(self):
        """Test closing when not connected does nothing."""
        client = BrowserMCPClient()
        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            await client.close()
            mock.assert_not_called()

    async def test_browser_client_wait(self):
        """Test wait action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.wait(1000)
            assert result is True
            mock.assert_called_once_with("wait", {"timeout": 1000})

    async def test_browser_client_wait_for_selector(self):
        """Test wait for selector action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.wait_for_selector("#loading", timeout=5000)
            assert result is True
            mock.assert_called_once_with("waitForSelector", {"selector": "#loading", "timeout": 5000})

    async def test_browser_client_select(self):
        """Test select dropdown action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.select("#country", "US")
            assert result is True
            mock.assert_called_once_with("select", {"selector": "#country", "value": "US"})

    async def test_browser_client_check(self):
        """Test checkbox check action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.check("#agree-checkbox", True)
            assert result is True
            mock.assert_called_once_with("check", {"selector": "#agree-checkbox", "checked": True})

    async def test_browser_client_submit(self):
        """Test form submit action."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(client, "_mcp_call", new_callable=AsyncMock, return_value=True) as mock:
            result = await client.submit("#login-form")
            assert result is True
            mock.assert_called_once_with("submit", {"selector": "#login-form"})

    async def test_browser_client_get_element_position(self):
        """Test getting element position."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"x": 100, "y": 200, "width": 300, "height": 50}
        ):
            result = await client.get_element_position("#button")
            assert result["x"] == 100
            assert result["y"] == 200
            assert result["width"] == 300
            assert result["height"] == 50

    async def test_browser_client_assert_position_success(self):
        """Test position assertion (matching)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"x": 100, "y": 200, "width": 300, "height": 50}
        ):
            result = await client.assert_position("#button", {"x": 100, "y": 200})
            assert result is True

    async def test_browser_client_assert_position_failure(self):
        """Test position assertion (not matching)."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"x": 100, "y": 200, "width": 300, "height": 50}
        ):
            result = await client.assert_position("#button", {"x": 500, "y": 200})
            assert result is False

    async def test_browser_client_get_dom_snapshot(self):
        """Test getting DOM snapshot."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"html": "<html><body>Hello</body></html>"}
        ):
            result = await client.get_dom_snapshot()
            assert "Hello" in result

    async def test_browser_client_xpath(self):
        """Test XPath selector."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"elements": ["elem1", "elem2"]}
        ):
            result = await client.xpath("//button[@id='submit']")
            assert len(result) == 2
            assert "elem1" in result

    async def test_browser_client_find_by_text(self):
        """Test find element by text content."""
        client = BrowserMCPClient()
        client._connected = True
        with patch.object(
            client, "_mcp_call", new_callable=AsyncMock,
            return_value={"selector": "#found-element"}
        ):
            result = await client.find_by_text("Submit")
            assert result == "#found-element"
