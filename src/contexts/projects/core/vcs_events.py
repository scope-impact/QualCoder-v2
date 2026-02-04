"""Version Control Events - Immutable domain events for VCS state changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.shared.common.types import DomainEvent

# ============================================================
# Decision Events (returned by derivers, consumed by handlers)
# ============================================================


@dataclass(frozen=True)
class AutoCommitDecided:
    """
    Decision event: Auto-commit should proceed.

    Derivers return this to indicate the commit can proceed.
    Command handler uses this to create the actual SnapshotCreated event.
    """

    message: str
    event_count: int


@dataclass(frozen=True)
class RestoreDecided:
    """
    Decision event: Restore should proceed.

    Derivers return this to indicate the restore can proceed.
    Command handler uses this to create the actual SnapshotRestored event.
    """

    ref: str


@dataclass(frozen=True)
class InitializeDecided:
    """
    Decision event: Initialization should proceed.

    Derivers return this to indicate initialization can proceed.
    Command handler uses this to create the actual VersionControlInitialized event.
    """

    project_path: str


# ============================================================
# Domain Events (published after successful I/O)
# ============================================================


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


# ============================================================
# Type Unions
# ============================================================

DecisionEvent = AutoCommitDecided | RestoreDecided | InitializeDecided
VersionControlEvent = SnapshotCreated | SnapshotRestored | VersionControlInitialized

# ============================================================
# Exports
# ============================================================

__all__ = [
    # Decision events
    "AutoCommitDecided",
    "RestoreDecided",
    "InitializeDecided",
    "DecisionEvent",
    # Domain events
    "SnapshotCreated",
    "SnapshotRestored",
    "VersionControlInitialized",
    "VersionControlEvent",
]
