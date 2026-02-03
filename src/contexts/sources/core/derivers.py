"""
Sources Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.
These are the core of the Functional DDD pattern.

Note: For backward compatibility, the actual deriver definitions are in
projects/core/derivers.py. This module re-exports them for use in the
Sources bounded context. A future migration will move the definitions here.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations

# Re-export from projects for backward compatibility
# These derivers conceptually belong to Sources but are currently defined in Projects
from src.contexts.projects.core.derivers import (
    ProjectState,
    derive_add_source,
    derive_open_source,
    derive_remove_source,
    derive_update_source,
)

# Also export the state container used by source derivers
# Note: ProjectState contains existing_sources, path_exists, parent_writable
# which are needed for source operations

__all__ = [
    # State container
    "ProjectState",
    # Source derivers
    "derive_add_source",
    "derive_remove_source",
    "derive_open_source",
    "derive_update_source",
]
