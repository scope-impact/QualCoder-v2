"""
Version Control Events - Immutable Domain Events

Immutable event records representing state changes in version control.
Events are produced by derivers and consumed by the application layer.
All events inherit from DomainEvent base class.

Event type convention: projects.{action}
Event naming: Past tense (e.g., SnapshotCreated, not CreateSnapshot)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.shared.common.types import DomainEvent

# ============================================================
# Version Control Events
# ============================================================


@dataclass(frozen=True)
class SnapshotCreated(DomainEvent):
    """
    Event: A version control snapshot was created.

    Emitted after successful auto-commit or manual snapshot.
    Contains the git SHA and commit message for traceability.
    """

    event_type: ClassVar[str] = "projects.snapshot_created"

    git_sha: str
    message: str
    event_count: int

    @classmethod
    def create(
        cls,
        git_sha: str,
        message: str,
        event_count: int,
    ) -> SnapshotCreated:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            git_sha=git_sha,
            message=message,
            event_count=event_count,
        )


@dataclass(frozen=True)
class SnapshotRestored(DomainEvent):
    """
    Event: Database was restored to a previous snapshot.

    Emitted after successful restore operation.
    The ref is the original reference (e.g., "HEAD~3") and
    git_sha is the resolved commit SHA.
    """

    event_type: ClassVar[str] = "projects.snapshot_restored"

    ref: str
    git_sha: str

    @classmethod
    def create(
        cls,
        ref: str,
        git_sha: str,
    ) -> SnapshotRestored:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            ref=ref,
            git_sha=git_sha,
        )


@dataclass(frozen=True)
class VersionControlInitialized(DomainEvent):
    """
    Event: Version control was initialized for a project.

    Emitted after successful git init and initial snapshot.
    """

    event_type: ClassVar[str] = "projects.version_control_initialized"

    project_path: str

    @classmethod
    def create(
        cls,
        project_path: str,
    ) -> VersionControlInitialized:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            project_path=project_path,
        )


# ============================================================
# Type Unions
# ============================================================

VersionControlEvent = SnapshotCreated | SnapshotRestored | VersionControlInitialized


# ============================================================
# Exports
# ============================================================

__all__ = [
    "SnapshotCreated",
    "SnapshotRestored",
    "VersionControlInitialized",
    "VersionControlEvent",
]
