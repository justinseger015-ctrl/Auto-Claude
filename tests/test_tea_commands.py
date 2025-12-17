"""Tests for TEA commands module."""
import pytest
from pathlib import Path


def test_commands_module_imports():
    """Test commands module can be imported."""
    from integrations.tea.commands import (
        TestCommand,
        get_test_command,
        get_test_file_pattern,
        get_test_file_extension,
    )
    assert TestCommand is not None
    assert get_test_command is not None


def test_test_command_dataclass():
    """Test TestCommand dataclass."""
    from integrations.tea import TestCommand

    cmd = TestCommand(
        command=["pytest", "-v", "test_file.py"],
        env={"PYTHONPATH": "."},
        cwd=Path("/project"),
        timeout=60,
    )

    assert cmd.command == ["pytest", "-v", "test_file.py"]
    assert cmd.env == {"PYTHONPATH": "."}
    assert cmd.timeout == 60


def test_get_test_command_pytest(tmp_path):
    """Test pytest command generation."""
    from integrations.tea import get_test_command, TestFramework

    test_file = tmp_path / "test_example.py"
    cmd = get_test_command(TestFramework.PYTEST, [test_file], tmp_path)

    assert cmd.command[0] == "pytest"
    assert "-v" in cmd.command
    assert str(test_file) in cmd.command
    assert cmd.cwd == tmp_path


def test_get_test_command_jest(tmp_path):
    """Test Jest command generation."""
    from integrations.tea import get_test_command, TestFramework

    test_file = tmp_path / "example.test.ts"
    cmd = get_test_command(TestFramework.JEST, [test_file], tmp_path)

    assert cmd.command[0] == "npm"
    assert "test" in cmd.command
    assert str(test_file) in cmd.command


def test_get_test_command_vitest(tmp_path):
    """Test Vitest command generation."""
    from integrations.tea import get_test_command, TestFramework

    test_file = tmp_path / "example.test.ts"
    cmd = get_test_command(TestFramework.VITEST, [test_file], tmp_path)

    assert cmd.command[0] == "npm"
    assert "test" in cmd.command


def test_get_test_command_go(tmp_path):
    """Test Go command generation."""
    from integrations.tea import get_test_command, TestFramework

    test_file = tmp_path / "example_test.go"
    cmd = get_test_command(TestFramework.GO_TEST, [test_file], tmp_path)

    assert cmd.command[0] == "go"
    assert "test" in cmd.command
    assert cmd.env.get("CGO_ENABLED") == "0"


def test_get_test_command_cargo(tmp_path):
    """Test Cargo command generation."""
    from integrations.tea import get_test_command, TestFramework

    test_file = tmp_path / "tests" / "integration_test.rs"
    cmd = get_test_command(TestFramework.CARGO_TEST, [test_file], tmp_path)

    assert cmd.command[0] == "cargo"
    assert "test" in cmd.command


def test_get_test_file_pattern_pytest():
    """Test pytest file pattern."""
    from integrations.tea import get_test_file_pattern, TestFramework

    pattern = get_test_file_pattern(TestFramework.PYTEST)
    assert "test_*.py" in pattern


def test_get_test_file_pattern_jest():
    """Test Jest file pattern."""
    from integrations.tea import get_test_file_pattern, TestFramework

    pattern = get_test_file_pattern(TestFramework.JEST)
    assert ".test." in pattern


def test_get_test_file_pattern_go():
    """Test Go file pattern."""
    from integrations.tea import get_test_file_pattern, TestFramework

    pattern = get_test_file_pattern(TestFramework.GO_TEST)
    assert "_test.go" in pattern


def test_get_test_file_pattern_rust():
    """Test Rust file pattern."""
    from integrations.tea import get_test_file_pattern, TestFramework

    pattern = get_test_file_pattern(TestFramework.CARGO_TEST)
    assert ".rs" in pattern


def test_get_test_file_extension_pytest():
    """Test pytest file extension."""
    from integrations.tea import get_test_file_extension, TestFramework

    ext = get_test_file_extension(TestFramework.PYTEST)
    assert ext == "py"


def test_get_test_file_extension_jest():
    """Test Jest file extension."""
    from integrations.tea import get_test_file_extension, TestFramework

    ext = get_test_file_extension(TestFramework.JEST)
    assert "test.ts" in ext


def test_get_test_file_extension_go():
    """Test Go file extension."""
    from integrations.tea import get_test_file_extension, TestFramework

    ext = get_test_file_extension(TestFramework.GO_TEST)
    assert "go" in ext


def test_get_test_file_extension_rust():
    """Test Rust file extension."""
    from integrations.tea import get_test_file_extension, TestFramework

    ext = get_test_file_extension(TestFramework.CARGO_TEST)
    assert "rs" in ext
