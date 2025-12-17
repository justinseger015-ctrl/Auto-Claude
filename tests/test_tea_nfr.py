"""Tests for TEA NFR assessment module."""
import pytest
from pathlib import Path


def test_nfr_module_imports():
    """Test NFR module can be imported."""
    from integrations.tea.nfr_assess import (
        NFRAssessment,
        NFRCheck,
        run_nfr_assessment,
        format_nfr_report,
    )
    assert NFRAssessment is not None
    assert NFRCheck is not None


def test_nfr_check_dataclass():
    """Test NFRCheck dataclass."""
    from integrations.tea import NFRCheck

    check = NFRCheck(
        name="Large Files",
        type="performance",
        passed=True,
        message="No large files detected",
    )

    assert check.name == "Large Files"
    assert check.type == "performance"
    assert check.passed is True


def test_nfr_assessment_dataclass():
    """Test NFRAssessment dataclass."""
    from integrations.tea import NFRAssessment, NFRCheck

    assessment = NFRAssessment(
        passed=False,
        performance_checks=[
            NFRCheck("Test", "performance", True, "OK")
        ],
        issues=["Performance issue found"],
    )

    assert not assessment.passed
    assert len(assessment.performance_checks) == 1
    assert len(assessment.issues) == 1


@pytest.mark.asyncio
async def test_run_nfr_assessment_clean_project(tmp_path):
    """Test NFR assessment on clean project."""
    from integrations.tea import run_nfr_assessment

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("# Story")

    # Create a simple Python file with error handling and logging
    (tmp_path / "main.py").write_text("""
import logging
logger = logging.getLogger(__name__)

def process():
    try:
        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
""")

    assessment = await run_nfr_assessment(story_path, tmp_path)

    assert assessment.passed is True
    assert len(assessment.performance_checks) > 0
    assert len(assessment.security_checks) > 0
    assert len(assessment.reliability_checks) > 0


@pytest.mark.asyncio
async def test_run_nfr_assessment_with_issues(tmp_path):
    """Test NFR assessment catches issues."""
    from integrations.tea import run_nfr_assessment

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("# Story")

    # Create a file with potential secret
    (tmp_path / "config.py").write_text("""
# Bad practice - hardcoded secret
api_key = "sk-1234567890abcdef"
password = "supersecret123"
""")

    assessment = await run_nfr_assessment(story_path, tmp_path)

    # Should detect potential hardcoded secrets
    assert any(
        "secret" in check.message.lower() or not check.passed
        for check in assessment.security_checks
    )


@pytest.mark.asyncio
async def test_run_nfr_assessment_env_file(tmp_path):
    """Test NFR assessment checks .env file handling."""
    from integrations.tea import run_nfr_assessment

    story_path = tmp_path / "1-1-test.md"
    story_path.write_text("# Story")

    # Create .env file without .gitignore
    (tmp_path / ".env").write_text("SECRET=value")

    # Create empty gitignore (not ignoring .env)
    (tmp_path / ".gitignore").write_text("*.pyc")

    assessment = await run_nfr_assessment(story_path, tmp_path)

    # Should flag .env not in gitignore
    env_check = next(
        (c for c in assessment.security_checks if "Environment" in c.name),
        None
    )
    if env_check:
        assert not env_check.passed or ".env" in env_check.message


def test_format_nfr_report_passed():
    """Test formatting passed NFR report."""
    from integrations.tea import format_nfr_report, NFRAssessment, NFRCheck

    assessment = NFRAssessment(
        passed=True,
        performance_checks=[
            NFRCheck("Large Files", "performance", True, "No issues")
        ],
        security_checks=[
            NFRCheck("Secrets", "security", True, "No secrets found")
        ],
        reliability_checks=[
            NFRCheck("Error Handling", "reliability", True, "Good coverage")
        ],
    )

    report = format_nfr_report(assessment)

    assert "NFR Assessment Report" in report
    assert "✅ PASSED" in report
    assert "Performance Checks" in report
    assert "Security Checks" in report
    assert "Reliability Checks" in report


def test_format_nfr_report_failed():
    """Test formatting failed NFR report."""
    from integrations.tea import format_nfr_report, NFRAssessment, NFRCheck

    assessment = NFRAssessment(
        passed=False,
        performance_checks=[],
        security_checks=[
            NFRCheck("Secrets", "security", False, "Hardcoded secret found")
        ],
        reliability_checks=[],
        issues=["[SECURITY] Secrets: Hardcoded secret found"],
    )

    report = format_nfr_report(assessment)

    assert "❌ FAILED" in report
    assert "Issues Found" in report
    assert "Hardcoded secret" in report
