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

from src.contexts.projects.core.entities import Source, SourceStatus
from src.contexts.projects.core.events import (
    ProjectCreated,
    ProjectOpened,
    SourceAdded,
    SourceOpened,
    SourceRemoved,
    SourceUpdated,
)
from src.contexts.projects.core.failure_events import (
    ProjectNotCreated,
    ProjectNotOpened,
    SourceNotAdded,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)
from src.contexts.projects.core.invariants import (
    can_open_project,
    detect_source_type,
    is_source_name_unique,
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


# FolderState re-exported from folders context
from src.contexts.folders.core.derivers import FolderState  # noqa: F401, E402

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
        prefix = (
            f"Invalid project path: {self.path}"
            if self.path
            else "Invalid project path"
        )
        object.__setattr__(self, "message", f"{prefix}. Must have .qda extension.")


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
# Folder Derivers (re-exported from folders context)
# ============================================================

from src.contexts.folders.core.derivers import (  # noqa: F401, E402
    derive_create_folder,
    derive_delete_folder,
    derive_move_source_to_folder,
    derive_rename_folder,
)
