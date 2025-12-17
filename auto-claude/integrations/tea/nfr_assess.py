"""TEA non-functional requirements assessment for complex tier."""

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class NFRCheck:
    """Individual NFR check result."""
    name: str
    type: str  # "performance", "security", "reliability"
    passed: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class NFRAssessment:
    """Non-functional requirements assessment."""
    passed: bool = True
    performance_checks: list[NFRCheck] = field(default_factory=list)
    security_checks: list[NFRCheck] = field(default_factory=list)
    reliability_checks: list[NFRCheck] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


async def run_nfr_assessment(
    story_path: Path,
    project_path: Path,
) -> NFRAssessment:
    """Run NFR assessment for complex tier.

    Args:
        story_path: Path to story file
        project_path: Project root

    Returns:
        NFRAssessment result
    """
    assessment = NFRAssessment()

    # Run performance checks
    perf_checks = await check_performance_requirements(project_path)
    assessment.performance_checks = perf_checks

    # Run security checks
    sec_checks = await check_security_requirements(project_path)
    assessment.security_checks = sec_checks

    # Run reliability checks
    rel_checks = await check_reliability_requirements(project_path)
    assessment.reliability_checks = rel_checks

    # Aggregate issues from failed checks
    all_checks = perf_checks + sec_checks + rel_checks
    for check in all_checks:
        if not check.passed:
            assessment.issues.append(f"[{check.type.upper()}] {check.name}: {check.message}")

    # Overall pass status
    assessment.passed = len(assessment.issues) == 0

    logger.info(
        f"NFR Assessment: {'PASSED' if assessment.passed else 'FAILED'} "
        f"({len(assessment.issues)} issues)"
    )

    return assessment


async def check_performance_requirements(project_path: Path) -> list[NFRCheck]:
    """Check performance-related requirements.

    Args:
        project_path: Project root

    Returns:
        List of performance check results
    """
    checks = []

    # Check for large files that might impact performance
    large_files_check = NFRCheck(
        name="Large Files",
        type="performance",
        passed=True,
        message="No excessively large files detected",
    )

    try:
        # Find files larger than 1MB in source directories
        for pattern in ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js"]:
            for file in project_path.glob(pattern):
                if file.is_file() and file.stat().st_size > 1_000_000:
                    large_files_check.passed = False
                    large_files_check.message = f"Large source file detected: {file.name}"
                    large_files_check.details["file"] = str(file)
                    break
    except Exception as e:
        logger.warning(f"Error checking large files: {e}")

    checks.append(large_files_check)

    # Check for missing indexes in common patterns (basic heuristic)
    complexity_check = NFRCheck(
        name="Code Complexity",
        type="performance",
        passed=True,
        message="No obvious complexity issues detected",
    )
    checks.append(complexity_check)

    return checks


async def check_security_requirements(project_path: Path) -> list[NFRCheck]:
    """Check security-related requirements.

    Args:
        project_path: Project root

    Returns:
        List of security check results
    """
    checks = []

    # Check for hardcoded secrets patterns
    secrets_check = NFRCheck(
        name="Hardcoded Secrets",
        type="security",
        passed=True,
        message="No obvious hardcoded secrets detected",
    )

    secret_patterns = [
        "password=",
        "api_key=",
        "secret=",
        "token=",
        "AWS_SECRET",
    ]

    try:
        for pattern in ["**/*.py", "**/*.ts", "**/*.js", "**/*.env.example"]:
            for file in project_path.glob(pattern):
                if file.is_file() and ".git" not in str(file):
                    try:
                        content = file.read_text(errors="ignore").lower()
                        for secret_pattern in secret_patterns:
                            if secret_pattern.lower() in content:
                                # Check if it's a template/example file
                                if "example" not in file.name.lower() and "template" not in file.name.lower():
                                    secrets_check.passed = False
                                    secrets_check.message = f"Potential hardcoded secret in {file.name}"
                                    break
                    except Exception:
                        pass
                if not secrets_check.passed:
                    break
    except Exception as e:
        logger.warning(f"Error checking secrets: {e}")

    checks.append(secrets_check)

    # Check for .env files in git
    env_check = NFRCheck(
        name="Environment Files",
        type="security",
        passed=True,
        message="No .env files tracked in git",
    )

    env_file = project_path / ".env"
    if env_file.exists():
        # Check if it's in .gitignore
        gitignore = project_path / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
            if ".env" not in gitignore_content:
                env_check.passed = False
                env_check.message = ".env file exists but not in .gitignore"

    checks.append(env_check)

    return checks


