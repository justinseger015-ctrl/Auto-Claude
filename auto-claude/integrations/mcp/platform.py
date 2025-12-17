"""
Cross-platform utilities for Electron MCP integration.

This module provides Electron project detection and platform-specific
path resolution utilities.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_electron_project(project_path: Path) -> bool:
    """Detect if project is an Electron application.

    Checks for Electron in dependencies or devDependencies of package.json.

    Args:
        project_path: Project root path.

    Returns:
        True if Electron project detected, False otherwise.
    """
    package_json = project_path / "package.json"

    if not package_json.exists():
        return False

    try:
        pkg = json.loads(package_json.read_text())

        # Check dependencies and devDependencies
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "electron" in deps:
            return True

        # Check main field points to electron entry
        main = pkg.get("main", "")
        if "electron" in main.lower():
            return True

        return False

    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {package_json}")
        return False


def get_electron_entry(project_path: Path) -> Path | None:
    """Get Electron app entry point.

    Reads the main field from package.json to determine the entry point.

    Args:
        project_path: Project root path.

    Returns:
        Path to main entry file or None if not found.
    """
    package_json = project_path / "package.json"

    if not package_json.exists():
        return None

    try:
        pkg = json.loads(package_json.read_text())
        main = pkg.get("main", "index.js")
        entry_path = project_path / main

        if entry_path.exists():
            return entry_path

        return None

    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {package_json}")
        return None
