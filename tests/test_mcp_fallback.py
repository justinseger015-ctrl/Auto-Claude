"""
Tests for MCP graceful degradation.

Story 6-4: MCP Graceful Degradation
Covers availability detection, error messaging, and fallback behavior.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import json

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")


class TestMCPStatusEnum:
    """Test MCPStatus enum values."""

    def test_available_status(self):
        """Test AVAILABLE status value."""
        from integrations.mcp.availability import MCPStatus

        assert MCPStatus.AVAILABLE.value == "available"

    def test_unavailable_status(self):
        """Test UNAVAILABLE status value."""
        from integrations.mcp.availability import MCPStatus

        assert MCPStatus.UNAVAILABLE.value == "unavailable"

    def test_degraded_status(self):
        """Test DEGRADED status value."""
        from integrations.mcp.availability import MCPStatus

        assert MCPStatus.DEGRADED.value == "degraded"


class TestMCPFailureReason:
    """Test MCPFailureReason enum values."""

    def test_all_failure_reasons_exist(self):
        """Test all expected failure reasons exist."""
        from integrations.mcp.availability import MCPFailureReason

        reasons = [
            MCPFailureReason.SERVER_NOT_RUNNING,
            MCPFailureReason.CONNECTION_TIMEOUT,
            MCPFailureReason.AUTH_FAILED,
            MCPFailureReason.VERSION_MISMATCH,
            MCPFailureReason.PERMISSION_DENIED,
            MCPFailureReason.UNKNOWN,
        ]

        assert len(reasons) == 6


class TestMCPAvailability:
    """Test MCPAvailability dataclass."""

    def test_availability_is_available(self):
        """Test is_available property when available."""
        from integrations.mcp.availability import (
            MCPAvailability,
            MCPStatus,
        )

        availability = MCPAvailability(
            status=MCPStatus.AVAILABLE,
            reason=None,
            message="MCP is available",
            checked_at=datetime.now(),
        )

        assert availability.is_available is True

    def test_availability_is_unavailable(self):
        """Test is_available property when unavailable."""
        from integrations.mcp.availability import (
            MCPAvailability,
            MCPStatus,
            MCPFailureReason,
        )

        availability = MCPAvailability(
            status=MCPStatus.UNAVAILABLE,
            reason=MCPFailureReason.SERVER_NOT_RUNNING,
            message="Server not running",
            checked_at=datetime.now(),
        )

        assert availability.is_available is False


class TestMCPErrors:
    """Test error codes and messages."""

    def test_error_for_server_not_running(self):
        """Test error message for server not running."""
        from integrations.mcp.errors import (
            get_error_for_reason,
            MCPFailureReason,
        )

        error = get_error_for_reason(MCPFailureReason.SERVER_NOT_RUNNING)

        assert error.code == "MCP_001"
        assert "not running" in error.message
        assert "npm install" in error.remediation

    def test_error_for_connection_timeout(self):
        """Test error message for connection timeout."""
        from integrations.mcp.errors import (
            get_error_for_reason,
            MCPFailureReason,
        )

        error = get_error_for_reason(MCPFailureReason.CONNECTION_TIMEOUT)

        assert error.code == "MCP_002"
        assert "timed out" in error.message.lower()

    def test_error_for_auth_failed(self):
        """Test error message for auth failed."""
        from integrations.mcp.errors import (
            get_error_for_reason,
            MCPFailureReason,
        )

        error = get_error_for_reason(MCPFailureReason.AUTH_FAILED)

        assert error.code == "MCP_003"
        assert "auth" in error.message.lower()

    def test_all_errors_have_remediation(self):
        """Test all error codes have remediation text."""
        from integrations.mcp.errors import (
            get_error_for_reason,
            MCPFailureReason,
        )

        for reason in MCPFailureReason:
            error = get_error_for_reason(reason)
            assert len(error.remediation) > 0

    def test_format_error_message_includes_code(self):
        """Test formatted message includes error code."""
        from integrations.mcp.errors import (
            format_error_message,
            MCPFailureReason,
        )

        message = format_error_message(MCPFailureReason.SERVER_NOT_RUNNING)

        assert "MCP_001" in message
        assert "Remediation:" in message

    def test_format_error_message_without_remediation(self):
        """Test message can exclude remediation."""
        from integrations.mcp.errors import (
            format_error_message,
            MCPFailureReason,
        )

        message = format_error_message(
            MCPFailureReason.SERVER_NOT_RUNNING,
            include_remediation=False,
        )

        assert "MCP_001" in message
        assert "Remediation:" not in message


class TestFallbackConfig:
    """Test FallbackConfig dataclass."""

    def test_default_fallback_config(self):
        """Test default fallback configuration."""
        from integrations.mcp.fallback import FallbackConfig, FallbackMode

        config = FallbackConfig()

        assert config.mode == FallbackMode.WARN
        assert config.run_unit_tests is True
        assert config.run_lint is True
        assert config.mark_as_partial is True

    def test_custom_fallback_config(self):
        """Test custom fallback configuration."""
        from integrations.mcp.fallback import FallbackConfig, FallbackMode

        config = FallbackConfig(
            mode=FallbackMode.SKIP,
            run_unit_tests=False,
            run_lint=False,
        )

        assert config.mode == FallbackMode.SKIP
        assert config.run_unit_tests is False

    def test_load_fallback_config_missing_file(self, tmp_path):
        """Test loading fallback config when file doesn't exist."""
        from integrations.mcp.fallback import load_fallback_config, FallbackMode

        config = load_fallback_config(tmp_path)

        assert config.mode == FallbackMode.WARN  # Default

    def test_load_fallback_config_from_file(self, tmp_path):
        """Test loading fallback config from JSON file."""
        from integrations.mcp.fallback import load_fallback_config, FallbackMode

        config_dir = tmp_path / ".auto-claude"
        config_dir.mkdir()
        config_file = config_dir / "mcp-fallback.json"
        config_file.write_text(json.dumps({
            "mode": "skip",
            "run_unit_tests": False,
            "run_lint": True,
            "mark_as_partial": False,
        }))

        config = load_fallback_config(tmp_path)

        assert config.mode == FallbackMode.SKIP
        assert config.run_unit_tests is False
        assert config.run_lint is True


