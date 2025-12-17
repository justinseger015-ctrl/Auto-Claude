"""
MCP error codes and messages.

This module provides error definitions with remediation guidance
for MCP-related failures.

Story 6-4: MCP Graceful Degradation
Acceptance Criteria #1: Clear error message explains the issue
Acceptance Criteria #2: Suggested remediation steps are provided
"""

from dataclasses import dataclass
from .availability import MCPFailureReason


@dataclass
class MCPError:
    """MCP error with remediation.

    Attributes:
        code: Unique error code (e.g., MCP_001)
        message: Human-readable error message
        remediation: Step-by-step fix instructions
        docs_url: Link to documentation (optional)
    """

    code: str
    message: str
    remediation: str
    docs_url: str | None = None


# Error registry - maps failure reasons to error definitions
MCP_ERRORS: dict[MCPFailureReason, MCPError] = {
    MCPFailureReason.SERVER_NOT_RUNNING: MCPError(
        code="MCP_001",
        message="MCP server is not running",
        remediation="""To start the Browser MCP server:

1. Install the MCP server: npm install -g @anthropic/mcp-server-puppeteer
2. Start the server: mcp-server-puppeteer
3. Verify it's running: curl http://localhost:3000/health

For Electron MCP:
1. Install: npm install -g @anthropic/mcp-server-electron
2. Start: mcp-server-electron
""",
        docs_url="https://docs.anthropic.com/mcp/servers",
    ),
    MCPFailureReason.CONNECTION_TIMEOUT: MCPError(
        code="MCP_002",
        message="Connection to MCP server timed out",
        remediation="""Check your network and MCP server:

1. Verify the server is running: ps aux | grep mcp
2. Check the server port is accessible: nc -zv localhost 3000
3. Review firewall settings
4. Try increasing timeout in .auto-claude/config.json:
   {"mcp": {"timeout": 60000}}
""",
        docs_url="https://docs.anthropic.com/mcp/troubleshooting#timeout",
    ),
    MCPFailureReason.AUTH_FAILED: MCPError(
        code="MCP_003",
        message="Authentication to MCP server failed",
        remediation="""Check your MCP credentials:

1. Verify CLAUDE_MCP_TOKEN is set in your environment
2. Check the token hasn't expired
3. Regenerate token: claude mcp auth refresh
""",
        docs_url="https://docs.anthropic.com/mcp/auth",
    ),
    MCPFailureReason.VERSION_MISMATCH: MCPError(
        code="MCP_004",
        message="MCP server version is incompatible",
        remediation="""Update your MCP server:

1. Check current version: mcp-server --version
2. Update: npm update -g @anthropic/mcp-server-puppeteer
3. Restart the server

Required version: >=1.0.0
""",
        docs_url="https://docs.anthropic.com/mcp/changelog",
    ),
    MCPFailureReason.PERMISSION_DENIED: MCPError(
        code="MCP_005",
        message="Permission denied accessing MCP server",
        remediation="""Check permissions:

1. Verify you have access to the MCP socket
2. On macOS, grant accessibility permissions in System Preferences
3. On Linux, add user to appropriate group: sudo usermod -a -G mcp $USER
""",
        docs_url="https://docs.anthropic.com/mcp/permissions",
    ),
    MCPFailureReason.UNKNOWN: MCPError(
        code="MCP_999",
        message="Unknown MCP error",
        remediation="""Try these general troubleshooting steps:

1. Restart the MCP server
2. Check server logs: tail -f ~/.mcp/logs/server.log
3. Verify Claude Code is up to date
4. Report issue: https://github.com/anthropics/claude-code/issues
""",
        docs_url="https://docs.anthropic.com/mcp/troubleshooting",
    ),
}


def get_error_for_reason(reason: MCPFailureReason) -> MCPError:
    """Get error details for failure reason.

    Args:
        reason: MCPFailureReason enum value

    Returns:
        MCPError with code, message, and remediation
    """
    return MCP_ERRORS.get(reason, MCP_ERRORS[MCPFailureReason.UNKNOWN])


def format_error_message(
    reason: MCPFailureReason,
    include_remediation: bool = True,
) -> str:
    """Format error message for display.

    Creates a formatted string with error code, message, and
    optional remediation steps.

    Args:
        reason: MCPFailureReason enum value
        include_remediation: Whether to include fix steps

    Returns:
        Formatted error message string
    """
    error = get_error_for_reason(reason)

    lines = [
        f"⚠️  {error.message} [{error.code}]",
        "",
    ]

    if include_remediation:
        lines.extend([
            "Remediation:",
            error.remediation,
        ])

    if error.docs_url:
        lines.extend([
            "",
            f"Documentation: {error.docs_url}",
        ])

    return "\n".join(lines)
