"""
Sources Context: Domain Events

Re-exports source events from the projects context.
Source events are defined in projects/core/events.py as sources
are a core part of project management.
"""

from __future__ import annotations

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
