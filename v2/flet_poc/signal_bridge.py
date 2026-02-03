"""
FletSignalBridge - Connects EventBus domain events to Flet UI updates.

This demonstrates how the existing QualCoder EventBus architecture
integrates with Flet's reactive UI model.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
import flet as ft

from event_bus import (
    EventBus,
    DomainEvent,
    CodeCreated,
    CodeDeleted,
    SegmentCoded,
    SourceImported,
    Subscription,
)


@dataclass
class ActivityItem:
    """Represents an activity in the feed."""

    text: str
    time: str
    color: str  # primary, accent, sage, rose


@dataclass
class FletSignalBridge:
    """
    Bridge between EventBus domain events and Flet UI updates.

    This is the Flet equivalent of QualCoder's BaseSignalBridge.
    Instead of Qt signals, we use callbacks and page.update().
    """

    event_bus: EventBus
    page: ft.Page | None = None

    # Callbacks for UI updates
    on_code_created: Callable[[CodeCreated], None] | None = None
    on_code_deleted: Callable[[CodeDeleted], None] | None = None
    on_segment_coded: Callable[[SegmentCoded], None] | None = None
    on_source_imported: Callable[[SourceImported], None] | None = None
    on_activity: Callable[[ActivityItem], None] | None = None

    _subscriptions: list[Subscription] = field(default_factory=list)

    def bind_page(self, page: ft.Page) -> None:
        """Bind to a Flet page for UI updates."""
        self.page = page

    def start(self) -> None:
        """Start listening to events."""
        # Subscribe to domain events
        self._subscriptions.append(
            self.event_bus.subscribe_type(CodeCreated, self._handle_code_created)
        )
        self._subscriptions.append(
            self.event_bus.subscribe_type(CodeDeleted, self._handle_code_deleted)
        )
        self._subscriptions.append(
            self.event_bus.subscribe_type(SegmentCoded, self._handle_segment_coded)
        )
        self._subscriptions.append(
            self.event_bus.subscribe_type(SourceImported, self._handle_source_imported)
        )

    def stop(self) -> None:
        """Stop listening to events."""
        for sub in self._subscriptions:
            sub.cancel()
        self._subscriptions.clear()

    def _handle_code_created(self, event: CodeCreated) -> None:
        """Handle code creation event."""
        if self.on_code_created:
            self.on_code_created(event)

        # Emit activity
        self._emit_activity(
            ActivityItem(
                text=f"Created new code '{event.name}'",
                time="Just now",
                color="primary",
            )
        )

        self._update_ui()

    def _handle_code_deleted(self, event: CodeDeleted) -> None:
        """Handle code deletion event."""
        if self.on_code_deleted:
            self.on_code_deleted(event)

        self._emit_activity(
            ActivityItem(
                text=f"Deleted code '{event.name}'",
                time="Just now",
                color="rose",
            )
        )

        self._update_ui()

    def _handle_segment_coded(self, event: SegmentCoded) -> None:
        """Handle segment coding event."""
        if self.on_segment_coded:
            self.on_segment_coded(event)

        preview = event.text_preview[:50] + "..." if len(event.text_preview) > 50 else event.text_preview
        self._emit_activity(
            ActivityItem(
                text=f"Applied '{event.code_name}' to '{event.source_name}'",
                time="Just now",
                color="accent",
            )
        )

        self._update_ui()

    def _handle_source_imported(self, event: SourceImported) -> None:
        """Handle source import event."""
        if self.on_source_imported:
            self.on_source_imported(event)

        self._emit_activity(
            ActivityItem(
                text=f"Imported '{event.name}' ({event.word_count:,} words)",
                time="Just now",
                color="sage",
            )
        )

        self._update_ui()

    def _emit_activity(self, activity: ActivityItem) -> None:
        """Emit activity to the activity feed."""
        if self.on_activity:
            self.on_activity(activity)

    def _update_ui(self) -> None:
        """Trigger Flet UI update."""
        if self.page:
            self.page.update()
