"""
MCP (Model Context Protocol) integrations for Auto Claude.

This package contains integrations for various MCP servers:
- browser.py: Browser MCP integration for E2E web testing
- electron.py: Electron MCP integration for E2E desktop testing
- electron_validation.py: E2E validation runner for Electron apps
- platform.py: Cross-platform utilities for Electron projects
- models.py: Data models for E2E test suites
- validation.py: E2E validation runner for web apps
- validation_depth.py: Complexity-aware validation depth configuration
"""

from .browser import BrowserMCPClient, BrowserConfig, E2EValidationResult
from .electron import ElectronMCPClient, ElectronConfig, WindowState
from .electron_validation import (
    run_electron_validation,
    run_electron_test_case,
    execute_electron_step,
    capture_failure_context,
    ElectronFailureContext,
)
from .platform import detect_electron_project, get_electron_entry
from .models import E2ETestSuite, E2ETestCase, E2ETestStep
from .validation import run_e2e_validation, run_test_case, execute_step
from .validation_depth import (
    ValidationDepth,
    ValidationDepthConfig,
    get_validation_depth_for_tier,
    get_timeout_for_depth,
    load_validation_config,
)
from .smoke_tests import (
    SmokeTestResult,
    run_smoke_tests,
    smoke_result_to_e2e_result,
)
from .feature_tests import (
    FeatureMapping,
    get_affected_features,
    filter_tests_by_features,
    load_feature_mappings,
    get_changed_files_from_git,
)
from .full_suite import (
    FullSuiteConfig,
    create_browser_matrix,
    expand_test_cases_for_browsers,
    run_full_suite,
    aggregate_results,
)
from .complexity_aware_validation import (
    ValidationMetrics,
    log_validation_metrics,
    run_complexity_aware_validation,
)
from .availability import (
    MCPStatus,
    MCPFailureReason,
    MCPAvailability,
    MCPAvailabilityChecker,
)
from .errors import (
    MCPError,
    MCP_ERRORS,
    get_error_for_reason,
    format_error_message,
)
from .fallback import (
    FallbackMode,
    FallbackConfig,
    FallbackResult,
    load_fallback_config,
    handle_mcp_unavailable,
)

__all__ = [
    # Browser MCP
    "BrowserMCPClient",
    "BrowserConfig",
    "E2EValidationResult",
    # Electron MCP
    "ElectronMCPClient",
    "ElectronConfig",
    "WindowState",
    "detect_electron_project",
    "get_electron_entry",
    # Electron Validation
    "run_electron_validation",
    "run_electron_test_case",
    "execute_electron_step",
    "capture_failure_context",
    "ElectronFailureContext",
    # Models
    "E2ETestSuite",
    "E2ETestCase",
    "E2ETestStep",
    # Web Validation
    "run_e2e_validation",
    "run_test_case",
    "execute_step",
    # Validation Depth
    "ValidationDepth",
    "ValidationDepthConfig",
    "get_validation_depth_for_tier",
    "get_timeout_for_depth",
    "load_validation_config",
    # Smoke Tests
    "SmokeTestResult",
    "run_smoke_tests",
    "smoke_result_to_e2e_result",
    # Feature Tests
    "FeatureMapping",
    "get_affected_features",
    "filter_tests_by_features",
    "load_feature_mappings",
    "get_changed_files_from_git",
    # Full Suite
    "FullSuiteConfig",
    "create_browser_matrix",
    "expand_test_cases_for_browsers",
    "run_full_suite",
    "aggregate_results",
    # Complexity-Aware Validation
    "ValidationMetrics",
    "log_validation_metrics",
    "run_complexity_aware_validation",
    # MCP Availability
    "MCPStatus",
    "MCPFailureReason",
    "MCPAvailability",
    "MCPAvailabilityChecker",
    # MCP Errors
    "MCPError",
    "MCP_ERRORS",
    "get_error_for_reason",
    "format_error_message",
    # MCP Fallback
    "FallbackMode",
    "FallbackConfig",
    "FallbackResult",
    "load_fallback_config",
    "handle_mcp_unavailable",
]
