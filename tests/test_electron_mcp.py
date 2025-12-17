"""
Tests for Electron MCP integration.

This module tests the Electron MCP client for E2E desktop app testing.
"""

import json
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Import from integrations package directly (tests run from auto-claude/ directory)
sys.path.insert(0, "auto-claude")
from integrations.mcp.platform import detect_electron_project, get_electron_entry
from integrations.mcp.electron import (
    ElectronMCPClient,
    ElectronConfig,
    WindowState,
)


class TestElectronProjectDetection:
    """Tests for Electron project detection."""

    def test_detect_electron_project_via_dependency(self, tmp_path: Path):
        """Test Electron project detection via devDependencies."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-electron-app",
                    "devDependencies": {"electron": "^28.0.0"},
                }
            )
        )

        assert detect_electron_project(tmp_path) is True

    def test_detect_electron_project_via_main_dependency(self, tmp_path: Path):
        """Test Electron project detection via dependencies."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-electron-app",
                    "dependencies": {"electron": "^28.0.0"},
                }
            )
        )

        assert detect_electron_project(tmp_path) is True

    def test_detect_non_electron_project(self, tmp_path: Path):
        """Test non-Electron project detection."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-react-app",
                    "dependencies": {"react": "^18.0.0"},
                }
            )
        )

        assert detect_electron_project(tmp_path) is False

    def test_detect_electron_project_no_package_json(self, tmp_path: Path):
        """Test detection when package.json doesn't exist."""
        assert detect_electron_project(tmp_path) is False

    def test_detect_electron_project_invalid_json(self, tmp_path: Path):
        """Test detection with invalid JSON."""
        package_json = tmp_path / "package.json"
        package_json.write_text("not valid json {{{")

        assert detect_electron_project(tmp_path) is False

    def test_get_electron_entry_point(self, tmp_path: Path):
        """Test getting Electron app entry point."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-app",
                    "main": "src/main/index.js",
                    "devDependencies": {"electron": "^28.0.0"},
                }
            )
        )

        # Create the entry file
        entry_dir = tmp_path / "src" / "main"
        entry_dir.mkdir(parents=True)
        (entry_dir / "index.js").write_text("// Electron main")

        entry = get_electron_entry(tmp_path)
        assert entry is not None
        assert entry.name == "index.js"

    def test_get_electron_entry_point_default(self, tmp_path: Path):
        """Test getting default entry point when main not specified."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-app",
                    "devDependencies": {"electron": "^28.0.0"},
                }
            )
        )

        # Create default entry file
        (tmp_path / "index.js").write_text("// Electron main")

        entry = get_electron_entry(tmp_path)
        assert entry is not None
        assert entry.name == "index.js"

    def test_get_electron_entry_not_found(self, tmp_path: Path):
        """Test entry point not found."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "name": "my-app",
                    "main": "nonexistent.js",
                }
            )
        )

        entry = get_electron_entry(tmp_path)
        assert entry is None


class TestElectronConfig:
    """Tests for Electron configuration."""

    def test_electron_config_defaults(self):
        """Test ElectronConfig default values."""
        config = ElectronConfig()
        assert config.headless is False  # Electron usually needs display
        assert config.dev_mode is True
        assert config.timeout == 60000
        assert config.screenshot_on_failure is True

    def test_electron_config_custom(self):
        """Test ElectronConfig with custom values."""
        config = ElectronConfig(
            headless=True,
            dev_mode=False,
            timeout=120000,
            screenshot_on_failure=False,
        )
        assert config.headless is True
        assert config.dev_mode is False
        assert config.timeout == 120000
        assert config.screenshot_on_failure is False


class TestWindowState:
    """Tests for WindowState dataclass."""

    def test_window_state_creation(self):
        """Test WindowState creation."""
        state = WindowState(
            title="My App",
            width=800,
            height=600,
            x=100,
            y=100,
            focused=True,
            visible=True,
            fullscreen=False,
        )
        assert state.title == "My App"
        assert state.width == 800
        assert state.height == 600
        assert state.x == 100
        assert state.y == 100
        assert state.focused is True
        assert state.visible is True
        assert state.fullscreen is False


class TestElectronMCPClient:
    """Tests for ElectronMCPClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with default config."""
        client = ElectronMCPClient()
        assert client.config is not None
        assert isinstance(client.config, ElectronConfig)
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_client_initialization_with_config(self):
        """Test client initialization with custom config."""
        config = ElectronConfig(timeout=90000)
        client = ElectronMCPClient(config=config)
        assert client.config.timeout == 90000

    @pytest.mark.asyncio
    async def test_launch_app_requires_connection(self, tmp_path: Path):
        """Test that launch_app raises if not connected."""
        client = ElectronMCPClient()

        with pytest.raises(RuntimeError, match="Not connected"):
            await client.launch_app(tmp_path)

    @pytest.mark.asyncio
    async def test_launch_app_success(self, tmp_path: Path):
        """Test successful app launch."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.launch_app(tmp_path)

            assert result is True
            mock.assert_called_once()
            call_args = mock.call_args
            assert call_args[0][0] == "launchApp"

    @pytest.mark.asyncio
    async def test_get_window_state(self):
        """Test getting window state."""
        client = ElectronMCPClient()
        client._connected = True

        mock_state = {
            "title": "Test App",
            "width": 1024,
            "height": 768,
            "x": 50,
            "y": 50,
            "focused": True,
            "visible": True,
            "fullscreen": False,
        }

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = mock_state
            state = await client.get_window_state()

            assert state.title == "Test App"
            assert state.width == 1024
            assert state.height == 768
            assert state.focused is True

    @pytest.mark.asyncio
    async def test_click(self):
        """Test click action."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.click("#submit-button")

            mock.assert_called_with("click", {"selector": "#submit-button"})
            assert result is True

    @pytest.mark.asyncio
    async def test_type_text(self):
        """Test type text action."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.type_text("#input-field", "Hello World")

            mock.assert_called_with(
                "type", {"selector": "#input-field", "text": "Hello World"}
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close connection."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            await client.close()

            mock.assert_called_with("closeApp", {})
            assert client._connected is False

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self):
        """Test close when not connected does nothing."""
        client = ElectronMCPClient()

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            await client.close()
            mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_press_key(self):
        """Test keyboard shortcut."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.press_key("s", modifiers=["Control"])

            mock.assert_called_with("pressKey", {"key": "s", "modifiers": ["Control"]})
            assert result is True

    @pytest.mark.asyncio
    async def test_press_key_no_modifiers(self):
        """Test keyboard press without modifiers."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.press_key("Enter")

            mock.assert_called_with("pressKey", {"key": "Enter", "modifiers": []})
            assert result is True

    @pytest.mark.asyncio
    async def test_click_menu(self):
        """Test menu click."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.click_menu(["File", "Save"])

            mock.assert_called_with("clickMenu", {"path": ["File", "Save"]})
            assert result is True

    @pytest.mark.asyncio
    async def test_assert_window_title_match(self):
        """Test window title assertion matches."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "title": "My App - Untitled",
                "width": 800,
                "height": 600,
                "x": 0,
                "y": 0,
                "focused": True,
                "visible": True,
                "fullscreen": False,
            }
            result = await client.assert_window_title("My App")
            assert result is True

    @pytest.mark.asyncio
    async def test_assert_window_title_no_match(self):
        """Test window title assertion does not match."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "title": "Other App",
                "width": 800,
                "height": 600,
                "x": 0,
                "y": 0,
                "focused": True,
                "visible": True,
                "fullscreen": False,
            }
            result = await client.assert_window_title("My App")
            assert result is False

    @pytest.mark.asyncio
    async def test_assert_window_size_within_tolerance(self):
        """Test window size assertion within tolerance."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "title": "Test",
                "width": 805,
                "height": 600,
                "x": 0,
                "y": 0,
                "focused": True,
                "visible": True,
                "fullscreen": False,
            }
            result = await client.assert_window_size(800, 600, tolerance=10)
            assert result is True

    @pytest.mark.asyncio
    async def test_assert_window_size_outside_tolerance(self):
        """Test window size assertion outside tolerance."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "title": "Test",
                "width": 900,
                "height": 600,
                "x": 0,
                "y": 0,
                "focused": True,
                "visible": True,
                "fullscreen": False,
            }
            result = await client.assert_window_size(800, 600, tolerance=10)
            assert result is False

    @pytest.mark.asyncio
    async def test_screenshot(self, tmp_path: Path):
        """Test screenshot capture."""
        client = ElectronMCPClient()
        client._connected = True
        screenshot_path = tmp_path / "test.png"

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.screenshot(screenshot_path)

            mock.assert_called_with("screenshot", {"path": str(screenshot_path)})
            assert result is True


class TestPlatformPathResolution:
    """Tests for platform-specific path resolution."""

    def test_resolve_app_path_macos_app_bundle(self, tmp_path: Path):
        """Test macOS app bundle path resolution."""
        client = ElectronMCPClient()
        client._platform = "darwin"

        # Create mock app bundle structure
        (tmp_path / "Contents" / "MacOS").mkdir(parents=True)

        resolved = client._resolve_app_path(tmp_path)
        assert resolved == tmp_path

    def test_resolve_app_path_macos_dev_mode(self, tmp_path: Path):
        """Test macOS dev mode path resolution."""
        client = ElectronMCPClient()
        client._platform = "darwin"

        # Create mock dev structure
        (tmp_path / "node_modules" / "electron").mkdir(parents=True)
        (tmp_path / "node_modules" / ".bin").mkdir(parents=True)
        (tmp_path / "node_modules" / ".bin" / "electron").touch()

        resolved = client._resolve_app_path(tmp_path)
        assert "electron" in str(resolved)

    def test_resolve_app_path_windows_exe(self, tmp_path: Path):
        """Test Windows exe path resolution."""
        client = ElectronMCPClient()
        client._platform = "windows"

        # Create mock exe
        (tmp_path / "electron.exe").touch()

        resolved = client._resolve_app_path(tmp_path)
        assert "electron.exe" in str(resolved)

    def test_resolve_app_path_windows_dev_mode(self, tmp_path: Path):
        """Test Windows dev mode path resolution."""
        client = ElectronMCPClient()
        client._platform = "windows"

        # Create mock dev structure
        (tmp_path / "node_modules" / "electron" / "dist").mkdir(parents=True)
        (tmp_path / "node_modules" / "electron" / "dist" / "electron.exe").touch()

        resolved = client._resolve_app_path(tmp_path)
        assert "electron.exe" in str(resolved)

    def test_resolve_app_path_linux(self, tmp_path: Path):
        """Test Linux path resolution."""
        client = ElectronMCPClient()
        client._platform = "linux"

        # Create mock electron binary
        (tmp_path / "electron").touch()

        resolved = client._resolve_app_path(tmp_path)
        assert "electron" in str(resolved)

    def test_resolve_app_path_linux_dev_mode(self, tmp_path: Path):
        """Test Linux dev mode path resolution."""
        client = ElectronMCPClient()
        client._platform = "linux"

        # Create mock dev structure
        (tmp_path / "node_modules" / ".bin").mkdir(parents=True)
        (tmp_path / "node_modules" / ".bin" / "electron").touch()

        resolved = client._resolve_app_path(tmp_path)
        assert "electron" in str(resolved)

    def test_resolve_app_path_fallback(self, tmp_path: Path):
        """Test path resolution fallback to original path."""
        client = ElectronMCPClient()
        client._platform = "darwin"

        # No app bundle or node_modules structure
        resolved = client._resolve_app_path(tmp_path)
        assert resolved == tmp_path


class TestDesktopUIInteractions:
    """Tests for desktop UI interactions (Task 2)."""

    @pytest.mark.asyncio
    async def test_focus_window(self):
        """Test focusing window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.focus_window()

            mock.assert_called_with("focusWindow", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_resize_window(self):
        """Test resizing window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.resize_window(1024, 768)

            mock.assert_called_with("resizeWindow", {"width": 1024, "height": 768})
            assert result is True

    @pytest.mark.asyncio
    async def test_minimize_window(self):
        """Test minimizing window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.minimize_window()

            mock.assert_called_with("minimizeWindow", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_maximize_window(self):
        """Test maximizing window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.maximize_window()

            mock.assert_called_with("maximizeWindow", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_restore_window(self):
        """Test restoring window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.restore_window()

            mock.assert_called_with("restoreWindow", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_handle_dialog_accept(self):
        """Test accepting dialog."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.handle_dialog("accept")

            mock.assert_called_with("handleDialog", {"action": "accept"})
            assert result is True

    @pytest.mark.asyncio
    async def test_handle_dialog_with_value(self):
        """Test handling prompt dialog with value."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.handle_dialog("setValue", "test input")

            mock.assert_called_with("handleDialog", {"action": "setValue", "value": "test input"})
            assert result is True

    @pytest.mark.asyncio
    async def test_get_dialog_message(self):
        """Test getting dialog message."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {"message": "Are you sure?"}
            result = await client.get_dialog_message()

            mock.assert_called_with("getDialogMessage", {})
            assert result == "Are you sure?"


class TestMultiWindowHandling:
    """Tests for multi-window handling (Task 3)."""

    @pytest.mark.asyncio
    async def test_get_all_windows(self):
        """Test getting all windows."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "windows": [
                    {"id": 1, "title": "Main Window"},
                    {"id": 2, "title": "Settings"},
                ]
            }
            result = await client.get_all_windows()

            mock.assert_called_with("getAllWindows", {})
            assert len(result) == 2
            assert result[0]["title"] == "Main Window"

    @pytest.mark.asyncio
    async def test_switch_to_window(self):
        """Test switching to window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.switch_to_window(2)

            mock.assert_called_with("switchToWindow", {"windowId": 2})
            assert result is True

    @pytest.mark.asyncio
    async def test_close_window_specific(self):
        """Test closing specific window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.close_window(2)

            mock.assert_called_with("closeWindow", {"windowId": 2})
            assert result is True

    @pytest.mark.asyncio
    async def test_close_window_current(self):
        """Test closing current window."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.close_window()

            mock.assert_called_with("closeWindow", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_navigate_to(self):
        """Test navigation within app."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.navigate_to("/settings")

            mock.assert_called_with("navigate", {"route": "/settings"})
            assert result is True

    @pytest.mark.asyncio
    async def test_go_back(self):
        """Test navigating back."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.go_back()

            mock.assert_called_with("goBack", {})
            assert result is True

    @pytest.mark.asyncio
    async def test_go_forward(self):
        """Test navigating forward."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = True
            result = await client.go_forward()

            mock.assert_called_with("goForward", {})
            assert result is True


class TestFailureReporting:
    """Tests for failure reporting (Task 4)."""

    @pytest.mark.asyncio
    async def test_get_app_state(self):
        """Test getting app state for failure context."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "focusedElement": "#input-field",
                "activeMenu": None,
                "modalOpen": False,
            }
            result = await client.get_app_state()

            mock.assert_called_with("getAppState", {})
            assert result["focusedElement"] == "#input-field"
            assert result["modalOpen"] is False

    @pytest.mark.asyncio
    async def test_get_ipc_messages(self):
        """Test getting IPC messages for debugging."""
        client = ElectronMCPClient()
        client._connected = True

        with patch.object(client, "_mcp_call", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "messages": [
                    {"channel": "app:ready", "data": {}},
                    {"channel": "window:resize", "data": {"width": 800}},
                ]
            }
            result = await client.get_ipc_messages(limit=10)

            mock.assert_called_with("getIPCMessages", {"limit": 10})
            assert len(result) == 2
            assert result[0]["channel"] == "app:ready"


class TestElectronFailureContext:
    """Tests for ElectronFailureContext dataclass."""

    def test_failure_context_to_dict(self):
        """Test converting failure context to dict."""
        from integrations.mcp.electron_validation import ElectronFailureContext

        window_state = WindowState(
            title="Test App",
            width=800,
            height=600,
            x=100,
            y=100,
            focused=True,
            visible=True,
            fullscreen=False,
        )

        context = ElectronFailureContext(
            test_case_id="test-1",
            test_case_name="Login Test",
            error_message="Element not found",
            window_state=window_state,
            app_state={"focusedElement": "#login-button"},
            ipc_messages=[{"channel": "app:error", "data": {"message": "Not found"}}],
        )

        result = context.to_dict()

        assert result["test_case_id"] == "test-1"
        assert result["test_case_name"] == "Login Test"
        assert result["error"] == "Element not found"
        assert result["window_state"]["title"] == "Test App"
        assert result["window_state"]["width"] == 800
        assert result["app_state"]["focusedElement"] == "#login-button"
        assert len(result["ipc_messages"]) == 1

    def test_failure_context_without_window_state(self):
        """Test failure context without window state."""
        from integrations.mcp.electron_validation import ElectronFailureContext

        context = ElectronFailureContext(
            test_case_id="test-2",
            test_case_name="Startup Test",
            error_message="App failed to launch",
        )

        result = context.to_dict()

        assert result["test_case_id"] == "test-2"
        assert result["window_state"] is None
        assert result["screenshot"] is None
