"""
Project Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Project context into Qt signals
for reactive UI updates.

Usage:
    from src.application.projects.signal_bridge import ProjectSignalBridge
    from src.application.event_bus import get_event_bus

    bridge = ProjectSignalBridge.instance(get_event_bus())
    bridge.project_opened.connect(on_project_opened)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.protocols import EventConverter
from src.domain.projects.events import (
    NavigatedToSegment,
    ProjectClosed,
    ProjectCreated,
    ProjectOpened,
    ProjectRenamed,
    ScreenChanged,
    SourceAdded,
    SourceOpened,
    SourceRemoved,
    SourceRenamed,
    SourceStatusChanged,
)


# =============================================================================
# Payloads - Data transferred via signals
# =============================================================================


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ProjectPayload:
    """Payload for project-related signals."""

    event_type: str
    path: str
    name: str | None = None
    memo: str | None = None
    timestamp: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class SourcePayload:
    """Payload for source-related signals."""

    event_type: str
    source_id: int
    name: str
    source_type: str
    file_path: str | None = None
    file_size: int = 0
    origin: str | None = None
    memo: str | None = None
    status: str | None = None
    timestamp: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class NavigationPayload:
    """Payload for navigation-related signals."""

    event_type: str
    from_screen: str | None = None
    to_screen: str | None = None
    source_id: int | None = None
    position_start: int | None = None
    position_end: int | None = None
    timestamp: datetime = field(default_factory=_now)


# =============================================================================
# Converters - Transform events to payloads
# =============================================================================


class ProjectCreatedConverter(EventConverter):
    """Convert ProjectCreated event to payload."""

    def convert(self, event: ProjectCreated) -> ProjectPayload:
        return ProjectPayload(
            event_type="projects.project_created",
            path=str(event.path),
            name=event.name,
            memo=event.memo,
        )


class ProjectOpenedConverter(EventConverter):
    """Convert ProjectOpened event to payload."""

    def convert(self, event: ProjectOpened) -> ProjectPayload:
        return ProjectPayload(
            event_type="projects.project_opened",
            path=str(event.path),
            name=event.name,
        )


class ProjectClosedConverter(EventConverter):
    """Convert ProjectClosed event to payload."""

    def convert(self, event: ProjectClosed) -> ProjectPayload:
        return ProjectPayload(
            event_type="projects.project_closed",
            path=str(event.path),
        )


class ProjectRenamedConverter(EventConverter):
    """Convert ProjectRenamed event to payload."""

    def convert(self, event: ProjectRenamed) -> ProjectPayload:
        return ProjectPayload(
            event_type="projects.project_renamed",
            path=str(event.path),
            name=event.new_name,
        )


class SourceAddedConverter(EventConverter):
    """Convert SourceAdded event to payload."""

    def convert(self, event: SourceAdded) -> SourcePayload:
        return SourcePayload(
            event_type="projects.source_added",
            source_id=event.source_id.value,
            name=event.name,
            source_type=event.source_type.value,
            file_path=str(event.file_path) if event.file_path else None,
            file_size=event.file_size,
            origin=event.origin,
            memo=event.memo,
        )


class SourceRemovedConverter(EventConverter):
    """Convert SourceRemoved event to payload."""

    def convert(self, event: SourceRemoved) -> SourcePayload:
        return SourcePayload(
            event_type="projects.source_removed",
            source_id=event.source_id.value,
            name=event.name,
            source_type="",
        )


class SourceRenamedConverter(EventConverter):
    """Convert SourceRenamed event to payload."""

    def convert(self, event: SourceRenamed) -> SourcePayload:
        return SourcePayload(
            event_type="projects.source_renamed",
            source_id=event.source_id.value,
            name=event.new_name,
            source_type="",
        )


class SourceOpenedConverter(EventConverter):
    """Convert SourceOpened event to payload."""

    def convert(self, event: SourceOpened) -> SourcePayload:
        return SourcePayload(
            event_type="projects.source_opened",
            source_id=event.source_id.value,
            name=event.name,
            source_type=event.source_type.value,
        )


class SourceStatusChangedConverter(EventConverter):
    """Convert SourceStatusChanged event to payload."""

    def convert(self, event: SourceStatusChanged) -> SourcePayload:
        return SourcePayload(
            event_type="projects.source_status_changed",
            source_id=event.source_id.value,
            name="",
            source_type="",
            status=event.new_status,
        )


class ScreenChangedConverter(EventConverter):
    """Convert ScreenChanged event to payload."""

    def convert(self, event: ScreenChanged) -> NavigationPayload:
        return NavigationPayload(
            event_type="projects.screen_changed",
            from_screen=event.from_screen,
            to_screen=event.to_screen,
        )


class NavigatedToSegmentConverter(EventConverter):
    """Convert NavigatedToSegment event to payload."""

    def convert(self, event: NavigatedToSegment) -> NavigationPayload:
        return NavigationPayload(
            event_type="projects.navigated_to_segment",
            source_id=event.source_id.value,
            position_start=event.position_start,
            position_end=event.position_end,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class ProjectSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Project bounded context.

    Emits Qt signals when domain events occur, enabling reactive UI updates.

    Signals:
        project_created: Emitted when a new project is created
        project_opened: Emitted when a project is opened
        project_closed: Emitted when a project is closed
        project_renamed: Emitted when a project is renamed
        source_added: Emitted when a source is added to the project
        source_removed: Emitted when a source is removed
        source_renamed: Emitted when a source is renamed
        source_opened: Emitted when a source is opened for viewing
        source_status_changed: Emitted when a source's status changes
        screen_changed: Emitted when user navigates to a different screen
        navigated_to_segment: Emitted when navigating to a specific segment

    Usage:
        bridge = ProjectSignalBridge.instance(event_bus)
        bridge.project_opened.connect(self._on_project_opened)
        bridge.start()
    """

    # Project signals
    project_created = Signal(object)
    project_opened = Signal(object)
    project_closed = Signal(object)
    project_renamed = Signal(object)

    # Source signals
    source_added = Signal(object)
    source_removed = Signal(object)
    source_renamed = Signal(object)
    source_opened = Signal(object)
    source_status_changed = Signal(object)

    # Navigation signals
    screen_changed = Signal(object)
    navigated_to_segment = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "projects"

    def _register_converters(self) -> None:
        """Register all event converters."""
        # Project events
        self.register_converter(
            "projects.project_created",
            ProjectCreatedConverter(),
            "project_created",
        )
        self.register_converter(
            "projects.project_opened",
            ProjectOpenedConverter(),
            "project_opened",
        )
        self.register_converter(
            "projects.project_closed",
            ProjectClosedConverter(),
            "project_closed",
        )
        self.register_converter(
            "projects.project_renamed",
            ProjectRenamedConverter(),
            "project_renamed",
        )

        # Source events
        self.register_converter(
            "projects.source_added",
            SourceAddedConverter(),
            "source_added",
        )
        self.register_converter(
            "projects.source_removed",
            SourceRemovedConverter(),
            "source_removed",
        )
        self.register_converter(
            "projects.source_renamed",
            SourceRenamedConverter(),
            "source_renamed",
        )
        self.register_converter(
            "projects.source_opened",
            SourceOpenedConverter(),
            "source_opened",
        )
        self.register_converter(
            "projects.source_status_changed",
            SourceStatusChangedConverter(),
            "source_status_changed",
        )

        # Navigation events
        self.register_converter(
            "projects.screen_changed",
            ScreenChangedConverter(),
            "screen_changed",
        )
        self.register_converter(
            "projects.navigated_to_segment",
            NavigatedToSegmentConverter(),
            "navigated_to_segment",
        )
