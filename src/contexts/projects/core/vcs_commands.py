"""
Version Control Commands - Command DTOs

Immutable command objects representing version control operations.
Commands are pure data containers with no behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class AutoCommitCommand:
    """
    Command to auto-commit pending domain events.

    Used by VersionControlListener after debounce period.
    """

    project_path: str
    events: list[Any]  # List of DomainEvent instances


@dataclass(frozen=True)
class RestoreSnapshotCommand:
    """
    Command to restore database to a previous snapshot.

    The ref can be:
    - A git SHA (e.g., "abc1234")
    - A relative ref (e.g., "HEAD~1", "HEAD~3")
    """

    project_path: str
    ref: str


@dataclass(frozen=True)
class InitializeVersionControlCommand:
    """
    Command to initialize version control for a project.

    Creates .git directory and initial snapshot.
    """

    project_path: str


__all__ = [
    "AutoCommitCommand",
    "RestoreSnapshotCommand",
    "InitializeVersionControlCommand",
]
