"""Version Control Listener - Subscribes to mutations and triggers auto-commit with debouncing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QTimer

logger = logging.getLogger(__name__)

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
    "projects.source_added",
    "projects.source_removed",
    "projects.source_updated",
    # Cases
    "cases.case_created",
    "cases.case_updated",
    "cases.case_deleted",
    "cases.attribute_set",
    "cases.attribute_removed",
    "cases.source_linked",
    "cases.source_unlinked",
    # Folders
    "folders.folder_created",
    "folders.folder_deleted",
    "folders.source_moved",
)


class VersionControlListener:
    """Batches mutation events with debouncing and triggers auto-commit.

    All mutation events now arrive on the Qt main thread (marshalled by the
    MCP server's _MainThreadExecutor), so we can use a simple QTimer for
    debouncing without any threading concerns.
    """

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
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(self.DEBOUNCE_MS)
        self._timer.timeout.connect(self._flush)
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
        logger.info(
            "VCS listener enabled: subscribed to %d mutation event types",
            len(MUTATION_EVENTS),
        )

    def disable(self) -> None:
        """Disable the listener and flush any pending events."""
        if not self._enabled:
            return
        self._enabled = False
        pending_count = len(self._pending_events)
        logger.info(
            "VCS listener disabling (pending_events=%d, flushing=%s)",
            pending_count,
            pending_count > 0,
        )

        self._timer.stop()

        if self._pending_events:
            self._flush()

        for subscription in self._subscriptions:
            subscription.cancel()
        self._subscriptions.clear()
        logger.debug("VCS listener disabled, subscriptions cleared")

    def _on_mutation(self, event: Any) -> None:
        """Handle a mutation event - add to pending and restart timer."""
        if not self._enabled:
            return
        event_type = getattr(event, "event_type", type(event).__name__)
        self._pending_events.append(event)
        logger.debug(
            "VCS mutation received: %s (pending=%d, debounce=%dms)",
            event_type,
            len(self._pending_events),
            self.DEBOUNCE_MS,
        )
        self._timer.start()  # (re)starts the single-shot timer

    def _flush(self) -> None:
        """Flush pending events via auto_commit command handler."""
        if not self._pending_events:
            return
        events_to_commit = tuple(self._pending_events)
        self._pending_events.clear()
        self._timer.stop()

        logger.debug(
            "VCS debounce timer fired — flushing %d event(s) for auto-commit",
            len(events_to_commit),
        )

        from src.contexts.projects.core.commandHandlers.auto_commit import auto_commit
        from src.contexts.projects.core.vcs_commands import AutoCommitCommand

        command = AutoCommitCommand(
            project_path=str(self._project_path),
            events=list(events_to_commit),
        )
        result = auto_commit(
            command=command,
            diffable_adapter=self._diffable_adapter,
            git_adapter=self._git_adapter,
            event_bus=self._event_bus,
        )
        if result.is_failure:
            logger.error(
                "VCS auto-commit failed: %s [%s]", result.error, result.error_code
            )
        else:
            logger.info(
                "VCS auto-commit succeeded (%d events)", len(events_to_commit)
            )
