"""
DEPRECATED: Use src.contexts.projects.core.failure_events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.projects.core.failure_events import (
    FolderFailureEvent,
    # Folder Failure Events
    FolderNotCreated,
    FolderNotDeleted,
    FolderNotRenamed,
    # Type Unions
    ProjectFailureEvent,
    # Project Failure Events
    ProjectNotCreated,
    ProjectNotOpened,
    ProjectsContextFailureEvent,
    SourceFailureEvent,
    # Source Failure Events
    SourceNotAdded,
    SourceNotMoved,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)

__all__ = [
    # Project Failure Events
    "ProjectNotCreated",
    "ProjectNotOpened",
    # Source Failure Events
    "SourceNotAdded",
    "SourceNotRemoved",
    "SourceNotOpened",
    "SourceNotUpdated",
    # Folder Failure Events
    "FolderNotCreated",
    "FolderNotRenamed",
    "FolderNotDeleted",
    "SourceNotMoved",
    # Type Unions
    "ProjectFailureEvent",
    "SourceFailureEvent",
    "FolderFailureEvent",
    "ProjectsContextFailureEvent",
]
