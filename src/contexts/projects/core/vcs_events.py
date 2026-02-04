"""Version Control Events - Immutable domain events for VCS state changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.shared.common.types import DomainEvent


@dataclass(frozen=True)
class SnapshotCreated(DomainEvent):
    """A version control snapshot was created (auto-commit or manual)."""

    event_type: ClassVar[str] = "projects.snapshot_created"

    git_sha: str
    message: str
    event_count: int

    @classmethod
    def create(cls, git_sha: str, message: str, event_count: int) -> SnapshotCreated:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            git_sha=git_sha,
            message=message,
            event_count=event_count,
        )


@dataclass(frozen=True)
class SnapshotRestored(DomainEvent):
    """Database was restored to a previous snapshot."""

    event_type: ClassVar[str] = "projects.snapshot_restored"

    ref: str
    git_sha: str

    @classmethod
    def create(cls, ref: str, git_sha: str) -> SnapshotRestored:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            ref=ref,
            git_sha=git_sha,
        )


@dataclass(frozen=True)
class VersionControlInitialized(DomainEvent):
    """Version control was initialized for a project."""

    event_type: ClassVar[str] = "projects.version_control_initialized"

    project_path: str

    @classmethod
    def create(cls, project_path: str) -> VersionControlInitialized:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            project_path=project_path,
        )


VersionControlEvent = SnapshotCreated | SnapshotRestored | VersionControlInitialized
