"""
Folders Context: Core Domain Layer

Entities, events, derivers, and invariants for folder management.
"""

from src.contexts.folders.core.commands import (
    CreateFolderCommand,
    DeleteFolderCommand,
    MoveSourceToFolderCommand,
    RenameFolderCommand,
)
from src.contexts.folders.core.derivers import (
    FolderState,
    derive_create_folder,
    derive_delete_folder,
    derive_move_source_to_folder,
    derive_rename_folder,
)
from src.contexts.folders.core.entities import Folder
from src.contexts.folders.core.events import (
    FolderCreated,
    FolderDeleted,
    FolderRenamed,
    SourceMovedToFolder,
)
from src.contexts.folders.core.failure_events import (
    FolderNotCreated,
    FolderNotDeleted,
    FolderNotRenamed,
    SourceNotMoved,
)
from src.contexts.folders.core.invariants import (
    is_folder_empty,
    is_folder_name_unique,
    is_valid_folder_name,
    would_create_cycle,
)

__all__ = [
    # Entities
    "Folder",
    # Commands
    "CreateFolderCommand",
    "DeleteFolderCommand",
    "MoveSourceToFolderCommand",
    "RenameFolderCommand",
    # Events
    "FolderCreated",
    "FolderDeleted",
    "FolderRenamed",
    "SourceMovedToFolder",
    # Failure Events
    "FolderNotCreated",
    "FolderNotDeleted",
    "FolderNotRenamed",
    "SourceNotMoved",
    # Derivers
    "FolderState",
    "derive_create_folder",
    "derive_delete_folder",
    "derive_move_source_to_folder",
    "derive_rename_folder",
    # Invariants
    "is_folder_empty",
    "is_folder_name_unique",
    "is_valid_folder_name",
    "would_create_cycle",
]
