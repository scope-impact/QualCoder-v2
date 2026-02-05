"""
Version Control ViewModel

Orchestrates VCS operations for the presentation layer.
Follows the pattern: ViewModel → CommandHandler → Repository → EventBus → SignalBridge → ViewModel
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot

from src.contexts.projects.core.commandHandlers import (
    initialize_version_control,
    list_snapshots,
    restore_snapshot,
    view_diff,
)
from src.contexts.projects.core.vcs_commands import (
    InitializeVersionControlCommand,
    RestoreSnapshotCommand,
)
from src.shared.presentation.organisms.version_history_panel import SnapshotItem

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus


class VersionControlViewModel(QObject):
    """
    ViewModel for version control operations.

    Provides:
    - Load and display snapshot history
    - Restore to a previous snapshot
    - View diff between snapshots
    - Initialize VCS for a project

    Signals:
        snapshots_loaded(list): Emitted when snapshots are loaded
        restore_completed(str): Emitted when restore completes (with message)
        restore_failed(str): Emitted when restore fails (with error)
        diff_loaded(str, str, str): Emitted when diff is loaded (from, to, content)
        error_occurred(str): Emitted when an error occurs
        vcs_initialized(): Emitted when VCS is initialized
    """

    snapshots_loaded = Signal(list)  # list[SnapshotItem]
    restore_completed = Signal(str)  # success message
    restore_failed = Signal(str)  # error message
    diff_loaded = Signal(str, str, str)  # from_ref, to_ref, diff_content
    error_occurred = Signal(str)  # error message
    vcs_initialized = Signal()

    def __init__(
        self,
        project_path: Path,
        diffable_adapter: SqliteDiffableAdapter,
        git_adapter: GitRepositoryAdapter,
        event_bus: EventBus,
        parent=None,
    ):
        super().__init__(parent)
        self._project_path = project_path
        self._diffable_adapter = diffable_adapter
        self._git_adapter = git_adapter
        self._event_bus = event_bus

    @property
    def is_initialized(self) -> bool:
        """Check if VCS is initialized for this project."""
        return self._git_adapter.is_initialized()

    @Slot()
    def load_snapshots(self):
        """Load snapshot history from git log."""
        if not self.is_initialized:
            self.snapshots_loaded.emit([])
            return

        result = list_snapshots(limit=50, git_adapter=self._git_adapter)

        if result.is_failure:
            self.error_occurred.emit(result.error or "Failed to load history")
            self.snapshots_loaded.emit([])
            return

        # Convert to SnapshotItem list
        commits = result.data or []
        snapshots = []

        for i, commit in enumerate(commits):
            snapshot = SnapshotItem(
                git_sha=commit.sha,
                message=commit.message,
                timestamp=commit.timestamp,
                event_count=0,  # Could parse from message if needed
                is_current=(i == 0),  # First is current
            )
            snapshots.append(snapshot)

        self.snapshots_loaded.emit(snapshots)

    @Slot(str)
    def restore_to_snapshot(self, git_sha: str):
        """Restore the database to a specific snapshot."""
        if not self.is_initialized:
            self.restore_failed.emit("Version control not initialized")
            return

        command = RestoreSnapshotCommand(
            project_path=str(self._project_path),
            ref=git_sha,
        )

        result = restore_snapshot(
            command=command,
            diffable_adapter=self._diffable_adapter,
            git_adapter=self._git_adapter,
            event_bus=self._event_bus,
        )

        if result.is_failure:
            self.restore_failed.emit(result.error or "Failed to restore snapshot")
        else:
            self.restore_completed.emit(f"Restored to {git_sha[:8]}")
            # Reload snapshots to update current marker
            self.load_snapshots()

    @Slot(str, str)
    def load_diff(self, from_ref: str, to_ref: str):
        """Load diff between two snapshots."""
        if not self.is_initialized:
            self.error_occurred.emit("Version control not initialized")
            return

        result = view_diff(
            from_ref=from_ref,
            to_ref=to_ref,
            git_adapter=self._git_adapter,
        )

        if result.is_failure:
            self.error_occurred.emit(result.error or "Failed to load diff")
        else:
            diff_content = result.data or ""
            self.diff_loaded.emit(from_ref, to_ref, diff_content)

    @Slot()
    def initialize_vcs(self):
        """Initialize version control for the project."""
        if self.is_initialized:
            self.error_occurred.emit("Version control already initialized")
            return

        command = InitializeVersionControlCommand(
            project_path=str(self._project_path),
        )

        result = initialize_version_control(
            command=command,
            diffable_adapter=self._diffable_adapter,
            git_adapter=self._git_adapter,
            event_bus=self._event_bus,
        )

        if result.is_failure:
            self.error_occurred.emit(result.error or "Failed to initialize VCS")
        else:
            self.vcs_initialized.emit()
            self.load_snapshots()


__all__ = ["VersionControlViewModel"]
