"""
Project Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.
These are the core of the Functional DDD pattern.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.contexts.projects.core.entities import Folder, Source
from src.contexts.projects.core.events import (
    FolderCreated,
    FolderDeleted,
    FolderRenamed,
    ProjectCreated,
    ProjectOpened,
    SourceAdded,
    SourceMovedToFolder,
    SourceOpened,
    SourceRemoved,
    SourceUpdated,
)
from src.contexts.projects.core.failure_events import (
    FolderNotCreated,
    FolderNotDeleted,
    FolderNotRenamed,
    ProjectNotCreated,
    ProjectNotOpened,
    SourceNotAdded,
    SourceNotMoved,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)
from src.contexts.projects.core.invariants import (
    can_open_project,
    detect_source_type,
    is_folder_empty,
    is_folder_name_unique,
    is_source_name_unique,
    is_valid_folder_name,
    is_valid_project_name,
    is_valid_project_path,
)
from src.shared.common.types import FolderId, SourceId

# ============================================================
# State Container (Input to Derivers)
# ============================================================


@dataclass(frozen=True)
class ProjectState:
    """
    State container for project context derivers.

    Contains all the context needed to validate operations.
    Functions are passed as dependencies for I/O operations.
    """

    path_exists: Callable[[Path], bool] = lambda _: False
    parent_writable: Callable[[Path], bool] = lambda _: True
    existing_sources: tuple[Source, ...] = ()


@dataclass(frozen=True)
class FolderState:
    """
    State container for folder context derivers.

    Contains all the context needed to validate folder operations.
    """

    existing_folders: tuple[Folder, ...] = ()
    existing_sources: tuple[Source, ...] = ()


# ============================================================
# Failure Reasons
# ============================================================


@dataclass(frozen=True)
class EmptyProjectName:
    """Project name cannot be empty."""

    message: str = "Project name cannot be empty"


@dataclass(frozen=True)
class InvalidProjectPath:
    """Project path must have .qda extension."""

    path: Path | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if self.path:
            object.__setattr__(
                self,
                "message",
                f"Invalid project path: {self.path}. Must have .qda extension.",
            )
        else:
            object.__setattr__(
                self, "message", "Invalid project path. Must have .qda extension."
            )


@dataclass(frozen=True)
class ProjectAlreadyExists:
    """A project already exists at this path."""

    path: Path
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Project already exists at: {self.path}")


@dataclass(frozen=True)
class ParentNotWritable:
    """Cannot write to the parent directory."""

    path: Path
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Cannot write to directory: {self.path.parent}"
        )


@dataclass(frozen=True)
class ProjectNotFound:
    """Project file does not exist."""

    path: Path
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Project not found: {self.path}")


@dataclass(frozen=True)
class SourceFileNotFound:
    """Source file does not exist."""

    path: Path
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Source file not found: {self.path}")


@dataclass(frozen=True)
class DuplicateSourceName:
    """A source with this name already exists in the project."""

    name: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Source with name '{self.name}' already exists"
        )


@dataclass(frozen=True)
class UnsupportedSourceType:
    """The source file type is not supported."""

    path: Path
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Unsupported file type: {self.path.suffix}"
        )


@dataclass(frozen=True)
class InvalidFolderName:
    """Folder name is invalid."""

    name: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Invalid folder name: '{self.name}'")


@dataclass(frozen=True)
class DuplicateFolderName:
    """A folder with this name already exists at this level."""

    name: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "message",
            f"Folder with name '{self.name}' already exists at this level",
        )


@dataclass(frozen=True)
class FolderNotFound:
    """Folder does not exist."""

    folder_id: FolderId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Folder not found: {self.folder_id.value}")


@dataclass(frozen=True)
class FolderNotEmpty:
    """Cannot delete folder because it contains sources."""

    folder_id: FolderId
    source_count: int
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "message",
            f"Folder contains {self.source_count} source(s) and cannot be deleted",
        )


@dataclass(frozen=True)
class SourceNotFound:
    """Source does not exist."""

    source_id: SourceId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Source not found: {self.source_id.value}")


@dataclass(frozen=True)
class InvalidSourceStatus:
    """Invalid source status value."""

    status: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Invalid source status: '{self.status}'")


# ============================================================
# Project Derivers
# ============================================================


def derive_create_project(
    name: str,
    path: Path,
    memo: str | None,
    owner: str | None,
    state: ProjectState,
) -> ProjectCreated | ProjectNotCreated:
    """
    Derive a ProjectCreated event or failure event.

    Args:
        name: Name for the new project
        path: Path where project will be created
        memo: Optional project memo/description
        owner: Owner identifier
        state: Current project state (with I/O functions)

    Returns:
        ProjectCreated event or ProjectNotCreated failure event
    """
    # Validate project name
    if not is_valid_project_name(name):
        return ProjectNotCreated.empty_name()

    # Validate path has .qda extension
    if not is_valid_project_path(path):
        return ProjectNotCreated.invalid_path(path)

    # Check if path already exists
    if state.path_exists(path):
        return ProjectNotCreated.already_exists(path)

    # Check if parent directory is writable
    if not state.parent_writable(path.parent):
        return ProjectNotCreated.parent_not_writable(path)

    return ProjectCreated.create(
        name=name,
        path=path,
        memo=memo,
        owner=owner,
    )


def derive_open_project(
    path: Path,
    state: ProjectState,
) -> ProjectOpened | ProjectNotOpened:
    """
    Derive a ProjectOpened event or failure event.

    Args:
        path: Path to the project file
        state: Current project state (with I/O functions)

    Returns:
        ProjectOpened event or ProjectNotOpened failure event
    """
    # Validate path has .qda extension
    if not is_valid_project_path(path):
        return ProjectNotOpened.invalid_path(path)

    # Check if path exists
    if not can_open_project(path, state.path_exists):
        return ProjectNotOpened.not_found(path)

    return ProjectOpened.create(path=path)


# ============================================================
# Source Derivers
# ============================================================


def derive_add_source(
    source_path: Path,
    origin: str | None,
    memo: str | None,
    owner: str | None,
    state: ProjectState,
) -> SourceAdded | SourceNotAdded:
    """
    Derive a SourceAdded event or failure event.

    Args:
        source_path: Path to the source file
        origin: Origin/category of the source (e.g., "Field Interview")
        memo: Optional memo about the source
        owner: Owner identifier
        state: Current project state

    Returns:
        SourceAdded event or SourceNotAdded failure event
    """
    # Check if source file exists
    if not state.path_exists(source_path):
        return SourceNotAdded.file_not_found(source_path)

    # Get source name from path
    source_name = source_path.name

    # Check if name is unique
    if not is_source_name_unique(source_name, state.existing_sources):
        return SourceNotAdded.duplicate_name(source_name)

    # Detect source type
    source_type = detect_source_type(source_path)

    # Generate source ID
    source_id = SourceId.new()

    return SourceAdded.create(
        source_id=source_id,
        name=source_name,
        source_type=source_type,
        file_path=source_path,
        file_size=0,  # Would be populated by infrastructure layer
        origin=origin,
        memo=memo,
        owner=owner,
    )


def derive_remove_source(
    source_id: SourceId,
    state: ProjectState,
) -> SourceRemoved | SourceNotRemoved:
    """
    Derive a SourceRemoved event or failure event.

    Args:
        source_id: ID of the source to remove
        state: Current project state

    Returns:
        SourceRemoved event or SourceNotRemoved failure event
    """
    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return SourceNotRemoved.not_found(source_id)

    return SourceRemoved.create(
        source_id=source_id,
        name=source.name,
        segments_removed=source.code_count,
    )


def derive_open_source(
    source_id: SourceId,
    state: ProjectState,
) -> SourceOpened | SourceNotOpened:
    """
    Derive a SourceOpened event or failure event.

    Args:
        source_id: ID of the source to open
        state: Current project state

    Returns:
        SourceOpened event or SourceNotOpened failure event
    """
    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return SourceNotOpened.not_found(source_id)

    return SourceOpened.create(
        source_id=source_id,
        name=source.name,
        source_type=source.source_type,
    )


def derive_update_source(
    source_id: SourceId,
    memo: str | None,
    origin: str | None,
    status: str | None,
    state: ProjectState,
) -> SourceUpdated | SourceNotUpdated:
    """
    Derive a SourceUpdated event or failure event.

    Args:
        source_id: ID of the source to update
        memo: New memo value (None = no change, "" = clear)
        origin: New origin value (None = no change, "" = clear)
        status: New status value (None = no change)
        state: Current project state

    Returns:
        SourceUpdated event or SourceNotUpdated failure event
    """
    from src.contexts.projects.core.entities import SourceStatus

    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return SourceNotUpdated.not_found(source_id)

    # Validate status if provided
    if status is not None:
        try:
            SourceStatus(status)
        except ValueError:
            return SourceNotUpdated.invalid_status(source_id, status)

    return SourceUpdated.create(
        source_id=source_id,
        memo=memo,
        origin=origin,
        status=status,
    )


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
    # Validate folder name
    if not is_valid_folder_name(name):
        return FolderNotCreated.invalid_name(name)

    # Check if name is unique at this parent level
    if not is_folder_name_unique(name, parent_id, state.existing_folders):
        return FolderNotCreated.duplicate_name(name, parent_id)

    # Generate folder ID
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
    # Find the folder
    folder = next((f for f in state.existing_folders if f.id == folder_id), None)

    if folder is None:
        return FolderNotRenamed.not_found(folder_id)

    # Validate new name
    if not is_valid_folder_name(new_name):
        return FolderNotRenamed.invalid_name(folder_id, new_name)

    # Check if new name is unique at the same parent level (excluding self)
    for existing_folder in state.existing_folders:
        # Skip the folder being renamed
        if existing_folder.id == folder_id:
            continue

        # Check folders at the same parent level
        if (
            existing_folder.parent_id == folder.parent_id
            and existing_folder.name.lower() == new_name.lower()
        ):
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
    # Find the folder
    folder = next((f for f in state.existing_folders if f.id == folder_id), None)

    if folder is None:
        return FolderNotDeleted.not_found(folder_id)

    # Check if folder is empty (no sources)
    if not is_folder_empty(folder_id, state.existing_sources):
        # Count sources in folder for error message
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
    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return SourceNotMoved.source_not_found(source_id)

    # If moving to a specific folder, verify it exists
    if folder_id is not None:
        folder_exists = any(f.id == folder_id for f in state.existing_folders)
        if not folder_exists:
            return SourceNotMoved.folder_not_found(source_id, folder_id)

    return SourceMovedToFolder.create(
        source_id=source_id,
        old_folder_id=source.folder_id,
        new_folder_id=folder_id,
    )
