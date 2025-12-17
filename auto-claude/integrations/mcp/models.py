"""
Data models for E2E validation test suites.

This module defines the structure for E2E test cases and suites.
"""

from dataclasses import dataclass, field
from typing import Literal


ActionType = Literal[
    "click",
    "type",
    "navigate",
    "wait",
    "assert_visible",
    "assert_text",
    "select",
    "check",
    "submit",
    "wait_for_selector",
    "assert_position",
]


@dataclass
class E2ETestStep:
    """A single step in an E2E test case.

    Attributes:
        action: The type of action to perform (click, type, navigate, etc.)
        selector: CSS selector, XPath, or text selector for the target element
        value: Value for type/navigate actions, or option value for select
        expected: Expected value for assertions
        timeout: Optional timeout in ms for wait operations
        position: Expected position for position assertions (x, y, width, height)
    """

    action: ActionType
    selector: str | None = None
    value: str | None = None
    expected: str | None = None
    timeout: int | None = None
    position: dict | None = None


@dataclass
class E2ETestCase:
    """A single E2E test case.

    Attributes:
        id: Unique identifier for the test case
        name: Human-readable name for the test
        description: Detailed description of what the test validates
        steps: Ordered list of test steps to execute
        skip: If True, the test will be skipped during execution
        critical: If True, test is always run even in filtered suites
    """

    id: str
    name: str
    description: str
    steps: list[E2ETestStep] = field(default_factory=list)
    skip: bool = False
    critical: bool = False


@dataclass
class E2ETestSuite:
    """A collection of E2E test cases.

    Attributes:
        name: Name of the test suite
        description: Description of what the suite tests
        app_url: Base URL of the application under test
        test_cases: List of test cases in this suite
    """

    name: str
    description: str
    app_url: str
    test_cases: list[E2ETestCase] = field(default_factory=list)
