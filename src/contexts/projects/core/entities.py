"""
Project Context: Entities and Value Objects

Immutable data types representing domain concepts for project management.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from src.shared.common.types import FolderId, SourceId

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
    folder_id: FolderId | None = None  # Folder containing this source
    case_ids: tuple[int, ...] = ()  # Associated cases
    code_count: int = 0  # Number of codes applied
    fulltext: str | None = None  # Text content for text sources
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_status(self, new_status: SourceStatus) -> Source:
        """Return new Source with updated status."""
        return replace(self, status=new_status, modified_at=datetime.now(UTC))

    def with_memo(self, new_memo: str | None) -> Source:
        """Return new Source with updated memo."""
        return replace(self, memo=new_memo, modified_at=datetime.now(UTC))

    def with_origin(self, new_origin: str | None) -> Source:
        """Return new Source with updated origin."""
        return replace(self, origin=new_origin, modified_at=datetime.now(UTC))

    def with_folder(self, new_folder_id: FolderId | None) -> Source:
        """Return new Source with updated folder."""
        return replace(self, folder_id=new_folder_id, modified_at=datetime.now(UTC))

    def with_code_count(self, new_count: int) -> Source:
        """Return new Source with updated code count."""
        return replace(self, code_count=new_count, modified_at=datetime.now(UTC))

    def with_name(self, new_name: str) -> Source:
        """Return new Source with updated name."""
        return replace(self, name=new_name, modified_at=datetime.now(UTC))


@dataclass(frozen=True)
class Folder:
    """
    A folder for organizing sources in a project.

    Folders can contain sources and be nested within other folders.
    """

    id: FolderId
    name: str
    parent_id: FolderId | None = None  # None means root level
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_name(self, new_name: str) -> Folder:
        """Return new Folder with updated name."""
        return replace(self, name=new_name)

    def with_parent(self, new_parent_id: FolderId | None) -> Folder:
        """Return new Folder with updated parent."""
        return replace(self, parent_id=new_parent_id)


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
        return replace(self, name=new_name)

    def with_memo(self, new_memo: str | None) -> Project:
        """Return new Project with updated memo."""
        return replace(self, memo=new_memo)

    def with_summary(self, new_summary: ProjectSummary) -> Project:
        """Return new Project with updated summary."""
        return replace(self, summary=new_summary)

    def touch(self) -> Project:
        """Return new Project with updated last_opened_at."""
        return replace(self, last_opened_at=datetime.now(UTC))


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
        return replace(self, last_opened=datetime.now(UTC))
