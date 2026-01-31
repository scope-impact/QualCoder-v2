"""
Project Context: Entities and Value Objects

Immutable data types representing domain concepts for project management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from src.domain.shared.types import SourceId

# ============================================================
# Enums
# ============================================================


class SourceType(Enum):
    """Type of source file based on content."""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    PDF = "pdf"
    UNKNOWN = "unknown"


class SourceStatus(Enum):
    """Processing status of a source file."""

    IMPORTING = "importing"
    IMPORTED = "imported"
    QUEUED = "queued"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    CODED = "coded"
    ERROR = "error"


# ============================================================
# Value Objects
# ============================================================


@dataclass(frozen=True)
class ProjectId:
    """Unique identifier for a project."""

    value: str

    @classmethod
    def from_path(cls, path: Path) -> ProjectId:
        """Generate project ID from file path."""
        return cls(value=str(path.resolve()))


@dataclass(frozen=True)
class ProjectSummary:
    """Summary statistics for a project."""

    total_sources: int = 0
    text_count: int = 0
    audio_count: int = 0
    video_count: int = 0
    image_count: int = 0
    pdf_count: int = 0
    total_codes: int = 0
    total_segments: int = 0


# ============================================================
# Entities
# ============================================================


@dataclass(frozen=True)
class Source:
    """
    A source file in a project (interview, document, media, etc.).

    Sources are imported into the project and can be coded.
    Aggregate Root for the Source aggregate.
    """

    id: SourceId
    name: str
    source_type: SourceType
    status: SourceStatus = SourceStatus.IMPORTED
    file_path: Path | None = None
    file_size: int = 0
    memo: str | None = None
    origin: str | None = None  # Where the source came from
    case_ids: tuple[int, ...] = ()  # Associated cases
    code_count: int = 0  # Number of codes applied
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_status(self, new_status: SourceStatus) -> Source:
        """Return new Source with updated status."""
        return Source(
            id=self.id,
            name=self.name,
            source_type=self.source_type,
            status=new_status,
            file_path=self.file_path,
            file_size=self.file_size,
            memo=self.memo,
            origin=self.origin,
            case_ids=self.case_ids,
            code_count=self.code_count,
            created_at=self.created_at,
            modified_at=datetime.now(UTC),
        )

    def with_memo(self, new_memo: str | None) -> Source:
        """Return new Source with updated memo."""
        return Source(
            id=self.id,
            name=self.name,
            source_type=self.source_type,
            status=self.status,
            file_path=self.file_path,
            file_size=self.file_size,
            memo=new_memo,
            origin=self.origin,
            case_ids=self.case_ids,
            code_count=self.code_count,
            created_at=self.created_at,
            modified_at=datetime.now(UTC),
        )

    def with_code_count(self, new_count: int) -> Source:
        """Return new Source with updated code count."""
        return Source(
            id=self.id,
            name=self.name,
            source_type=self.source_type,
            status=self.status,
            file_path=self.file_path,
            file_size=self.file_size,
            memo=self.memo,
            origin=self.origin,
            case_ids=self.case_ids,
            code_count=new_count,
            created_at=self.created_at,
            modified_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class Project:
    """
    A QualCoder research project.

    Contains metadata about the project and references to sources.
    The .qda file is a SQLite database containing all project data.

    Aggregate Root for the Project aggregate.
    """

    id: ProjectId
    name: str
    path: Path
    memo: str | None = None
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    summary: ProjectSummary = field(default_factory=ProjectSummary)

    def with_name(self, new_name: str) -> Project:
        """Return new Project with updated name."""
        return Project(
            id=self.id,
            name=new_name,
            path=self.path,
            memo=self.memo,
            owner=self.owner,
            created_at=self.created_at,
            last_opened_at=self.last_opened_at,
            summary=self.summary,
        )

    def with_memo(self, new_memo: str | None) -> Project:
        """Return new Project with updated memo."""
        return Project(
            id=self.id,
            name=self.name,
            path=self.path,
            memo=new_memo,
            owner=self.owner,
            created_at=self.created_at,
            last_opened_at=self.last_opened_at,
            summary=self.summary,
        )

    def with_summary(self, new_summary: ProjectSummary) -> Project:
        """Return new Project with updated summary."""
        return Project(
            id=self.id,
            name=self.name,
            path=self.path,
            memo=self.memo,
            owner=self.owner,
            created_at=self.created_at,
            last_opened_at=self.last_opened_at,
            summary=new_summary,
        )

    def touch(self) -> Project:
        """Return new Project with updated last_opened_at."""
        return Project(
            id=self.id,
            name=self.name,
            path=self.path,
            memo=self.memo,
            owner=self.owner,
            created_at=self.created_at,
            last_opened_at=datetime.now(UTC),
            summary=self.summary,
        )


@dataclass(frozen=True)
class RecentProject:
    """
    A recently opened project for quick access.

    Stored in user preferences, not in project file.
    """

    path: Path
    name: str
    last_opened: datetime

    def touch(self) -> RecentProject:
        """Return new RecentProject with updated timestamp."""
        return RecentProject(
            path=self.path,
            name=self.name,
            last_opened=datetime.now(UTC),
        )
