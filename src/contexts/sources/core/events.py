"""
Sources Context: Domain Events

Immutable event records representing state changes in the sources domain.
Events are produced by Derivers and consumed by the Application layer.

Note: For backward compatibility, the actual event definitions are in
projects/core/events.py. This module re-exports them for use in the
Sources bounded context. A future migration will move the definitions here.
"""

from __future__ import annotations

# Re-export from projects for backward compatibility
# These events conceptually belong to Sources but are currently defined in Projects
from src.contexts.projects.core.events import (
    SourceAdded,
    SourceEvent,
    SourceMovedToFolder,
    SourceOpened,
    SourceRemoved,
    SourceRenamed,
    SourceStatusChanged,
    SourceUpdated,
)

__all__ = [
    # Source Events
    "SourceAdded",
    "SourceRemoved",
    "SourceRenamed",
    "SourceOpened",
    "SourceStatusChanged",
    "SourceUpdated",
    "SourceMovedToFolder",
    # Type Unions
    "SourceEvent",
]
