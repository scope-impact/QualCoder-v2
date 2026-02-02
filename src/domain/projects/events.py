"""
DEPRECATED: Use src.contexts.projects.core.events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.projects.core.events import (
    FolderCreated,
    FolderDeleted,
    FolderEvent,
    FolderRenamed,
    NavigatedToSegment,
    NavigationEvent,
    ProjectClosed,
    ProjectCreated,
    ProjectEvent,
    ProjectOpened,
    ProjectRenamed,
    ScreenChanged,
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
    # Project Events
    "ProjectCreated",
    "ProjectOpened",
    "ProjectClosed",
    "ProjectRenamed",
    # Source Events
    "SourceAdded",
    "SourceRemoved",
    "SourceRenamed",
    "SourceOpened",
    "SourceStatusChanged",
    "SourceUpdated",
    # Folder Events
    "FolderCreated",
    "FolderRenamed",
    "FolderDeleted",
    "SourceMovedToFolder",
    # Navigation Events
    "ScreenChanged",
    "NavigatedToSegment",
    # Type Unions
    "ProjectEvent",
    "SourceEvent",
    "FolderEvent",
    "NavigationEvent",
]
