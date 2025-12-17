"""Exception classes for framework adapters.

This module provides a shared exception hierarchy for all adapters,
ensuring consistent error handling across BMAD, Native, and future frameworks.

Story 1.1: Create Adapter Infrastructure (AC: #4 - proper imports)
Added based on code review: project-context.md error handling pattern
"""


class AdapterError(Exception):
    """Base exception for all adapter errors.

    All adapter-related exceptions should inherit from this class
    to enable consistent error handling in calling code.

    Example:
        ```python
        try:
            adapter.parse_work_units(path)
        except AdapterError as e:
            logger.error(f"Adapter failed: {e}")
        ```
    """

    pass


class ParseError(AdapterError):
    """File parsing failed.

    Raised when framework artifacts cannot be parsed due to:
    - Malformed YAML/JSON
    - Missing required fields
    - Invalid data types
    - Corrupt file content

    Attributes:
        file_path: Path to the file that failed to parse (if available)
        details: Additional error details
    """

    def __init__(self, message: str, file_path: str | None = None, details: str | None = None):
        self.file_path = file_path
        self.details = details
        full_message = message
        if file_path:
            full_message = f"{message} (file: {file_path})"
        if details:
            full_message = f"{full_message} - {details}"
        super().__init__(full_message)


class ValidationError(AdapterError):
    """Data validation failed.

    Raised when parsed data fails validation rules, such as:
    - Invalid status values
    - Missing required relationships
    - Inconsistent state
    """

    pass
