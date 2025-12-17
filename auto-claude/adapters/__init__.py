"""Framework adapters package.

This module provides the adapter factory function and exports for the
adapter pattern infrastructure. Each planning framework (BMAD, Native)
implements the FrameworkAdapter interface.

Story 1.1: Create Adapter Infrastructure (AC: #1, #3)
Updated in Story 1.2: Import models from models package
Updated in Story 2.5: Register BMADAdapter

Usage:
    ```python
    from adapters import get_adapter, FrameworkAdapter

    # Get a specific adapter
    adapter = get_adapter("bmad")

    # Use the adapter
    work_units = adapter.parse_work_units(project_path)
    ```
"""

from adapters.base import FrameworkAdapter
from adapters.glossary import GlossaryTerms, BMAD_GLOSSARY, NATIVE_GLOSSARY
from adapters.exceptions import AdapterError, ParseError, ValidationError
from models import WorkUnit, Task, ProjectStatus

__all__ = [
    # Core classes
    "FrameworkAdapter",
    "WorkUnit",
    "Task",
    "ProjectStatus",
    # Factory functions
    "get_adapter",
    "register_adapter",
    # Glossary types
    "GlossaryTerms",
    "BMAD_GLOSSARY",
    "NATIVE_GLOSSARY",
    # Exceptions
    "AdapterError",
    "ParseError",
    "ValidationError",
]

# Registry of adapter classes by framework name
_adapters: dict[str, type[FrameworkAdapter]] = {}


def register_adapter(name: str, adapter_class: type[FrameworkAdapter]) -> None:
    """Register an adapter class for a framework name.

    This function is used by concrete adapter implementations to register
    themselves with the factory. Typically called at module import time.

    Args:
        name: Framework identifier (e.g., 'bmad', 'native').
              Should be lowercase and alphanumeric.
        adapter_class: Class implementing FrameworkAdapter interface.

    Example:
        ```python
        class BMADAdapter(FrameworkAdapter):
            ...

        register_adapter("bmad", BMADAdapter)
        ```
    """
    _adapters[name] = adapter_class


def get_adapter(framework_name: str) -> FrameworkAdapter:
    """Get adapter instance for the specified framework.

    Returns a new instance of the adapter registered for the given
    framework name. Raises ValueError if no adapter is registered.

    Args:
        framework_name: Framework identifier (e.g., 'bmad', 'native').

    Returns:
        New instance of the appropriate FrameworkAdapter.

    Raises:
        ValueError: If framework_name is not registered.
                   Error message includes list of available frameworks.

    Example:
        ```python
        adapter = get_adapter("bmad")
        status = adapter.get_status(project_path)
        ```
    """
    if framework_name not in _adapters:
        available = list(_adapters.keys())
        raise ValueError(
            f"Unknown framework: {framework_name}. "
            f"Available: {available}"
        )
    return _adapters[framework_name]()


# =============================================================================
# Adapter Registration
# =============================================================================

# Register BMAD adapter
from adapters.bmad.adapter import BMADAdapter
register_adapter("bmad", BMADAdapter)
