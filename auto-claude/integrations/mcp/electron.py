"""
Electron MCP client for E2E desktop application testing.

This module provides integration with Electron MCP server for automated
desktop UI interactions and window state validation.
"""

import logging
import platform
from pathlib import Path
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ElectronConfig:
    """Electron MCP configuration.

    Attributes:
        headless: Whether to run headless (usually False for Electron).
        dev_mode: Whether to run in development mode.
        timeout: Timeout in milliseconds for operations.
        screenshot_on_failure: Whether to capture screenshots on test failure.
    """

    headless: bool = False  # Electron usually needs display
    dev_mode: bool = True
    timeout: int = 60000  # ms - longer for app startup
    screenshot_on_failure: bool = True


@dataclass
class WindowState:
    """Electron window state.

    Attributes:
        title: Window title.
        width: Window width in pixels.
        height: Window height in pixels.
        x: Window x position.
        y: Window y position.
        focused: Whether window is focused.
        visible: Whether window is visible.
        fullscreen: Whether window is fullscreen.
    """

    title: str
    width: int
    height: int
    x: int
    y: int
    focused: bool
    visible: bool
    fullscreen: bool


class ElectronMCPClient:
    """Client for Electron MCP interactions.

    Provides methods to launch Electron apps, interact with UI elements,
    validate window state, and capture screenshots.
    """

    def __init__(self, config: ElectronConfig | None = None):
        """Initialize Electron client with optional configuration.

        Args:
            config: Electron configuration. Uses defaults if not provided.
        """
        self.config = config or ElectronConfig()
        self._connected = False
        self._app_path: Path | None = None
        self._platform = platform.system().lower()

    async def connect(self) -> bool:
        """Connect to Electron MCP server.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            # TODO: Implement actual MCP connection via Claude SDK
            await self._mcp_call("ping", {})
            self._connected = True
            logger.info("Connected to Electron MCP")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Electron MCP: {e}")
            self._connected = False
            return False

    async def launch_app(self, app_path: Path) -> bool:
        """Launch Electron application.

        Args:
            app_path: Path to Electron app.

        Returns:
            True if launch successful.

        Raises:
            RuntimeError: If not connected to Electron MCP.
        """
        if not self._connected:
            raise RuntimeError("Not connected to Electron MCP")

        # Resolve platform-specific path
        resolved_path = self._resolve_app_path(app_path)

        try:
            await self._mcp_call(
                "launchApp",
                {
                    "path": str(resolved_path),
                    "devMode": self.config.dev_mode,
                },
            )
            self._app_path = resolved_path
            logger.info(f"Launched Electron app at {resolved_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch app: {e}")
            return False

    def _resolve_app_path(self, app_path: Path) -> Path:
        """Resolve platform-specific app path.

        Looks for platform-specific Electron binaries or app bundles.

        Args:
            app_path: Base path to Electron project.

        Returns:
            Resolved path to Electron executable.
        """
        if self._platform == "darwin":
            # macOS: Look for .app bundle or electron binary
            if (app_path / "Contents" / "MacOS").exists():
                return app_path
            if (app_path / "node_modules" / "electron").exists():
                return app_path / "node_modules" / ".bin" / "electron"
        elif self._platform == "windows":
            # Windows: Look for .exe
            if (app_path / "electron.exe").exists():
                return app_path / "electron.exe"
            if (app_path / "node_modules" / "electron").exists():
                return (
                    app_path / "node_modules" / "electron" / "dist" / "electron.exe"
                )
        else:
            # Linux: Look for electron binary
            if (app_path / "electron").exists():
                return app_path / "electron"
            if (app_path / "node_modules" / ".bin" / "electron").exists():
                return app_path / "node_modules" / ".bin" / "electron"

        return app_path

    async def get_window_state(self) -> WindowState:
        """Get current window state.

        Returns:
            WindowState with current window properties.
        """
        result = await self._mcp_call("getWindowState", {})
        return WindowState(
            title=result.get("title", ""),
            width=result.get("width", 0),
            height=result.get("height", 0),
            x=result.get("x", 0),
            y=result.get("y", 0),
            focused=result.get("focused", False),
            visible=result.get("visible", False),
            fullscreen=result.get("fullscreen", False),
        )

    async def click(self, selector: str) -> bool:
        """Click an element in the Electron app.

        Args:
            selector: CSS selector for element to click.

        Returns:
            True if click successful.
        """
        return await self._mcp_call("click", {"selector": selector})

    async def type_text(self, selector: str, text: str) -> bool:
        """Type text into an element.

        Args:
            selector: CSS selector for input element.
            text: Text to type.

        Returns:
            True if typing successful.
        """
        return await self._mcp_call("type", {"selector": selector, "text": text})

    async def press_key(self, key: str, modifiers: list[str] | None = None) -> bool:
        """Press keyboard key with optional modifiers.

        Args:
            key: Key to press (e.g., "Enter", "Tab", "a").
            modifiers: Modifier keys (e.g., ["Control", "Shift"]).

        Returns:
            True if key press successful.
        """
        return await self._mcp_call(
            "pressKey",
            {
                "key": key,
                "modifiers": modifiers or [],
            },
        )

    async def click_menu(self, menu_path: list[str]) -> bool:
        """Click a menu item by path.

        Args:
            menu_path: Menu path (e.g., ["File", "Save"]).

        Returns:
            True if menu click successful.
        """
        return await self._mcp_call("clickMenu", {"path": menu_path})

    async def assert_window_title(self, expected: str) -> bool:
        """Assert window title matches expected value.

        Args:
            expected: Expected title substring.

        Returns:
            True if title contains expected text.
        """
        state = await self.get_window_state()
        return expected in state.title

    async def assert_window_size(
        self, width: int, height: int, tolerance: int = 10
    ) -> bool:
        """Assert window size within tolerance.

        Args:
            width: Expected width.
            height: Expected height.
            tolerance: Allowed deviation in pixels.

        Returns:
            True if size within tolerance.
        """
        state = await self.get_window_state()
        return (
            abs(state.width - width) <= tolerance
            and abs(state.height - height) <= tolerance
        )

    async def screenshot(self, path: Path) -> bool:
        """Take window screenshot.

        Args:
            path: Path to save screenshot.

        Returns:
            True if screenshot captured successfully.
        """
        return await self._mcp_call("screenshot", {"path": str(path)})

    # Window management methods (Task 2)
    async def focus_window(self) -> bool:
        """Bring window to front and focus it.

        Returns:
            True if focus successful.
        """
        return await self._mcp_call("focusWindow", {})

    async def resize_window(self, width: int, height: int) -> bool:
        """Resize window to specified dimensions.

        Args:
            width: Target width in pixels.
            height: Target height in pixels.

        Returns:
            True if resize successful.
        """
        return await self._mcp_call("resizeWindow", {"width": width, "height": height})

    async def minimize_window(self) -> bool:
        """Minimize window to taskbar/dock.

        Returns:
            True if minimize successful.
        """
        return await self._mcp_call("minimizeWindow", {})

    async def maximize_window(self) -> bool:
        """Maximize window.

        Returns:
            True if maximize successful.
        """
        return await self._mcp_call("maximizeWindow", {})

    async def restore_window(self) -> bool:
        """Restore window from minimized/maximized state.

        Returns:
            True if restore successful.
        """
        return await self._mcp_call("restoreWindow", {})

    # Dialog handling (Task 2)
    async def handle_dialog(self, action: str, value: str | None = None) -> bool:
        """Handle native dialog (alert, confirm, prompt, file picker).

        Args:
            action: Dialog action ("accept", "dismiss", "setValue").
            value: Value to set for prompt dialogs.

        Returns:
            True if dialog handled successfully.
        """
        params = {"action": action}
        if value is not None:
            params["value"] = value
        return await self._mcp_call("handleDialog", params)

    async def get_dialog_message(self) -> str | None:
        """Get message from current dialog.

        Returns:
            Dialog message text or None if no dialog.
        """
        result = await self._mcp_call("getDialogMessage", {})
        return result.get("message") if isinstance(result, dict) else None

    # Multi-window handling (Task 3)
    async def get_all_windows(self) -> list[dict]:
        """Get list of all open windows.

        Returns:
            List of window info dictionaries.
        """
        result = await self._mcp_call("getAllWindows", {})
        return result.get("windows", []) if isinstance(result, dict) else []

    async def switch_to_window(self, window_id: int | str) -> bool:
        """Switch to window by ID or title.

        Args:
            window_id: Window ID or title substring.

        Returns:
            True if switch successful.
        """
        return await self._mcp_call("switchToWindow", {"windowId": window_id})

    async def close_window(self, window_id: int | str | None = None) -> bool:
        """Close window by ID or current window if not specified.

        Args:
            window_id: Window ID to close, or None for current.

        Returns:
            True if close successful.
        """
        params = {}
        if window_id is not None:
            params["windowId"] = window_id
        return await self._mcp_call("closeWindow", params)

    # Navigation (Task 3)
    async def navigate_to(self, route: str) -> bool:
        """Navigate to a route within the app.

        Args:
            route: Route path (e.g., "/settings", "#/dashboard").

        Returns:
            True if navigation successful.
        """
        return await self._mcp_call("navigate", {"route": route})

    async def go_back(self) -> bool:
        """Navigate back in history.

        Returns:
            True if navigation successful.
        """
        return await self._mcp_call("goBack", {})

    async def go_forward(self) -> bool:
        """Navigate forward in history.

        Returns:
            True if navigation successful.
        """
        return await self._mcp_call("goForward", {})

    # IPC and app state (Task 4)
    async def get_app_state(self) -> dict:
        """Get current application state (focused element, menus, etc.).

        Returns:
            Dict with app state information for failure context.
        """
        result = await self._mcp_call("getAppState", {})
        return result if isinstance(result, dict) else {}

    async def get_ipc_messages(self, limit: int = 100) -> list[dict]:
        """Get recent IPC messages for debugging.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of IPC message dictionaries.
        """
        result = await self._mcp_call("getIPCMessages", {"limit": limit})
        return result.get("messages", []) if isinstance(result, dict) else []

    async def _mcp_call(self, method: str, params: dict) -> Any:
        """Make MCP call to Electron server.

        Args:
            method: MCP method name.
            params: Method parameters.

        Returns:
            MCP response data.

        Note:
            This is a stub implementation. Actual implementation will use
            Claude SDK MCP client to communicate with Electron MCP server.
        """
        # Stub implementation for testing
        # Real implementation will use Claude SDK MCP client
        return True

    async def close(self):
        """Close Electron app and connection."""
        if self._connected:
            await self._mcp_call("closeApp", {})
            self._connected = False
            logger.info("Electron connection closed")
