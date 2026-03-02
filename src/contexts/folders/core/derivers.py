"""
Folders Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations

from dataclasses import dataclass

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
)
from src.contexts.projects.core.entities import Source
from src.shared.common.types import FolderId, SourceId

# ============================================================
# State Containers
# ============================================================


@dataclass(frozen=True)
class FolderState:
    """
    State container for folder context derivers.

    Contains all the context needed to validate folder operations.
    """

    existing_folders: tuple[Folder, ...] = ()
    existing_sources: tuple[Source, ...] = ()


# ============================================================
# Folder Derivers
# ============================================================


def derive_create_folder(
    name: str,
    parent_id: FolderId | None,
    state: FolderState,
) -> FolderCreated | FolderNotCreated:
    """
    Derive a FolderCreated event or failure event.

    Args:
        name: Name for the new folder
        parent_id: Parent folder ID (None for root level)
        state: Current folder state

    Returns:
        FolderCreated event or FolderNotCreated failure event
    """
    if not is_valid_folder_name(name):
        return FolderNotCreated.invalid_name(name)

    # Validate parent folder exists if specified
    if parent_id is not None:
        parent_exists = any(f.id == parent_id for f in state.existing_folders)
        if not parent_exists:
            return FolderNotCreated.parent_not_found(name, parent_id)

    if not is_folder_name_unique(name, parent_id, state.existing_folders):
        return FolderNotCreated.duplicate_name(name, parent_id)

    folder_id = FolderId.new()

    return FolderCreated.create(
        folder_id=folder_id,
        name=name,
        parent_id=parent_id,
    )


def derive_rename_folder(
    folder_id: FolderId,
    new_name: str,
    state: FolderState,
) -> FolderRenamed | FolderNotRenamed:
    """
    Derive a FolderRenamed event or failure event.

    Args:
        folder_id: ID of the folder to rename
        new_name: New name for the folder
        state: Current folder state

    Returns:
        FolderRenamed event or FolderNotRenamed failure event
    """
    folder = next((f for f in state.existing_folders if f.id == folder_id), None)

    if folder is None:
        return FolderNotRenamed.not_found(folder_id)

    if not is_valid_folder_name(new_name):
        return FolderNotRenamed.invalid_name(folder_id, new_name)

    # Check uniqueness among siblings (excluding self)
    siblings = tuple(f for f in state.existing_folders if f.id != folder_id)
    if not is_folder_name_unique(new_name, folder.parent_id, siblings):
        return FolderNotRenamed.duplicate_name(folder_id, new_name)

    return FolderRenamed.create(
        folder_id=folder_id,
        old_name=folder.name,
        new_name=new_name,
    )


def derive_delete_folder(
    folder_id: FolderId,
    state: FolderState,
) -> FolderDeleted | FolderNotDeleted:
    """
    Derive a FolderDeleted event or failure event.

    Args:
        folder_id: ID of the folder to delete
        state: Current folder state

    Returns:
        FolderDeleted event or FolderNotDeleted failure event
    """
    folder = next((f for f in state.existing_folders if f.id == folder_id), None)

    if folder is None:
        return FolderNotDeleted.not_found(folder_id)

    if not is_folder_empty(folder_id, state.existing_sources):
        source_count = sum(
            1 for s in state.existing_sources if s.folder_id == folder_id
        )
        return FolderNotDeleted.not_empty(folder_id, source_count)

    return FolderDeleted.create(
        folder_id=folder_id,
        name=folder.name,
    )


def derive_move_source_to_folder(
    source_id: SourceId,
    folder_id: FolderId | None,
    state: FolderState,
) -> SourceMovedToFolder | SourceNotMoved:
    """
    Derive a SourceMovedToFolder event or failure event.

    Args:
        source_id: ID of the source to move
        folder_id: Target folder ID (None for root level)
        state: Current folder state

    Returns:
        SourceMovedToFolder event or SourceNotMoved failure event
    """
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return SourceNotMoved.source_not_found(source_id)

    if folder_id is not None:
        folder_exists = any(f.id == folder_id for f in state.existing_folders)
        if not folder_exists:
            return SourceNotMoved.folder_not_found(source_id, folder_id)

    return SourceMovedToFolder.create(
        source_id=source_id,
        old_folder_id=source.folder_id,
        new_folder_id=folder_id,
    )
