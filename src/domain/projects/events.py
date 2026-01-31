"""
Project Context: Domain Events

Immutable event records representing state changes in the project domain.
Events are produced by Derivers and consumed by the Application layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.domain.projects.entities import SourceType
from src.domain.shared.types import SourceId


# ============================================================
# Project Events
# ============================================================


@dataclass(frozen=True)
class ProjectCreated:
    """Event: A new project was created."""

    event_id: str
    occurred_at: datetime
    name: str
    path: Path
    memo: str | None
    owner: str | None

    @classmethod
    def create(
        cls,
        name: str,
        path: Path,
        memo: str | None = None,
        owner: str | None = None,
    ) -> ProjectCreated:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            name=name,
            path=path,
            memo=memo,
            owner=owner,
        )


@dataclass(frozen=True)
class ProjectOpened:
    """Event: An existing project was opened."""

    event_id: str
    occurred_at: datetime
    path: Path
    name: str | None = None  # May be resolved later from DB

    @classmethod
    def create(
        cls,
        path: Path,
        name: str | None = None,
    ) -> ProjectOpened:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            path=path,
            name=name,
        )


@dataclass(frozen=True)
class ProjectClosed:
    """Event: The current project was closed."""

    event_id: str
    occurred_at: datetime
    path: Path

    @classmethod
    def create(cls, path: Path) -> ProjectClosed:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            path=path,
        )


@dataclass(frozen=True)
class ProjectRenamed:
    """Event: Project was renamed."""

    event_id: str
    occurred_at: datetime
    path: Path
    old_name: str
    new_name: str

    @classmethod
    def create(cls, path: Path, old_name: str, new_name: str) -> ProjectRenamed:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            path=path,
            old_name=old_name,
            new_name=new_name,
        )


# ============================================================
# Source Events
# ============================================================


@dataclass(frozen=True)
class SourceAdded:
    """Event: A source file was added to the project."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    name: str
    source_type: SourceType
    file_path: Path
    file_size: int
    origin: str | None
    memo: str | None
    owner: str | None

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        source_type: SourceType,
        file_path: Path,
        file_size: int = 0,
        origin: str | None = None,
        memo: str | None = None,
        owner: str | None = None,
    ) -> SourceAdded:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            name=name,
            source_type=source_type,
            file_path=file_path,
            file_size=file_size,
            origin=origin,
            memo=memo,
            owner=owner,
        )


@dataclass(frozen=True)
class SourceRemoved:
    """Event: A source file was removed from the project."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    name: str
    segments_removed: int

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        segments_removed: int = 0,
    ) -> SourceRemoved:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            name=name,
            segments_removed=segments_removed,
        )


@dataclass(frozen=True)
class SourceRenamed:
    """Event: A source was renamed."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    old_name: str
    new_name: str

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        old_name: str,
        new_name: str,
    ) -> SourceRenamed:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            old_name=old_name,
            new_name=new_name,
        )


@dataclass(frozen=True)
class SourceOpened:
    """Event: A source was opened for viewing/coding."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    name: str
    source_type: SourceType

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        source_type: SourceType,
    ) -> SourceOpened:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            name=name,
            source_type=source_type,
        )


@dataclass(frozen=True)
class SourceStatusChanged:
    """Event: Source processing status changed."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    old_status: str
    new_status: str

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        old_status: str,
        new_status: str,
    ) -> SourceStatusChanged:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            old_status=old_status,
            new_status=new_status,
        )


# ============================================================
# Navigation Events
# ============================================================


@dataclass(frozen=True)
class ScreenChanged:
    """Event: User navigated to a different screen."""

    event_id: str
    occurred_at: datetime
    from_screen: str | None
    to_screen: str

    @classmethod
    def create(
        cls,
        from_screen: str | None,
        to_screen: str,
    ) -> ScreenChanged:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            from_screen=from_screen,
            to_screen=to_screen,
        )


@dataclass(frozen=True)
class NavigatedToSegment:
    """Event: User/Agent navigated to a specific segment in a source."""

    event_id: str
    occurred_at: datetime
    source_id: SourceId
    position_start: int
    position_end: int
    highlight: bool

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        position_start: int,
        position_end: int,
        highlight: bool = True,
    ) -> NavigatedToSegment:
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            source_id=source_id,
            position_start=position_start,
            position_end=position_end,
            highlight=highlight,
        )
