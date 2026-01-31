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

from src.domain.projects.entities import Source
from src.domain.projects.events import (
    ProjectCreated,
    ProjectOpened,
    SourceAdded,
    SourceOpened,
    SourceRemoved,
)
from src.domain.projects.invariants import (
    can_open_project,
    detect_source_type,
    is_source_name_unique,
    is_valid_project_name,
    is_valid_project_path,
)
from src.domain.shared.types import Failure, SourceId

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


# ============================================================
# Project Derivers
# ============================================================


def derive_create_project(
    name: str,
    path: Path,
    memo: str | None,
    owner: str | None,
    state: ProjectState,
) -> ProjectCreated | Failure:
    """
    Derive a ProjectCreated event or failure.

    Args:
        name: Name for the new project
        path: Path where project will be created
        memo: Optional project memo/description
        owner: Owner identifier
        state: Current project state (with I/O functions)

    Returns:
        ProjectCreated event or Failure with reason
    """
    # Validate project name
    if not is_valid_project_name(name):
        return Failure(EmptyProjectName())

    # Validate path has .qda extension
    if not is_valid_project_path(path):
        return Failure(InvalidProjectPath(path))

    # Check if path already exists
    if state.path_exists(path):
        return Failure(ProjectAlreadyExists(path))

    # Check if parent directory is writable
    if not state.parent_writable(path.parent):
        return Failure(ParentNotWritable(path))

    return ProjectCreated.create(
        name=name,
        path=path,
        memo=memo,
        owner=owner,
    )


def derive_open_project(
    path: Path,
    state: ProjectState,
) -> ProjectOpened | Failure:
    """
    Derive a ProjectOpened event or failure.

    Args:
        path: Path to the project file
        state: Current project state (with I/O functions)

    Returns:
        ProjectOpened event or Failure with reason
    """
    # Validate path has .qda extension
    if not is_valid_project_path(path):
        return Failure(InvalidProjectPath(path))

    # Check if path exists
    if not can_open_project(path, state.path_exists):
        return Failure(ProjectNotFound(path))

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
) -> SourceAdded | Failure:
    """
    Derive a SourceAdded event or failure.

    Args:
        source_path: Path to the source file
        origin: Origin/category of the source (e.g., "Field Interview")
        memo: Optional memo about the source
        owner: Owner identifier
        state: Current project state

    Returns:
        SourceAdded event or Failure with reason
    """
    # Check if source file exists
    if not state.path_exists(source_path):
        return Failure(SourceFileNotFound(source_path))

    # Get source name from path
    source_name = source_path.name

    # Check if name is unique
    if not is_source_name_unique(source_name, state.existing_sources):
        return Failure(DuplicateSourceName(source_name))

    # Detect source type
    source_type = detect_source_type(source_path)

    # Generate source ID
    source_id = SourceId(value=hash(str(source_path)) % 1_000_000)

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
) -> SourceRemoved | Failure:
    """
    Derive a SourceRemoved event or failure.

    Args:
        source_id: ID of the source to remove
        state: Current project state

    Returns:
        SourceRemoved event or Failure with reason
    """
    from src.domain.projects.events import SourceRemoved

    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return Failure(SourceFileNotFound(Path(f"source_id={source_id.value}")))

    return SourceRemoved.create(
        source_id=source_id,
        name=source.name,
        segments_removed=source.code_count,
    )


def derive_open_source(
    source_id: SourceId,
    state: ProjectState,
) -> SourceOpened | Failure:
    """
    Derive a SourceOpened event or failure.

    Args:
        source_id: ID of the source to open
        state: Current project state

    Returns:
        SourceOpened event or Failure with reason
    """
    from src.domain.projects.events import SourceOpened

    # Find the source
    source = next((s for s in state.existing_sources if s.id == source_id), None)

    if source is None:
        return Failure(SourceFileNotFound(Path(f"source_id={source_id.value}")))

    return SourceOpened.create(
        source_id=source_id,
        name=source.name,
        source_type=source.source_type,
    )
