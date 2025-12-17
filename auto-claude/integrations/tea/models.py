"""TEA data models for test plans and test cases."""

from dataclasses import dataclass, field
from enum import Enum


class TestFramework(Enum):
    """Supported test frameworks."""

    PYTEST = "pytest"
    JEST = "jest"
    VITEST = "vitest"
    CARGO_TEST = "cargo test"
    GO_TEST = "go test"
    UNKNOWN = "unknown"


@dataclass
class TestCase:
    """Individual test case from TEA."""

    id: str
    name: str
    description: str
    acceptance_criteria_id: str  # Maps to AC
    given: str
    when: str
    then: str
    priority: str  # "high", "medium", "low"


@dataclass
class TestPlan:
    """TEA-generated test plan."""

    story_id: str
    framework: TestFramework
    test_cases: list[TestCase]
    setup_instructions: str
    teardown_instructions: str
    coverage_map: dict[str, list[str]]  # AC_id -> [test_case_ids]
