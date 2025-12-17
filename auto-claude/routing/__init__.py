"""Two-stage routing system for framework and complexity-based task routing.

Story 4.1: Two-Stage Routing Implementation

This module implements ADR-004's two-stage routing:
- Stage 1: Framework Selection (BMAD vs Native)
- Stage 2: Complexity Routing (within framework)
"""

from .router import (
    Framework,
    BMADTier,
    NativeTier,
    RoutingResult,
    route_task,
    get_active_framework,
    route_bmad_task,
    route_native_task,
)

__all__ = [
    "Framework",
    "BMADTier",
    "NativeTier",
    "RoutingResult",
    "route_task",
    "get_active_framework",
    "route_bmad_task",
    "route_native_task",
]