@pytest.mark.asyncio
class TestHandleMCPUnavailable:
    """Test fallback behavior when MCP is unavailable."""

    async def test_fallback_warn_mode(self, tmp_path):
        """Test WARN fallback mode continues build."""
        from integrations.mcp.availability import (
            MCPAvailability,
            MCPStatus,
            MCPFailureReason,
        )
        from integrations.mcp.fallback import (
            FallbackConfig,
            FallbackMode,
            handle_mcp_unavailable,
        )

        availability = MCPAvailability(
            status=MCPStatus.UNAVAILABLE,
            reason=MCPFailureReason.SERVER_NOT_RUNNING,
            message="Server not running",
            checked_at=datetime.now(),
        )

        config = FallbackConfig(mode=FallbackMode.WARN)

        result, fallback = await handle_mcp_unavailable(
            availability=availability,
            project_path=tmp_path,
            config=config,
        )

        assert result.passed is True  # Doesn't fail build
        assert fallback.used_fallback is True
        assert "Server not running" in fallback.reason

    async def test_fallback_skip_mode(self, tmp_path):
        """Test SKIP fallback mode skips E2E silently."""
        from integrations.mcp.availability import (
            MCPAvailability,
            MCPStatus,
            MCPFailureReason,
        )
        from integrations.mcp.fallback import (
            FallbackConfig,
            FallbackMode,
            handle_mcp_unavailable,
        )

        availability = MCPAvailability(
            status=MCPStatus.UNAVAILABLE,
            reason=MCPFailureReason.CONNECTION_TIMEOUT,
            message="Connection timeout",
            checked_at=datetime.now(),
        )

        config = FallbackConfig(mode=FallbackMode.SKIP)

        result, fallback = await handle_mcp_unavailable(
            availability=availability,
            project_path=tmp_path,
            config=config,
        )

        assert result.passed is True
        assert result.total_checks == 0
        assert fallback.validation_run == "none"

    async def test_fallback_fail_mode(self, tmp_path):
        """Test FAIL fallback mode returns None."""
        from integrations.mcp.availability import (
            MCPAvailability,
            MCPStatus,
            MCPFailureReason,
        )
        from integrations.mcp.fallback import (
            FallbackConfig,
            FallbackMode,
            handle_mcp_unavailable,
        )

        availability = MCPAvailability(
            status=MCPStatus.UNAVAILABLE,
            reason=MCPFailureReason.AUTH_FAILED,
            message="Auth failed",
            checked_at=datetime.now(),
        )

        config = FallbackConfig(mode=FallbackMode.FAIL)

        result, fallback = await handle_mcp_unavailable(
            availability=availability,
            project_path=tmp_path,
            config=config,
        )

        assert result is None
        assert fallback.used_fallback is False


class TestMCPAvailabilityChecker:
    """Test MCP availability checker."""

    def test_checker_cache_duration(self):
        """Test checker has configurable cache duration."""
        from integrations.mcp.availability import MCPAvailabilityChecker

        checker = MCPAvailabilityChecker(cache_duration=120)

        # Cache duration should be set
        assert checker._cache_duration.total_seconds() == 120


class TestMCPErrorHasDocsURL:
    """Test all errors have documentation URL."""

    def test_all_known_errors_have_docs_url(self):
        """Test all known error types have documentation URL."""
        from integrations.mcp.errors import get_error_for_reason, MCPFailureReason

        known_reasons = [
            MCPFailureReason.SERVER_NOT_RUNNING,
            MCPFailureReason.CONNECTION_TIMEOUT,
            MCPFailureReason.AUTH_FAILED,
            MCPFailureReason.VERSION_MISMATCH,
            MCPFailureReason.PERMISSION_DENIED,
        ]

        for reason in known_reasons:
            error = get_error_for_reason(reason)
            assert error.docs_url is not None, f"{reason} should have docs URL"
