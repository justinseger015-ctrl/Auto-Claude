"""
MCP availability detection.

This module provides availability checking and caching for MCP servers.

Story 6-4: MCP Graceful Degradation
Acceptance Criteria #1: Detect when MCP integration is unavailable
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .browser import BrowserMCPClient
    from .electron import ElectronMCPClient

logger = logging.getLogger(__name__)


class MCPStatus(Enum):
    """MCP server status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class MCPFailureReason(Enum):
    """Reasons for MCP unavailability."""

    SERVER_NOT_RUNNING = "server_not_running"
    CONNECTION_TIMEOUT = "connection_timeout"
    AUTH_FAILED = "auth_failed"
    VERSION_MISMATCH = "version_mismatch"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


@dataclass
class MCPAvailability:
    """MCP availability status.

    Attributes:
        status: Current MCP status
        reason: Failure reason if unavailable
        message: Human-readable status message
        checked_at: When this check was performed
        retry_after: When to retry (for transient failures)
    """

    status: MCPStatus
    reason: MCPFailureReason | None
    message: str
    checked_at: datetime
    retry_after: datetime | None = None

    @property
    def is_available(self) -> bool:
        """Check if MCP is available."""
        return self.status == MCPStatus.AVAILABLE


class MCPAvailabilityChecker:
    """Checks and caches MCP availability.

    Provides availability checking with caching to avoid repeated
    connection attempts in short time windows.
    """

    def __init__(self, cache_duration: int = 60):
        """Initialize checker.

        Args:
            cache_duration: Cache duration in seconds
        """
        self._cache_duration = timedelta(seconds=cache_duration)
        self._browser_cache: MCPAvailability | None = None
        self._electron_cache: MCPAvailability | None = None

    async def check_browser_mcp(self, force: bool = False) -> MCPAvailability:
        """Check Browser MCP availability.

        Args:
            force: Force fresh check, ignore cache

        Returns:
            MCPAvailability status
        """
        if not force and self._browser_cache:
            if datetime.now() - self._browser_cache.checked_at < self._cache_duration:
                return self._browser_cache

        try:
            # Attempt connection
            from .browser import BrowserMCPClient

            client = BrowserMCPClient()

            connected = await client.connect()
            await client.close()

            if connected:
                self._browser_cache = MCPAvailability(
                    status=MCPStatus.AVAILABLE,
                    reason=None,
                    message="Browser MCP is available",
                    checked_at=datetime.now(),
                )
            else:
                self._browser_cache = MCPAvailability(
                    status=MCPStatus.UNAVAILABLE,
                    reason=MCPFailureReason.SERVER_NOT_RUNNING,
                    message="Browser MCP server is not running",
                    checked_at=datetime.now(),
                    retry_after=datetime.now() + timedelta(minutes=5),
                )

        except TimeoutError:
            self._browser_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.CONNECTION_TIMEOUT,
                message="Connection to Browser MCP timed out",
                checked_at=datetime.now(),
                retry_after=datetime.now() + timedelta(minutes=1),
            )
        except PermissionError:
            self._browser_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.PERMISSION_DENIED,
                message="Permission denied connecting to Browser MCP",
                checked_at=datetime.now(),
            )
        except Exception as e:
            self._browser_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.UNKNOWN,
                message=f"Browser MCP check failed: {e}",
                checked_at=datetime.now(),
            )

        return self._browser_cache

    async def check_electron_mcp(self, force: bool = False) -> MCPAvailability:
        """Check Electron MCP availability.

        Args:
            force: Force fresh check, ignore cache

        Returns:
            MCPAvailability status
        """
        if not force and self._electron_cache:
            if datetime.now() - self._electron_cache.checked_at < self._cache_duration:
                return self._electron_cache

        try:
            # Attempt connection
            from .electron import ElectronMCPClient

            client = ElectronMCPClient()

            connected = await client.connect()
            await client.close()

            if connected:
                self._electron_cache = MCPAvailability(
                    status=MCPStatus.AVAILABLE,
                    reason=None,
                    message="Electron MCP is available",
                    checked_at=datetime.now(),
                )
            else:
                self._electron_cache = MCPAvailability(
                    status=MCPStatus.UNAVAILABLE,
                    reason=MCPFailureReason.SERVER_NOT_RUNNING,
                    message="Electron MCP server is not running",
                    checked_at=datetime.now(),
                    retry_after=datetime.now() + timedelta(minutes=5),
                )

        except TimeoutError:
            self._electron_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.CONNECTION_TIMEOUT,
                message="Connection to Electron MCP timed out",
                checked_at=datetime.now(),
                retry_after=datetime.now() + timedelta(minutes=1),
            )
        except PermissionError:
            self._electron_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.PERMISSION_DENIED,
                message="Permission denied connecting to Electron MCP",
                checked_at=datetime.now(),
            )
        except Exception as e:
            self._electron_cache = MCPAvailability(
                status=MCPStatus.UNAVAILABLE,
                reason=MCPFailureReason.UNKNOWN,
                message=f"Electron MCP check failed: {e}",
                checked_at=datetime.now(),
            )

        return self._electron_cache

    def clear_cache(self) -> None:
        """Clear all cached availability results."""
        self._browser_cache = None
        self._electron_cache = None
