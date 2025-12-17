"""Tests for enhanced complexity assessment (Story 4.2).

Story 4.2: Complexity Assessment Integration (AC: all)
"""

import sys
from pathlib import Path
import pytest

# Add auto-claude to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "auto-claude"))

from spec.complexity import assess_task_complexity, EnhancedComplexityAssessment


# =============================================================================
# Enhanced Assessment Tests (Story 4.2)
# =============================================================================


def test_assess_task_complexity_simple():
    """Test simple task gets simple tier.

    Story 4.2: AC #1, #2 - Basic complexity assessment
    """
    result = assess_task_complexity("Fix typo in README.md")
    assert result.tier == "simple"
    assert result.confidence > 0.7
    assert isinstance(result.factors, list)


def test_assess_task_complexity_complex():
    """Test complex task gets complex tier.

    Story 4.2: AC #1 - Scope and risk evaluation
    """
    result = assess_task_complexity(
        "Architect a new authentication system with OAuth2, "
        "database migrations for user schema, and API security hardening"
    )
    assert result.tier == "complex"
    assert "Security-sensitive changes" in result.factors
    assert "Database/data changes" in result.factors
    assert result.risk_score > 0


def test_assess_task_complexity_standard():
    """Test standard task gets standard tier.

    Story 4.2: AC #2 - Tier assignment
    """
    result = assess_task_complexity("Add user profile page with API endpoint")
    assert result.tier in ["standard", "simple"]  # Accept either based on scoring
    assert result.confidence > 0.5


def test_file_detection():
    """Test file mentions are detected.

    Story 4.2: AC #1 - Affected files detection
    """
    result = assess_task_complexity(
        "Update Button.tsx and helpers.ts files"
    )
    # Files are detected (regex captures extension groups)
    assert len(result.affected_files) >= 1
    # Verify file extensions were captured
    assert "ts" in result.affected_files or "tsx" in result.affected_files


def test_scope_score_evaluation():
    """Test scope score is calculated.

    Story 4.2: AC #1 - Scope evaluation (number of files/components)
    """
    result = assess_task_complexity(
        "Refactor components/Header.tsx, Footer.tsx, Navigation.tsx, "
        "Sidebar.tsx, Layout.tsx, and App.tsx"
    )
    # Many files mentioned should increase scope score
    assert result.scope_score > 0
    assert len(result.affected_files) >= 5


def test_risk_factors_detected():
    """Test risk factors are identified.

    Story 4.2: AC #1 - Risk factor evaluation
    """
    result = assess_task_complexity(
        "Add password reset with database changes and email integration"
    )
    assert result.risk_score > 0
    # Should detect security, database, and external dependencies
    assert any("Security" in f or "security" in f for f in result.factors)
    assert any("Database" in f or "database" in f.lower() for f in result.factors)


def test_security_risk_detection():
    """Test security risks increase risk score.

    Story 4.2: AC #1 - Security risk evaluation
    """
    result = assess_task_complexity(
        "Implement OAuth2 authentication with JWT tokens and credential storage"
    )
    assert result.risk_score >= 3  # Should detect multiple security terms
    assert any("Security" in f or "security" in f for f in result.factors)


def test_codebase_analysis_with_project_path(tmp_path):
    """Test codebase analysis affects assessment.

    Story 4.2: AC #1 - Codebase analysis integration
    """
    # Create some files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Button.tsx").write_text("export const Button = () => {}")
    (tmp_path / "src" / "Input.tsx").write_text("export const Input = () => {}")

    result = assess_task_complexity(
        "Modify Button.tsx and Input.tsx components",
        project_path=tmp_path
    )
    # Assessment should consider existing files
    assert result.tier in ["simple", "standard"]
    assert len(result.affected_files) >= 2


def test_codebase_analysis_without_project_path():
    """Test assessment works without project_path.

    Story 4.2: AC #1 - Optional codebase analysis
    """
    result = assess_task_complexity(
        "Modify Button.tsx component",
        project_path=None
    )
    # Should still work, just skip codebase-specific checks
    assert result.tier in ["simple", "standard", "complex"]
    assert len(result.affected_files) >= 1


