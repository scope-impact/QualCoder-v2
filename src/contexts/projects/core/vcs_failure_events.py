"""
Version Control Failure Events - Rich Failure Context

Publishable failure events for version control operations.
These events can be published to the event bus and trigger policies.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
Examples:
    - AUTO_COMMIT_SKIPPED/NOT_INITIALIZED
    - SNAPSHOT_NOT_RESTORED/UNCOMMITTED_CHANGES
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent

# ============================================================
# Auto-Commit Failure Events
# ============================================================


@dataclass(frozen=True)
class AutoCommitSkipped(FailureEvent):
    """
    Failure event: Auto-commit was skipped.

    This is not necessarily an error - it can be skipped because
    there are no events to commit, which is normal.
    """

    suggestions: tuple[str, ...] = ()

    @classmethod
    def not_initialized(cls) -> AutoCommitSkipped:
        """Auto-commit skipped because VCS is not initialized."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="AUTO_COMMIT_SKIPPED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )

    @classmethod
    def no_events(cls) -> AutoCommitSkipped:
        """Auto-commit skipped because there are no events to commit."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="AUTO_COMMIT_SKIPPED/NO_EVENTS",
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_INITIALIZED":
                return "Version control not initialized"
            case "NO_EVENTS":
                return "No events to commit"
            case _:
                return super().message


# ============================================================
# Snapshot Restore Failure Events
# ============================================================


@dataclass(frozen=True)
class SnapshotNotRestored(FailureEvent):
    """
    Failure event: Snapshot restoration failed.

    Contains the target ref if available for debugging.
    """

    ref: str | None = None
    suggestions: tuple[str, ...] = ()

    @classmethod
    def not_initialized(cls) -> SnapshotNotRestored:
        """Restore failed because VCS is not initialized."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SNAPSHOT_NOT_RESTORED/NOT_INITIALIZED",
            suggestions=("Initialize version control first",),
        )

    @classmethod
    def uncommitted_changes(cls) -> SnapshotNotRestored:
        """Restore failed because there are uncommitted changes."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SNAPSHOT_NOT_RESTORED/UNCOMMITTED_CHANGES",
            suggestions=(
                "Wait for auto-commit to complete",
                "Or discard changes",
            ),
        )

    @classmethod
    def invalid_ref(cls, ref: str) -> SnapshotNotRestored:
        """Restore failed because the ref is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SNAPSHOT_NOT_RESTORED/INVALID_REF",
            ref=ref,
            suggestions=(
                "Use 'list_snapshots' to see valid refs",
                "Use HEAD~N syntax for relative refs",
            ),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_INITIALIZED":
                return "Version control not initialized"
            case "UNCOMMITTED_CHANGES":
                return "Cannot restore with uncommitted changes"
            case "INVALID_REF":
                return f"Invalid snapshot reference: {self.ref}"
            case _:
                return super().message


# ============================================================
# Version Control Initialization Failure Events
# ============================================================


@dataclass(frozen=True)
class VersionControlNotInitialized(FailureEvent):
    """
    Failure event: Version control initialization failed.
    """

    project_path: str | None = None
    suggestions: tuple[str, ...] = ()

    @classmethod
    def already_initialized(cls, project_path: str) -> VersionControlNotInitialized:
        """Initialization failed because VCS already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="VERSION_CONTROL_NOT_INITIALIZED/ALREADY_INITIALIZED",
            project_path=project_path,
        )

    @classmethod
    def git_not_available(cls) -> VersionControlNotInitialized:
        """Initialization failed because git is not installed."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="VERSION_CONTROL_NOT_INITIALIZED/GIT_NOT_AVAILABLE",
            suggestions=("Install git and ensure it's in PATH",),
        )

    @classmethod
    def permission_denied(cls, project_path: str) -> VersionControlNotInitialized:
        """Initialization failed due to permission issues."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="VERSION_CONTROL_NOT_INITIALIZED/PERMISSION_DENIED",
            project_path=project_path,
            suggestions=("Check write permissions for the project directory",),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "ALREADY_INITIALIZED":
                return f"Version control already initialized at: {self.project_path}"
            case "GIT_NOT_AVAILABLE":
                return "Git is not available on this system"
            case "PERMISSION_DENIED":
                return f"Permission denied for: {self.project_path}"
            case _:
                return super().message


# ============================================================
# Type Unions
# ============================================================

VersionControlFailureEvent = (
    AutoCommitSkipped | SnapshotNotRestored | VersionControlNotInitialized
)


# ============================================================
# Exports
# ============================================================

__all__ = [
    "AutoCommitSkipped",
    "SnapshotNotRestored",
    "VersionControlNotInitialized",
    "VersionControlFailureEvent",
]
