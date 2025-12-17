"""TEA (Test Engineering Agent) integration module.

This module integrates the BMAD TEA agent for test plan generation
and acceptance test-driven development (ATDD).
"""

from .models import (
    TestFramework,
    TestCase,
    TestPlan,
)

from .test_depth import (
    TestDepth,
    TestDepthConfig,
    get_test_depth_for_tier,
    load_test_depth_config,
    save_test_depth_config,
)

from .framework_detector import detect_test_framework

from .test_design import (
    invoke_tea_test_design,
    extract_acceptance_criteria,
    build_test_design_prompt,
)

from .atdd import (
    generate_atdd_tests,
    get_test_directory,
    get_extension,
    build_coder_context,
)

from .trace import (
    TraceabilityMatrix,
    generate_traceability_matrix,
    format_traceability_report,
)

from .nfr_assess import (
    NFRAssessment,
    NFRCheck,
    run_nfr_assessment,
    format_nfr_report,
)

from .orchestrator import (
    TEAResult,
    run_tea_for_tier,
    should_run_tea,
    get_tea_workflows_for_tier,
    format_tea_summary,
)

from .test_runner import (
    TestOutcome,
    TestCaseResult,
    TestRunResult,
    run_tea_tests,
    build_fix_context,
    extract_test_failures,
)

from .commands import (
    TestCommand,
    get_test_command,
    get_test_file_pattern,
    get_test_file_extension,
)

__all__ = [
    # Models
    "TestFramework",
    "TestCase",
    "TestPlan",
    # Test depth
    "TestDepth",
    "TestDepthConfig",
    "get_test_depth_for_tier",
    "load_test_depth_config",
    "save_test_depth_config",
    # Framework detection
    "detect_test_framework",
    # Test design
    "invoke_tea_test_design",
    "extract_acceptance_criteria",
    "build_test_design_prompt",
    # ATDD
    "generate_atdd_tests",
    "get_test_directory",
    "get_extension",
    "build_coder_context",
    # Trace
    "TraceabilityMatrix",
    "generate_traceability_matrix",
    "format_traceability_report",
    # NFR
    "NFRAssessment",
    "NFRCheck",
    "run_nfr_assessment",
    "format_nfr_report",
    # Orchestrator
    "TEAResult",
    "run_tea_for_tier",
    "should_run_tea",
    "get_tea_workflows_for_tier",
    "format_tea_summary",
    # Test runner
    "TestOutcome",
    "TestCaseResult",
    "TestRunResult",
    "run_tea_tests",
    "build_fix_context",
    "extract_test_failures",
    # Commands
    "TestCommand",
    "get_test_command",
    "get_test_file_pattern",
    "get_test_file_extension",
]
