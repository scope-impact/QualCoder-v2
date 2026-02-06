"""
Project Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Project context into Qt signals
for reactive UI updates.

Usage:
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
    from src.shared.infra.event_bus import get_event_bus

    bridge = ProjectSignalBridge.instance(get_event_bus())
    bridge.project_opened.connect(on_project_opened)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.contexts.projects.core.events import (
    FolderCreated,
    FolderDeleted,
    FolderRenamed,
    NavigatedToSegment,
    ProjectClosed,
    ProjectCreated,
    ProjectOpened,
    ProjectRenamed,
    ScreenChanged,
    SourceAdded,
    SourceMovedToFolder,
    SourceOpened,
    SourceRemoved,
    SourceRenamed,
    SourceStatusChanged,
)
from src.contexts.projects.core.vcs_events import (
    SnapshotCreated,
    SnapshotRestored,
    VersionControlInitialized,
)
from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter

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
    session_id: str = "local"
    is_ai_action: bool = False


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
    session_id: str = "local"
    is_ai_action: bool = False


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
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class FolderPayload:
    """Payload for folder events."""

    event_type: str
    folder_id: int
    name: str
    parent_id: int | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SourceMovedPayload:
    """Payload for source moved events."""

    event_type: str
    source_id: int
    old_folder_id: int | None
    new_folder_id: int | None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class SnapshotPayload:
    """Payload for version control snapshot events."""

    event_type: str
    git_sha: str
    message: str
    event_count: int = 0
    ref: str | None = None
    project_path: str | None = None
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


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


class FolderCreatedConverter(EventConverter):
    """Convert FolderCreated event to payload."""

    def convert(self, event: FolderCreated) -> FolderPayload:
        return FolderPayload(
            event_type="projects.folder_created",
            folder_id=event.folder_id.value,
            name=event.name,
            parent_id=event.parent_id.value if event.parent_id else None,
        )


class FolderRenamedConverter(EventConverter):
    """Convert FolderRenamed event to payload."""

    def convert(self, event: FolderRenamed) -> FolderPayload:
        return FolderPayload(
            event_type="projects.folder_renamed",
            folder_id=event.folder_id.value,
            name=event.new_name,
            parent_id=None,  # FolderRenamed event doesn't include parent_id
        )


class FolderDeletedConverter(EventConverter):
    """Convert FolderDeleted event to payload."""

    def convert(self, event: FolderDeleted) -> FolderPayload:
        return FolderPayload(
            event_type="projects.folder_deleted",
            folder_id=event.folder_id.value,
            name=event.name,
            parent_id=None,  # FolderDeleted event doesn't include parent_id
        )


class SourceMovedToFolderConverter(EventConverter):
    """Convert SourceMovedToFolder event to payload."""

    def convert(self, event: SourceMovedToFolder) -> SourceMovedPayload:
        return SourceMovedPayload(
            event_type="projects.source_moved_to_folder",
            source_id=event.source_id.value,
            old_folder_id=event.old_folder_id.value if event.old_folder_id else None,
            new_folder_id=event.new_folder_id.value if event.new_folder_id else None,
        )


class SnapshotCreatedConverter(EventConverter):
    """Convert SnapshotCreated event to payload."""

    def convert(self, event: SnapshotCreated) -> SnapshotPayload:
        return SnapshotPayload(
            event_type="projects.snapshot_created",
            git_sha=event.git_sha,
            message=event.message,
            event_count=event.event_count,
        )


class SnapshotRestoredConverter(EventConverter):
    """Convert SnapshotRestored event to payload."""

    def convert(self, event: SnapshotRestored) -> SnapshotPayload:
        return SnapshotPayload(
            event_type="projects.snapshot_restored",
            git_sha=event.git_sha,
            message="",
            ref=event.ref,
        )


class VersionControlInitializedConverter(EventConverter):
    """Convert VersionControlInitialized event to payload."""

    def convert(self, event: VersionControlInitialized) -> SnapshotPayload:
        return SnapshotPayload(
            event_type="projects.version_control_initialized",
            git_sha="",
            message="Version control initialized",
            project_path=event.project_path,
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
        folder_created: Emitted when a folder is created
        folder_renamed: Emitted when a folder is renamed
        folder_deleted: Emitted when a folder is deleted
        source_moved: Emitted when a source is moved to a different folder
        screen_changed: Emitted when user navigates to a different screen
        navigated_to_segment: Emitted when navigating to a specific segment
        snapshot_created: Emitted when a VCS snapshot is created (auto-commit)
        snapshot_restored: Emitted when database is restored to a snapshot
        version_control_initialized: Emitted when VCS is initialized

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

    # Folder signals
    folder_created = Signal(object)
    folder_renamed = Signal(object)
    folder_deleted = Signal(object)
    source_moved = Signal(object)

    # Version control signals
    snapshot_created = Signal(object)
    snapshot_restored = Signal(object)
    version_control_initialized = Signal(object)

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

        # Folder events
        self.register_converter(
            "projects.folder_created",
            FolderCreatedConverter(),
            "folder_created",
        )
        self.register_converter(
            "projects.folder_renamed",
            FolderRenamedConverter(),
            "folder_renamed",
        )
        self.register_converter(
            "projects.folder_deleted",
            FolderDeletedConverter(),
            "folder_deleted",
        )
        self.register_converter(
            "projects.source_moved_to_folder",
            SourceMovedToFolderConverter(),
            "source_moved",
        )

        # Version control events
        self.register_converter(
            "projects.snapshot_created",
            SnapshotCreatedConverter(),
            "snapshot_created",
        )
        self.register_converter(
            "projects.snapshot_restored",
            SnapshotRestoredConverter(),
            "snapshot_restored",
        )
        self.register_converter(
            "projects.version_control_initialized",
            VersionControlInitializedConverter(),
            "version_control_initialized",
        )