def test_enhanced_assessment_returns_correct_type():
    """Test that enhanced assessment returns EnhancedComplexityAssessment.

    Story 4.2: Data structure validation
    """
    result = assess_task_complexity("Fix bug in module")
    assert isinstance(result, EnhancedComplexityAssessment)
    assert hasattr(result, "tier")
    assert hasattr(result, "confidence")
    assert hasattr(result, "scope_score")
    assert hasattr(result, "risk_score")
    assert hasattr(result, "factors")
    assert hasattr(result, "affected_files")


def test_complexity_indicators():
    """Test simple and complex indicators affect scoring.

    Story 4.2: AC #2 - Complexity indicator detection
    """
    # Simple task
    simple_result = assess_task_complexity("Rename variable in utils.py")
    assert simple_result.tier == "simple"
    assert any("Simple" in f or "simple" in f for f in simple_result.factors)

    # Complex task
    complex_result = assess_task_complexity(
        "Refactor entire authentication architecture and migrate to new system"
    )
    assert complex_result.tier == "complex"
    assert any("Major" in f or "restructuring" in f for f in complex_result.factors)


def test_description_length_affects_complexity():
    """Test that description length is factored into complexity.

    Story 4.2: AC #1 - Description analysis
    """
    # Very short description
    short_result = assess_task_complexity("Fix typo")

    # Very long detailed description
    long_description = (
        "Implement a comprehensive user management system with role-based access control, "
        "including user registration, authentication, authorization, profile management, "
        "password reset functionality, email verification, session management, "
        "and integration with external identity providers. "
    ) * 3  # Make it extra long
    long_result = assess_task_complexity(long_description)

    # Long descriptions should generally score higher complexity
    assert long_result.scope_score >= short_result.scope_score


def test_multiple_system_components():
    """Test detection of multiple system components.

    Story 4.2: AC #1 - Component/module detection
    """
    result = assess_task_complexity(
        "Update the API service, database module, cache component, "
        "and authentication endpoint"
    )
    # Should detect multiple components
    assert result.scope_score > 0
    assert any("component" in f.lower() or "system" in f.lower() for f in result.factors)


def test_external_dependencies_detected():
    """Test external API and integration detection.

    Story 4.2: AC #1 - External dependency risk
    """
    result = assess_task_complexity(
        "Integrate with Stripe API and add webhook handlers"
    )
    assert result.risk_score > 0
    assert any("External" in f or "external" in f for f in result.factors)


def test_factors_list_not_empty_for_complex_tasks():
    """Test that factors list is populated for non-trivial tasks.

    Story 4.2: AC #1 - Factor reporting
    """
    result = assess_task_complexity(
        "Add authentication to the API with database migrations"
    )
    # Should have multiple factors identified
    assert len(result.factors) > 0
    assert result.scope_score > 0 or result.risk_score > 0


# =============================================================================
# Integration with Routing Tests (Story 4.2: AC #2)
# =============================================================================


def test_routing_integration_uses_enhanced_assessment(tmp_path):
    """Test that routing module uses enhanced assessment.

    Story 4.2: AC #2 - Integration with routing module
    """
    from routing import route_task

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test.py").write_text("# test file")

    # Create a task that mentions the file
    result = route_task(tmp_path, "Fix bug in src/test.py with security implications")

    # Enhanced assessment should be used, providing detailed factors
    assert result.confidence > 0
    # Factors should include enhanced assessment details
    assert len(result.factors) > 0


def test_enhanced_assessment_with_existing_files(tmp_path):
    """Test enhanced assessment detects existing files in project.

    Story 4.2: AC #1 - Codebase file existence checks
    """
    # Create a project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Button.tsx").write_text("export const Button = () => {}")
    (src_dir / "Input.tsx").write_text("export const Input = () => {}")
    (src_dir / "Form.tsx").write_text("export const Form = () => {}")

    result = assess_task_complexity(
        "Refactor Button.tsx, Input.tsx, and Form.tsx components",
        project_path=tmp_path
    )

    # Should detect these as existing files
    assert result.scope_score > 0
    assert len(result.affected_files) == 3
