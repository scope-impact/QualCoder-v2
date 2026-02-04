"""Version Control Listener - Subscribes to mutations and triggers auto-commit with debouncing."""

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

MUTATION_EVENTS: tuple[str, ...] = (
    # Coding
    "coding.code_created",
    "coding.code_updated",
    "coding.code_deleted",
    "coding.category_created",
    "coding.category_deleted",
    "coding.segment_coded",
    "coding.segment_uncoded",
    "coding.segment_memo_updated",
    # Sources
    "sources.source_imported",
    "sources.source_deleted",
    "sources.source_updated",
    # Cases
    "cases.case_created",
    "cases.case_updated",
    "cases.case_deleted",
    "cases.attribute_added",
    "cases.attribute_updated",
    # Folders
    "folders.folder_created",
    "folders.folder_deleted",
    "folders.source_moved",
)


class VersionControlListener:
    """Batches mutation events with debouncing and triggers auto-commit."""

    DEBOUNCE_MS = 500

    def __init__(
        self,
        event_bus: EventBus,
        diffable_adapter: SqliteDiffableAdapter,
        git_adapter: GitRepositoryAdapter,
        project_path: Path,
    ) -> None:
        self._event_bus = event_bus
        self._diffable_adapter = diffable_adapter
        self._git_adapter = git_adapter
        self._project_path = project_path
        self._pending_events: list[Any] = []
        self._timer: QTimer | None = None
        self._subscriptions: list[Subscription] = []
        self._enabled: bool = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def pending_event_count(self) -> int:
        return len(self._pending_events)

    def enable(self) -> None:
        """Enable the listener and subscribe to mutation events."""
        if self._enabled:
            return
        self._enabled = True
        for event_type in MUTATION_EVENTS:
            subscription = self._event_bus.subscribe(event_type, self._on_mutation)
            self._subscriptions.append(subscription)

    def disable(self) -> None:
        """Disable the listener and flush any pending events."""
        if not self._enabled:
            return
        self._enabled = False

        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        if self._pending_events:
            self._flush()

        for subscription in self._subscriptions:
            subscription.cancel()
        self._subscriptions.clear()

    def _on_mutation(self, event: Any) -> None:
        """Handle a mutation event - add to pending and reset timer."""
        if not self._enabled:
            return
        self._pending_events.append(event)
        self._reset_timer()

    def _reset_timer(self) -> None:
        """Reset the debounce timer."""
        if self._timer is not None:
            self._timer.stop()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._flush)
        self._timer.start(self.DEBOUNCE_MS)

    def _flush(self) -> None:
        """Flush pending events via auto_commit command handler."""
        if not self._pending_events:
            return

        events_to_commit = tuple(self._pending_events)
        self._pending_events.clear()

        if self._timer is not None:
            self._timer.stop()
            self._timer = None

        from src.contexts.projects.core.commandHandlers.auto_commit import auto_commit
        from src.contexts.projects.core.vcs_commands import AutoCommitCommand

        command = AutoCommitCommand(
            project_path=str(self._project_path),
            events=list(events_to_commit),
        )
        auto_commit(
            command=command,
            diffable_adapter=self._diffable_adapter,
            git_adapter=self._git_adapter,
            event_bus=self._event_bus,
        )
