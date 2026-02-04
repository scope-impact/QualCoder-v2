"""
Version Control Listener - Infrastructure Layer.

Subscribes to mutation events from EventBus and triggers auto-commit
with debouncing to batch rapid changes.

Implements QC-047 Version Control infrastructure.

Usage:
    listener = VersionControlListener(
        event_bus=bus,
        diffable_adapter=SqliteDiffableAdapter(),
        git_adapter=GitRepositoryAdapter(project_path),
        project_path=project_path,
    )

    # Enable after VCS is initialized
    listener.enable()

    # Disable on project close
    listener.disable()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QTimer

if TYPE_CHECKING:
    from pathlib import Path

    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus, Subscription


# ============================================================
# Mutation Events
# ============================================================

# Events that trigger auto-commit (database mutations)
MUTATION_EVENTS: tuple[str, ...] = (
    # Coding context
    "coding.code_created",
    "coding.code_updated",
    "coding.code_deleted",
    "coding.category_created",
    "coding.category_deleted",
    "coding.segment_coded",
    "coding.segment_uncoded",
    "coding.segment_memo_updated",
    # Sources context
    "sources.source_imported",
    "sources.source_deleted",
    "sources.source_updated",
    # Cases context
    "cases.case_created",
    "cases.case_updated",
    "cases.case_deleted",
    "cases.attribute_added",
    "cases.attribute_updated",
    # Folders context
    "folders.folder_created",
    "folders.folder_deleted",
    "folders.source_moved",
)


# ============================================================
# Version Control Listener
# ============================================================


class VersionControlListener:
    """
    Listener that subscribes to mutation events and triggers auto-commit.

    Implements debouncing to batch rapid changes:
    - Collects events in a pending list
    - Resets a 500ms timer on each event
    - When timer fires, delegates to auto_commit command handler

    The listener must be explicitly enabled after version control
    is initialized for the project.

    Example:
        listener = VersionControlListener(
            event_bus=bus,
            diffable_adapter=SqliteDiffableAdapter(),
            git_adapter=GitRepositoryAdapter(project_path),
            project_path=project_path,
        )

        # Enable after VCS is initialized
        listener.enable()

        # ... user makes changes, events are batched ...

        # Disable on project close
        listener.disable()
    """

    DEBOUNCE_MS = 500

    def __init__(
        self,
        event_bus: EventBus,
        diffable_adapter: SqliteDiffableAdapter,
        git_adapter: GitRepositoryAdapter,
        project_path: Path,
    ) -> None:
        """
        Initialize the listener.

        Args:
            event_bus: Event bus to subscribe to
            diffable_adapter: Adapter for sqlite-diffable operations
            git_adapter: Adapter for Git operations
            project_path: Path to the project directory
        """
        self._event_bus = event_bus
        self._diffable_adapter = diffable_adapter
        self._git_adapter = git_adapter
        self._project_path = project_path

        # Pending events awaiting commit
        self._pending_events: list[Any] = []

        # Debounce timer (created lazily)
        self._timer: QTimer | None = None

        # Subscriptions (for cleanup)
        self._subscriptions: list[Subscription] = []

        # Enabled state
        self._enabled: bool = False

    @property
    def enabled(self) -> bool:
        """Check if the listener is currently enabled."""
        return self._enabled

    @property
    def pending_event_count(self) -> int:
        """Get the number of pending events awaiting commit."""
        return len(self._pending_events)

    def enable(self) -> None:
        """
        Enable the listener and subscribe to mutation events.

        Should be called after version control is initialized.
        """
        if self._enabled:
            return

        self._enabled = True

        # Subscribe to all mutation events
        for event_type in MUTATION_EVENTS:
            subscription = self._event_bus.subscribe(event_type, self._on_mutation)
            self._subscriptions.append(subscription)

    def disable(self) -> None:
        """
        Disable the listener and flush any pending events.

        Should be called before closing the project.
        """
        if not self._enabled:
            return

        self._enabled = False

        # Stop timer if running
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        # Flush any pending events before disabling
        if self._pending_events:
            self._flush()

        # Cancel all subscriptions
        for subscription in self._subscriptions:
            subscription.cancel()
        self._subscriptions.clear()

    def _on_mutation(self, event: Any) -> None:
        """
        Handle a mutation event.

        Adds the event to the pending list and resets the debounce timer.

        Args:
            event: The domain event that was published
        """
        if not self._enabled:
            return

        # Add event to pending list
        self._pending_events.append(event)

        # Reset the debounce timer
        self._reset_timer()

    def _reset_timer(self) -> None:
        """
        Reset the debounce timer.

        Stops any existing timer and starts a new one.
        """
        # Stop existing timer if any
        if self._timer is not None:
            self._timer.stop()

        # Create new single-shot timer
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)
        self._timer.start(self.DEBOUNCE_MS)

    def _flush(self) -> None:
        """
        Flush pending events by delegating to auto_commit command handler.

        Creates an AutoCommitCommand and calls the handler.
        """
        if not self._pending_events:
            return

        # Capture events and clear pending list
        events_to_commit = tuple(self._pending_events)
        self._pending_events.clear()

        # Stop timer
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        # Local import to avoid circular dependencies
        from src.contexts.projects.core.commandHandlers.auto_commit import auto_commit
        from src.contexts.projects.core.vcs_commands import AutoCommitCommand

        # Create command
        command = AutoCommitCommand(
            project_path=str(self._project_path),
            events=list(events_to_commit),
        )

        # Delegate to command handler
        # The handler will:
        # 1. Export database to diffable format
        # 2. Stage changes in git
        # 3. Commit with message derived from events
        auto_commit(
            command=command,
            diffable_adapter=self._diffable_adapter,
            git_adapter=self._git_adapter,
            event_bus=self._event_bus,
        )


# ============================================================
# Exports
# ============================================================

__all__ = [
    "VersionControlListener",
    "MUTATION_EVENTS",
]
