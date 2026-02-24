"""
Projects Context: Failure Events

Publishable failure events for the projects bounded context.
These events can be published to the event bus and trigger policies.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.shared.common.failure_events import FailureEvent
from src.shared.common.types import SourceId

# ============================================================
# Project Failure Events
# ============================================================


@dataclass(frozen=True)
class ProjectNotCreated(FailureEvent):
    """Failure event: Project creation failed."""

    name: str | None = None
    path: Path | None = None

    @classmethod
    def empty_name(cls) -> ProjectNotCreated:
        """Project name cannot be empty."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/EMPTY_NAME",
        )

    @classmethod
    def invalid_path(cls, path: Path) -> ProjectNotCreated:
        """Project path must have .qda extension."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/INVALID_PATH",
            path=path,
        )

    @classmethod
    def already_exists(cls, path: Path) -> ProjectNotCreated:
        """A project already exists at this path."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/ALREADY_EXISTS",
            path=path,
        )

    @classmethod
    def parent_not_writable(cls, path: Path) -> ProjectNotCreated:
        """Cannot write to the parent directory."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_CREATED/PARENT_NOT_WRITABLE",
            path=path,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "EMPTY_NAME":
                return "Project name cannot be empty"
            case "INVALID_PATH":
                return f"Invalid project path: {self.path}. Must have .qda extension."
            case "ALREADY_EXISTS":
                return f"Project already exists at: {self.path}"
            case "PARENT_NOT_WRITABLE":
                return f"Cannot write to directory: {self.path.parent if self.path else 'unknown'}"
            case _:
                return super().message


@dataclass(frozen=True)
class ProjectNotOpened(FailureEvent):
    """Failure event: Project opening failed."""

    path: Path | None = None

    @classmethod
    def invalid_path(cls, path: Path) -> ProjectNotOpened:
        """Project path must have .qda extension."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_OPENED/INVALID_PATH",
            path=path,
        )

    @classmethod
    def not_found(cls, path: Path) -> ProjectNotOpened:
        """Project file does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="PROJECT_NOT_OPENED/NOT_FOUND",
            path=path,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "INVALID_PATH":
                return f"Invalid project path: {self.path}. Must have .qda extension."
            case "NOT_FOUND":
                return f"Project not found: {self.path}"
            case _:
                return super().message


# ============================================================
# Source Failure Events
# ============================================================


@dataclass(frozen=True)
class SourceNotAdded(FailureEvent):
    """Failure event: Source addition failed."""

    path: Path | None = None
    name: str | None = None

    @classmethod
    def file_not_found(cls, path: Path) -> SourceNotAdded:
        """Source file does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_ADDED/FILE_NOT_FOUND",
            path=path,
        )

    @classmethod
    def duplicate_name(cls, name: str) -> SourceNotAdded:
        """A source with this name already exists in the project."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_ADDED/DUPLICATE_NAME",
            name=name,
        )

    @classmethod
    def unsupported_type(cls, path: Path) -> SourceNotAdded:
        """The source file type is not supported."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_ADDED/UNSUPPORTED_TYPE",
            path=path,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "FILE_NOT_FOUND":
                return f"Source file not found: {self.path}"
            case "DUPLICATE_NAME":
                return f"Source with name '{self.name}' already exists"
            case "UNSUPPORTED_TYPE":
                return f"Unsupported file type: {self.path.suffix if self.path else 'unknown'}"
            case _:
                return super().message


@dataclass(frozen=True)
class SourceNotRemoved(FailureEvent):
    """Failure event: Source removal failed."""

    source_id: SourceId | None = None

    @classmethod
    def not_found(cls, source_id: SourceId) -> SourceNotRemoved:
        """Source does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_REMOVED/NOT_FOUND",
            source_id=source_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Source not found: {self.source_id.value if self.source_id else 'unknown'}"
            case _:
                return super().message


@dataclass(frozen=True)
class SourceNotOpened(FailureEvent):
    """Failure event: Source opening failed."""

    source_id: SourceId | None = None

    @classmethod
    def not_found(cls, source_id: SourceId) -> SourceNotOpened:
        """Source does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_OPENED/NOT_FOUND",
            source_id=source_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Source not found: {self.source_id.value if self.source_id else 'unknown'}"
            case _:
                return super().message


@dataclass(frozen=True)
class SourceNotUpdated(FailureEvent):
    """Failure event: Source update failed."""

    source_id: SourceId | None = None
    status: str | None = None

    @classmethod
    def not_found(cls, source_id: SourceId) -> SourceNotUpdated:
        """Source does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_UPDATED/NOT_FOUND",
            source_id=source_id,
        )

    @classmethod
    def invalid_status(cls, source_id: SourceId, status: str) -> SourceNotUpdated:
        """Invalid source status value."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_UPDATED/INVALID_STATUS",
            source_id=source_id,
            status=status,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Source not found: {self.source_id.value if self.source_id else 'unknown'}"
            case "INVALID_STATUS":
                return f"Invalid source status: '{self.status}'"
            case _:
                return super().message


# ============================================================
# Folder Failure Events
# ============================================================


# ============================================================
# Folder Failure Events (re-exported from folders context)
# ============================================================

from src.contexts.folders.core.failure_events import (  # noqa: F401, E402
    FolderNotCreated,
    FolderNotDeleted,
    FolderNotRenamed,
    SourceNotMoved,
)

# ============================================================
# Type Unions
# ============================================================

ProjectFailureEvent = ProjectNotCreated | ProjectNotOpened

SourceFailureEvent = (
    SourceNotAdded | SourceNotRemoved | SourceNotOpened | SourceNotUpdated
)

FolderFailureEvent = (
    FolderNotCreated | FolderNotRenamed | FolderNotDeleted | SourceNotMoved
)

# All failure events from the Projects context
ProjectsContextFailureEvent = (
    ProjectFailureEvent | SourceFailureEvent | FolderFailureEvent
)


# ============================================================
# Exports
# ============================================================

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
