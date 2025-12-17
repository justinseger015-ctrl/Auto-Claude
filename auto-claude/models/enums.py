"""Unified status enumeration for cross-framework compatibility.

This module provides the UnifiedStatus enum that normalizes status values
across different planning frameworks (BMAD Method, Native track).

Story 1.2: Create Unified Data Model (AC: #2)
"""

from enum import Enum


class UnifiedStatus(Enum):
    """Unified status values for cross-framework compatibility.

    Maps framework-specific statuses to a common set of values:
    - BMAD: backlog, ready-for-dev, in-progress, review, blocked, done
    - Native: pending, in_progress, ai_review, human_review, done, failed

    The unified statuses provide a consistent interface for the UI layer
    regardless of which planning framework is active.

    Story 4.4: Added NEEDS_HUMAN_REVIEW for QA loop escalation
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_HUMAN_REVIEW = "needs_human_review"  # Story 4.4: AC #1
