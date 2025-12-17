"""Tests for TEA integration module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json


def test_tea_module_imports():
    """Test that TEA integration module can be imported."""
    from integrations.tea import (
        TestFramework,
        TestCase,
        TestPlan,
    )
    assert TestFramework is not None
    assert TestCase is not None
    assert TestPlan is not None


def test_test_framework_enum():
    """Test TestFramework enum has expected values."""
    from integrations.tea import TestFramework

    assert TestFramework.PYTEST.value == "pytest"
    assert TestFramework.JEST.value == "jest"
    assert TestFramework.VITEST.value == "vitest"
    assert TestFramework.CARGO_TEST.value == "cargo test"
    assert TestFramework.GO_TEST.value == "go test"
    assert TestFramework.UNKNOWN.value == "unknown"


def test_test_case_dataclass():
    """Test TestCase dataclass structure."""
    from integrations.tea import TestCase

    test_case = TestCase(
        id="tc-1",
        name="Test login",
        description="Test user login functionality",
        acceptance_criteria_id="ac-1",
        given="user is on login page",
        when="user enters valid credentials",
        then="user is redirected to dashboard",
        priority="high"
    )

    assert test_case.id == "tc-1"
    assert test_case.priority == "high"
    assert test_case.acceptance_criteria_id == "ac-1"


def test_test_plan_dataclass():
    """Test TestPlan dataclass structure."""
    from integrations.tea import TestPlan, TestCase, TestFramework

    test_case = TestCase(
        id="tc-1",
        name="Test login",
        description="Test user login functionality",
        acceptance_criteria_id="ac-1",
        given="user is on login page",
        when="user enters valid credentials",
        then="user is redirected to dashboard",
        priority="high"
    )

    test_plan = TestPlan(
        story_id="5-1-test",
        framework=TestFramework.PYTEST,
        test_cases=[test_case],
        setup_instructions="Install pytest",
        teardown_instructions="Clean test data",
        coverage_map={"ac-1": ["tc-1"]}
    )

    assert test_plan.story_id == "5-1-test"
    assert test_plan.framework == TestFramework.PYTEST
    assert len(test_plan.test_cases) == 1
    assert "ac-1" in test_plan.coverage_map


def test_extract_acceptance_criteria():
    """Test AC extraction from story content."""
    from integrations.tea.test_design import extract_acceptance_criteria

    story = """
# Story 1.1

## Acceptance Criteria

1. **Given** a user is logged in
   **When** they click logout
   **Then** they are redirected to login page

2. **Given** a user is on the home page
   **When** they click settings
   **Then** settings modal opens
"""
    criteria = extract_acceptance_criteria(story)

    assert len(criteria) == 2
    assert criteria[0]["id"] == "ac-1"
    assert "logged in" in criteria[0]["given"]
    assert "click logout" in criteria[0]["when"]
    assert "redirected to login page" in criteria[0]["then"]


def test_detect_pytest(tmp_path):
    """Test pytest detection."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    (tmp_path / "pytest.ini").write_text("[pytest]")
    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.PYTEST


def test_detect_jest(tmp_path):
    """Test jest detection."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    (tmp_path / "package.json").write_text(json.dumps({
        "devDependencies": {"jest": "^29.0.0"}
    }))
    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.JEST


def test_detect_vitest_over_jest(tmp_path):
    """Test vitest is preferred when both present."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    (tmp_path / "package.json").write_text(json.dumps({
        "devDependencies": {"jest": "^29.0.0", "vitest": "^1.0.0"}
    }))
    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.VITEST


def test_detect_cargo_test(tmp_path):
    """Test Cargo test detection for Rust."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'")
    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.CARGO_TEST


def test_detect_go_test(tmp_path):
    """Test Go test detection."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    (tmp_path / "main_test.go").write_text("package main")
    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.GO_TEST


def test_detect_unknown_framework(tmp_path):
    """Test unknown framework detection."""
    from integrations.tea.framework_detector import detect_test_framework
    from integrations.tea import TestFramework

    framework = detect_test_framework(tmp_path)
    assert framework == TestFramework.UNKNOWN


@pytest.mark.asyncio
async def test_invoke_tea_test_design(tmp_path):
    """Test TEA workflow is invoked correctly."""
    from integrations.tea.test_design import invoke_tea_test_design
    from integrations.tea import TestPlan, TestFramework

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("""
# Story 1.1: Test

## Acceptance Criteria

1. **Given** X **When** Y **Then** Z
""")

    # Create pytest.ini to trigger framework detection
    (tmp_path / "pytest.ini").write_text("[pytest]")

    # Mock the TEA agent runner using unittest.mock.patch
    with patch('integrations.tea.test_design.run_tea_agent',
               new=AsyncMock(return_value='{"test_cases": [], "setup_instructions": "", "teardown_instructions": ""}')):
        with patch('integrations.tea.test_design.store_test_plan',
                   new=AsyncMock()):
            plan = await invoke_tea_test_design(story_path, tmp_path)
            assert plan is not None
            assert plan.story_id == "1-1-test"
            assert plan.framework == TestFramework.PYTEST
