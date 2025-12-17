"""Test command configuration for different frameworks."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from .models import TestFramework


@dataclass
class TestCommand:
    """Test execution command configuration."""
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path | None = None
    timeout: int = 300


def get_test_command(
    framework: TestFramework,
    test_files: list[Path],
    project_path: Path,
) -> TestCommand:
    """Get test command for framework.

    Args:
        framework: Test framework
        test_files: List of test files
        project_path: Project root

    Returns:
        TestCommand configuration
    """
    if framework == TestFramework.PYTEST:
        return TestCommand(
            command=["pytest", "-v", "--tb=short"] + [str(f) for f in test_files],
            cwd=project_path,
        )

    if framework == TestFramework.GO_TEST:
        # Go tests are run per package
        packages = list({f.parent for f in test_files})
        pkg_args = []
        for p in packages:
            try:
                rel = p.relative_to(project_path)
                pkg_args.append(f"./{rel}/...")
            except ValueError:
                pkg_args.append(str(p))

        return TestCommand(
            command=["go", "test", "-v"] + pkg_args,
            env={"CGO_ENABLED": "0"},
            cwd=project_path,
        )

    if framework == TestFramework.CARGO_TEST:
        return TestCommand(
            command=["cargo", "test", "--", "--nocapture"],
            cwd=project_path,
        )

    if framework in (TestFramework.JEST, TestFramework.VITEST):
        return TestCommand(
            command=["npm", "test", "--"] + [str(f) for f in test_files],
            cwd=project_path,
        )

    # Unknown framework - try pytest as fallback
    return TestCommand(
        command=["pytest", "-v"] + [str(f) for f in test_files],
        cwd=project_path,
    )


def get_test_file_pattern(framework: TestFramework) -> str:
    """Get glob pattern for test files.

    Args:
        framework: Test framework

    Returns:
        Glob pattern string
    """
    patterns = {
        TestFramework.PYTEST: "**/test_*.py",
        TestFramework.JEST: "**/*.test.{ts,tsx,js,jsx}",
        TestFramework.VITEST: "**/*.test.{ts,tsx,js,jsx}",
        TestFramework.GO_TEST: "**/*_test.go",
        TestFramework.CARGO_TEST: "**/tests/**/*.rs",
    }
    return patterns.get(framework, "**/test_*.py")


def get_test_file_extension(framework: TestFramework) -> str:
    """Get file extension for test files.

    Args:
        framework: Test framework

    Returns:
        File extension (without dot)
    """
    extensions = {
        TestFramework.PYTEST: "py",
        TestFramework.JEST: "test.ts",
        TestFramework.VITEST: "test.ts",
        TestFramework.GO_TEST: "_test.go",
        TestFramework.CARGO_TEST: ".rs",
    }
    return extensions.get(framework, "py")
