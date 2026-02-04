"""
Sources Context: Failure Events

Re-exports source failure events from the projects context.
Source failure events are defined in projects/core/failure_events.py
as sources are a core part of project management.
"""

from __future__ import annotations

from src.contexts.projects.core.failure_events import (
    SourceFailureEvent,
    SourceNotAdded,
    SourceNotMoved,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)

__all__ = [
    # Source Failure Events
    "SourceNotAdded",
    "SourceNotRemoved",
    "SourceNotOpened",
    "SourceNotUpdated",
    "SourceNotMoved",
    # Type Union
    "SourceFailureEvent",
]
