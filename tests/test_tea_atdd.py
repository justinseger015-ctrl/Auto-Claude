"""Tests for TEA ATDD integration module."""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock


def test_atdd_module_imports():
    """Test that ATDD module can be imported."""
    from integrations.tea.atdd import (
        generate_atdd_tests,
        get_test_directory,
        get_extension,
        build_coder_context,
    )
    assert generate_atdd_tests is not None
    assert get_test_directory is not None


def test_get_test_directory_pytest(tmp_path):
    """Test pytest test directory."""
    from integrations.tea.atdd import get_test_directory
    from integrations.tea import TestFramework

    directory = get_test_directory(tmp_path, TestFramework.PYTEST)
    assert "tests/acceptance" in str(directory)


def test_get_test_directory_jest(tmp_path):
    """Test jest test directory."""
    from integrations.tea.atdd import get_test_directory
    from integrations.tea import TestFramework

    directory = get_test_directory(tmp_path, TestFramework.JEST)
    assert "__tests__/acceptance" in str(directory)


def test_get_test_directory_go(tmp_path):
    """Test Go test directory (same as source)."""
    from integrations.tea.atdd import get_test_directory
    from integrations.tea import TestFramework

    directory = get_test_directory(tmp_path, TestFramework.GO_TEST)
    assert directory == tmp_path  # Go tests in same directory


def test_get_test_directory_rust(tmp_path):
    """Test Rust test directory."""
    from integrations.tea.atdd import get_test_directory
    from integrations.tea import TestFramework

    directory = get_test_directory(tmp_path, TestFramework.CARGO_TEST)
    assert "tests" in str(directory)


def test_get_extension_pytest():
    """Test pytest extension."""
    from integrations.tea.atdd import get_extension
    from integrations.tea import TestFramework

    assert get_extension(TestFramework.PYTEST) == "py"


def test_get_extension_jest():
    """Test jest extension."""
    from integrations.tea.atdd import get_extension
    from integrations.tea import TestFramework

    assert get_extension(TestFramework.JEST) == "test.ts"


def test_get_extension_go():
    """Test Go extension."""
    from integrations.tea.atdd import get_extension
    from integrations.tea import TestFramework

    assert get_extension(TestFramework.GO_TEST) == "go"


def test_get_extension_rust():
    """Test Rust extension."""
    from integrations.tea.atdd import get_extension
    from integrations.tea import TestFramework

    assert get_extension(TestFramework.CARGO_TEST) == "rs"


@pytest.fixture
def sample_test_plan():
    """Create sample test plan for testing."""
    from integrations.tea import TestPlan, TestCase, TestFramework

    return TestPlan(
        story_id="1-2-test",
        framework=TestFramework.PYTEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Create Models",
                description="Test model creation",
                acceptance_criteria_id="ac-1",
                given="models module exists",
                when="importing WorkUnit",
                then="no error occurs",
                priority="high",
            )
        ],
        setup_instructions="# Setup code",
        teardown_instructions="# Teardown code",
        coverage_map={"ac-1": ["tc-1"]},
    )


@pytest.mark.asyncio
async def test_generate_atdd_creates_file(tmp_path, sample_test_plan):
    """Test ATDD generates test file."""
    from integrations.tea.atdd import generate_atdd_tests

    files = await generate_atdd_tests(sample_test_plan, tmp_path)

    assert len(files) == 1
    assert files[0].exists()
    assert "test_1_2_test" in files[0].name


@pytest.mark.asyncio
async def test_generated_tests_contain_cases(tmp_path, sample_test_plan):
    """Test generated file contains test cases."""
    from integrations.tea.atdd import generate_atdd_tests

    files = await generate_atdd_tests(sample_test_plan, tmp_path)

    content = files[0].read_text()
    assert "TestCreateModels" in content or "Create Models" in content
    assert "pytest.fail" in content  # Should fail initially


@pytest.mark.asyncio
async def test_generate_atdd_jest(tmp_path):
    """Test ATDD generates Jest test file."""
    from integrations.tea.atdd import generate_atdd_tests
    from integrations.tea import TestPlan, TestCase, TestFramework

    test_plan = TestPlan(
        story_id="2-1-jest",
        framework=TestFramework.JEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Login Test",
                description="Test user login",
                acceptance_criteria_id="ac-1",
                given="user on login page",
                when="entering credentials",
                then="redirected to dashboard",
                priority="high",
            )
        ],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={"ac-1": ["tc-1"]},
    )

    files = await generate_atdd_tests(test_plan, tmp_path)

    assert len(files) == 1
    content = files[0].read_text()
    assert "describe" in content
    assert "expect(false).toBe(true)" in content  # Intentional failure


@pytest.mark.asyncio
async def test_generate_atdd_go(tmp_path):
    """Test ATDD generates Go test file."""
    from integrations.tea.atdd import generate_atdd_tests
    from integrations.tea import TestPlan, TestCase, TestFramework

    test_plan = TestPlan(
        story_id="3-1-go",
        framework=TestFramework.GO_TEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Handler Test",
                description="Test HTTP handler",
                acceptance_criteria_id="ac-1",
                given="server running",
                when="request sent",
                then="response returned",
                priority="high",
            )
        ],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={"ac-1": ["tc-1"]},
    )

    files = await generate_atdd_tests(test_plan, tmp_path)

    assert len(files) == 1
    content = files[0].read_text()
    assert "func Test" in content
    assert 't.Fatal("Not implemented' in content


@pytest.mark.asyncio
async def test_generate_atdd_rust(tmp_path):
    """Test ATDD generates Rust test file."""
    from integrations.tea.atdd import generate_atdd_tests
    from integrations.tea import TestPlan, TestCase, TestFramework

    test_plan = TestPlan(
        story_id="4-1-rust",
        framework=TestFramework.CARGO_TEST,
        test_cases=[
            TestCase(
                id="tc-1",
                name="Parse Test",
                description="Test parser",
                acceptance_criteria_id="ac-1",
                given="input string",
                when="parsing",
                then="AST returned",
                priority="high",
            )
        ],
        setup_instructions="",
        teardown_instructions="",
        coverage_map={"ac-1": ["tc-1"]},
    )

    files = await generate_atdd_tests(test_plan, tmp_path)

    assert len(files) == 1
    content = files[0].read_text()
    assert "#[test]" in content
    assert 'panic!("Not implemented' in content


@pytest.mark.asyncio
async def test_build_coder_context(tmp_path, sample_test_plan):
    """Test coder context building."""
    from integrations.tea.atdd import generate_atdd_tests, build_coder_context

    files = await generate_atdd_tests(sample_test_plan, tmp_path)
    context = await build_coder_context(sample_test_plan.story_id, files)

    assert "story_id" in context
    assert "acceptance_tests" in context
    assert "instructions" in context
    assert len(context["acceptance_tests"]) == 1
