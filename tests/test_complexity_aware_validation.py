"""
Tests for complexity-aware validation runner.

Story 6-3: Complexity-Aware Validation Depth
Task 5: Tests for unified validation runner with metrics
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Ensure auto-claude is in path for imports
sys.path.insert(0, "auto-claude")


class TestValidationMetrics:
    """Test ValidationMetrics dataclass."""

    def test_validation_metrics_creation(self):
        """Test creating validation metrics."""
        from integrations.mcp.complexity_aware_validation import ValidationMetrics

        metrics = ValidationMetrics(
            tier="simple",
            depth="smoke",
            test_count=4,
            passed_count=4,
            failed_count=0,
            duration_seconds=12.5,
            skipped_test_count=0,
            browser_count=1,
        )

        assert metrics.tier == "simple"
        assert metrics.depth == "smoke"
        assert metrics.test_count == 4
        assert metrics.passed_count == 4
        assert metrics.pass_rate == 1.0

    def test_validation_metrics_pass_rate(self):
        """Test pass rate calculation."""
        from integrations.mcp.complexity_aware_validation import ValidationMetrics

        metrics = ValidationMetrics(
            tier="standard",
            depth="feature",
            test_count=10,
            passed_count=8,
            failed_count=2,
            duration_seconds=60.0,
            skipped_test_count=0,
            browser_count=1,
        )

        assert metrics.pass_rate == 0.8

    def test_validation_metrics_zero_tests(self):
        """Test pass rate with zero tests."""
        from integrations.mcp.complexity_aware_validation import ValidationMetrics

        metrics = ValidationMetrics(
            tier="simple",
            depth="smoke",
            test_count=0,
            passed_count=0,
            failed_count=0,
            duration_seconds=0.0,
            skipped_test_count=0,
            browser_count=1,
        )

        # Should not divide by zero
        assert metrics.pass_rate == 1.0


@pytest.mark.asyncio
class TestComplexityAwareValidation:
    """Test complexity-aware validation execution."""

    async def test_simple_tier_runs_smoke_tests(self):
        """Test that simple tier runs smoke tests only."""
        from integrations.mcp.complexity_aware_validation import (
            run_complexity_aware_validation,
            ValidationMetrics,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        suite = E2ETestSuite(
            name="test",
            description="Test suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="tc-1", name="Test 1", description="Test", steps=[]),
            ],
        )

        def create_mock_client():
            client = MagicMock()
            client.connect = AsyncMock(return_value=True)
            client.launch_app = AsyncMock(return_value=True)
            client.assert_visible = AsyncMock(return_value=True)
            client._mcp_call = AsyncMock(return_value=None)
            client.close = AsyncMock()
            return client

        result, metrics = await run_complexity_aware_validation(
            tier="simple",
            suite=suite,
            project_path=Path("/tmp"),
            client_factory=create_mock_client,
        )

        assert metrics.depth == "smoke"
        # Smoke tests run 4 checks regardless of test suite
        assert metrics.test_count == 4

    async def test_standard_tier_runs_feature_tests(self):
        """Test that standard tier runs feature tests."""
        from integrations.mcp.complexity_aware_validation import (
            run_complexity_aware_validation,
            ValidationMetrics,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        suite = E2ETestSuite(
            name="test",
            description="Test suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="tc-1", name="Test 1", description="Test", steps=[]),
                E2ETestCase(id="tc-2", name="Test 2", description="Test", steps=[]),
            ],
        )

        def create_mock_client():
            client = MagicMock()
            client.connect = AsyncMock(return_value=True)
            client.launch_app = AsyncMock(return_value=True)
            client.close = AsyncMock()
            return client

        result, metrics = await run_complexity_aware_validation(
            tier="standard",
            suite=suite,
            project_path=Path("/tmp"),
            client_factory=create_mock_client,
            changed_files=[Path("src/auth/login.ts")],  # Simulate file change
        )

        assert metrics.depth == "feature"

    async def test_complex_tier_runs_full_suite(self):
        """Test that complex tier runs full suite."""
        from integrations.mcp.complexity_aware_validation import (
            run_complexity_aware_validation,
            ValidationMetrics,
        )
        from integrations.mcp.models import E2ETestSuite, E2ETestCase

        suite = E2ETestSuite(
            name="test",
            description="Test suite",
            app_url="http://localhost:3000",
            test_cases=[
                E2ETestCase(id="tc-1", name="Test 1", description="Test", steps=[]),
            ],
        )

        def create_mock_client():
            client = MagicMock()
            client.connect = AsyncMock(return_value=True)
            client.launch_app = AsyncMock(return_value=True)
            client.close = AsyncMock()
            return client

        result, metrics = await run_complexity_aware_validation(
            tier="complex",
            suite=suite,
            project_path=Path("/tmp"),
            client_factory=create_mock_client,
        )

        assert metrics.depth == "full"


class TestMetricsLogging:
    """Test metrics logging functionality."""

    def test_log_validation_metrics_format(self):
        """Test metrics are logged in correct format."""
        from integrations.mcp.complexity_aware_validation import (
            ValidationMetrics,
            log_validation_metrics,
        )
        import logging

        metrics = ValidationMetrics(
            tier="standard",
            depth="feature",
            test_count=15,
            passed_count=14,
            failed_count=1,
            duration_seconds=45.5,
            skipped_test_count=5,
            browser_count=2,
        )

        # Should not raise
        log_validation_metrics(metrics)

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        from integrations.mcp.complexity_aware_validation import ValidationMetrics

        metrics = ValidationMetrics(
            tier="complex",
            depth="full",
            test_count=100,
            passed_count=95,
            failed_count=5,
            duration_seconds=300.0,
            skipped_test_count=10,
            browser_count=3,
        )

        data = metrics.to_dict()

        assert data["tier"] == "complex"
        assert data["depth"] == "full"
        assert data["test_count"] == 100
        assert data["pass_rate"] == 0.95
        assert data["duration_seconds"] == 300.0
        assert data["browser_count"] == 3


class TestTimeOptimization:
    """Test validation time optimization (AC #4)."""

    def test_simple_tier_faster_than_standard(self):
        """Smoke tests should be faster than feature tests."""
        from integrations.mcp.validation_depth import (
            ValidationDepthConfig,
            get_timeout_for_depth,
            ValidationDepth,
        )

        config = ValidationDepthConfig()

        smoke_timeout = get_timeout_for_depth(ValidationDepth.SMOKE, config)
        feature_timeout = get_timeout_for_depth(ValidationDepth.FEATURE, config)

        assert smoke_timeout < feature_timeout

    def test_standard_tier_faster_than_complex(self):
        """Feature tests should be faster than full suite."""
        from integrations.mcp.validation_depth import (
            ValidationDepthConfig,
            get_timeout_for_depth,
            ValidationDepth,
        )

        config = ValidationDepthConfig()

        feature_timeout = get_timeout_for_depth(ValidationDepth.FEATURE, config)
        full_timeout = get_timeout_for_depth(ValidationDepth.FULL, config)

        assert feature_timeout < full_timeout