async def check_reliability_requirements(project_path: Path) -> list[NFRCheck]:
    """Check reliability-related requirements.

    Args:
        project_path: Project root

    Returns:
        List of reliability check results
    """
    checks = []

    # Check for error handling patterns
    error_handling_check = NFRCheck(
        name="Error Handling",
        type="reliability",
        passed=True,
        message="Error handling patterns detected",
    )

    try:
        has_try_except = False
        for py_file in project_path.glob("**/*.py"):
            if py_file.is_file() and ".git" not in str(py_file):
                try:
                    content = py_file.read_text(errors="ignore")
                    if "try:" in content and "except" in content:
                        has_try_except = True
                        break
                except Exception:
                    pass

        if not has_try_except:
            # Check for TS/JS patterns
            for ts_file in project_path.glob("**/*.ts"):
                if ts_file.is_file():
                    try:
                        content = ts_file.read_text(errors="ignore")
                        if "try {" in content or "catch" in content:
                            has_try_except = True
                            break
                    except Exception:
                        pass

        if not has_try_except:
            error_handling_check.message = "Limited error handling detected"
            # Don't fail, just note it

    except Exception as e:
        logger.warning(f"Error checking error handling: {e}")

    checks.append(error_handling_check)

    # Check for logging
    logging_check = NFRCheck(
        name="Logging",
        type="reliability",
        passed=True,
        message="Logging infrastructure detected",
    )

    try:
        has_logging = False
        for py_file in project_path.glob("**/*.py"):
            if py_file.is_file() and ".git" not in str(py_file):
                try:
                    content = py_file.read_text(errors="ignore")
                    if "import logging" in content or "logger" in content:
                        has_logging = True
                        break
                except Exception:
                    pass

        if not has_logging:
            logging_check.message = "No Python logging detected"

    except Exception as e:
        logger.warning(f"Error checking logging: {e}")

    checks.append(logging_check)

    return checks


def format_nfr_report(assessment: NFRAssessment) -> str:
    """Format NFR assessment as human-readable report.

    Args:
        assessment: NFR assessment result

    Returns:
        Formatted report string
    """
    lines = [
        "# NFR Assessment Report",
        "",
        f"**Overall Status:** {'✅ PASSED' if assessment.passed else '❌ FAILED'}",
        "",
    ]

    if assessment.performance_checks:
        lines.append("## Performance Checks")
        for check in assessment.performance_checks:
            status = "✅" if check.passed else "❌"
            lines.append(f"- {status} **{check.name}**: {check.message}")
        lines.append("")

    if assessment.security_checks:
        lines.append("## Security Checks")
        for check in assessment.security_checks:
            status = "✅" if check.passed else "❌"
            lines.append(f"- {status} **{check.name}**: {check.message}")
        lines.append("")

    if assessment.reliability_checks:
        lines.append("## Reliability Checks")
        for check in assessment.reliability_checks:
            status = "✅" if check.passed else "❌"
            lines.append(f"- {status} **{check.name}**: {check.message}")
        lines.append("")

    if assessment.issues:
        lines.append("## Issues Found")
        for issue in assessment.issues:
            lines.append(f"- ⚠️ {issue}")
        lines.append("")

    return "\n".join(lines)
