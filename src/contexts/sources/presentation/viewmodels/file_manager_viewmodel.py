"""
File Manager ViewModel

Connects the FileManagerScreen to source and folder use cases directly.
Handles data transformation between domain entities and UI DTOs.

Architecture (per SKILL.md - calls use cases directly):
    User Action → ViewModel → Use Cases → Domain → Events
                      ↓                              ↓
                    Repo (queries)          SignalBridge → UI Update
                                                     ↓
                                            ViewModel signals → Screen
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from PySide6.QtCore import QObject, Signal

from src.contexts.folders.core.commandHandlers import (
    create_folder,
    delete_folder,
    move_source_to_folder,
    rename_folder,
)
from src.contexts.projects.core.commands import (
    AddSourceCommand,
    CreateFolderCommand,
    DeleteFolderCommand,
    MoveSourceToFolderCommand,
    OpenSourceCommand,
    RemoveSourceCommand,
    RenameFolderCommand,
    UpdateSourceCommand,
)
from src.contexts.projects.core.entities import Folder, Source
from src.contexts.sources.core.commandHandlers import (
    add_source,
    open_source,
    remove_source,
    update_source,
)
from src.shared.common.types import SourceId
from src.shared.infra.signal_bridge.projects import (
    FolderPayload,
    ProjectSignalBridge,
    SourceMovedPayload,
    SourcePayload,
)
from src.shared.presentation.dto import FolderDTO, ProjectSummaryDTO, SourceDTO

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session
    from src.shared.infra.state import ProjectState

logger = logging.getLogger("qualcoder.sources.viewmodel")


class SourceRepository(Protocol):
    """Protocol for source repository - allows mock injection for testing."""

    def get_all(self) -> list[Source]: ...
    def get_by_id(self, source_id) -> Source | None: ...


class FolderRepository(Protocol):
    """Protocol for folder repository - allows mock injection for testing."""

    def get_all(self) -> list[Folder]: ...


class CaseRepository(Protocol):
    """Protocol for case repository - allows mock injection for testing."""

    def get_all(self) -> list[Case]: ...


class SegmentRepository(Protocol):
    """Protocol for segment repository - allows counting segments per source."""

    def count_by_source(self, source_id) -> int: ...


class FileManagerViewModel(QObject):
    """
    ViewModel for the File Manager screen.

    Responsibilities:
    - Transform domain Source entities to UI DTOs
    - Handle user actions by calling use cases directly
    - Provide filtering and search capabilities (via repo)
    - Track selection state for bulk operations
    - React to domain events via SignalBridge

    Follows SKILL.md pattern:
    - Queries → Direct to repo (CQRS)
    - Commands → Use cases
    - Events → SignalBridge → ViewModel signals → Screen

    Signals:
        sources_changed: Emitted when source list changes (add/remove)
        source_updated: Emitted when a source is updated (payload: SourceDTO)
        source_opened: Emitted when a source is opened (payload: SourceDTO)
        folders_changed: Emitted when folder list changes (create/delete/rename)
        source_moved: Emitted when a source is moved to a folder
        summary_changed: Emitted when summary statistics change
        error_occurred: Emitted on errors (payload: str)
    """

    # Signals for UI updates
    sources_changed = Signal()  # Emitted when source list changes
    source_updated = Signal(object)  # SourceDTO
    source_opened = Signal(object)  # SourceDTO
    folders_changed = Signal()  # Emitted when folder list changes
    source_moved = Signal(object)  # SourceMovedPayload
    summary_changed = Signal()  # Emitted when summary changes
    error_occurred = Signal(str)  # Error message

    # Batch import signals
    batch_import_progress = Signal(int, int, str)  # (current, total, filename)
    batch_import_finished = Signal(
        int, int, list
    )  # (imported_count, failed_count, imported_paths)

    def __init__(
        self,
        source_repo: SourceRepository,
        folder_repo: FolderRepository,
        case_repo: CaseRepository,
        state: ProjectState,
        event_bus: EventBus,
        segment_repo: SegmentRepository | None = None,
        signal_bridge: ProjectSignalBridge | None = None,
        session: Session | None = None,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel with direct dependencies.

        Args:
            source_repo: Repository for source operations
            folder_repo: Repository for folder operations
            case_repo: Repository for case queries (for source-case associations)
            state: Project state cache
            event_bus: Event bus for publishing events
            segment_repo: Segment repository for cascade deletion on source removal
            signal_bridge: Signal bridge for reactive updates (optional)
            session: Session for tracking user actions (optional)
            parent: Qt parent object
        """
        super().__init__(parent)
        self._source_repo = source_repo
        self._folder_repo = folder_repo
        self._case_repo = case_repo
        self._state = state
        self._event_bus = event_bus
        self._segment_repo = segment_repo
        self._signal_bridge = signal_bridge
        self._session = session

        # Selection state
        self._selected_source_ids: set[str] = set()
        self._current_source_id: str | None = None

        # Batch operation state — when > 0, signal bridge handlers are
        # suppressed to avoid O(n²) reloads.  A single reload is done
        # when the batch completes.
        self._suppress_reloads: int = 0

        # Batch import state (async)
        self._import_task: asyncio.Task | None = None
        self._import_cancelled: bool = False

        # Connect to signal bridge if provided
        if self._signal_bridge is not None:
            self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to ProjectSignalBridge signals for reactive updates."""
        if self._signal_bridge is None:
            return

        # Source events
        self._signal_bridge.source_added.connect(self._on_source_added)
        self._signal_bridge.source_removed.connect(self._on_source_removed)
        self._signal_bridge.source_renamed.connect(self._on_source_renamed)
        self._signal_bridge.source_opened.connect(self._on_source_opened)
        self._signal_bridge.source_status_changed.connect(
            self._on_source_status_changed
        )

        # Folder events
        self._signal_bridge.folder_created.connect(self._on_folder_created)
        self._signal_bridge.folder_renamed.connect(self._on_folder_renamed)
        self._signal_bridge.folder_deleted.connect(self._on_folder_deleted)
        self._signal_bridge.source_moved.connect(self._on_source_moved)

    def teardown(self) -> None:
        """Disconnect all signal bridge connections. Call before replacing this ViewModel."""
        if self._signal_bridge is None:
            return

        self._signal_bridge.source_added.disconnect(self._on_source_added)
        self._signal_bridge.source_removed.disconnect(self._on_source_removed)
        self._signal_bridge.source_renamed.disconnect(self._on_source_renamed)
        self._signal_bridge.source_opened.disconnect(self._on_source_opened)
        self._signal_bridge.source_status_changed.disconnect(
            self._on_source_status_changed
        )
        self._signal_bridge.folder_created.disconnect(self._on_folder_created)
        self._signal_bridge.folder_renamed.disconnect(self._on_folder_renamed)
        self._signal_bridge.folder_deleted.disconnect(self._on_folder_deleted)
        self._signal_bridge.source_moved.disconnect(self._on_source_moved)

    # =========================================================================
    # Batch suppression
    # =========================================================================

    @contextlib.contextmanager
    def suppress_reloads(self) -> Generator[None, None, None]:
        """Context manager that suppresses per-item UI reloads.

        On exit, emits a single ``sources_changed`` so the UI rebuilds once.

        Usage::

            with viewmodel.suppress_reloads():
                for path in paths:
                    viewmodel.add_source(path)
            # single reload happens here
        """
        self._suppress_reloads += 1
        logger.debug("suppress_reloads: entered (depth=%d)", self._suppress_reloads)
        try:
            yield
        finally:
            self._suppress_reloads = max(0, self._suppress_reloads - 1)
            logger.debug("suppress_reloads: exited (depth=%d)", self._suppress_reloads)
            # Only emit when outermost suppression exits
            if self._suppress_reloads == 0:
                self.sources_changed.emit()
                self.summary_changed.emit()

    # =========================================================================
    # Signal Bridge Handlers - React to domain events
    # =========================================================================

    def _on_source_added(self, _payload: SourcePayload) -> None:
        """Handle source added event.

        Suppressed during batch operations to avoid O(n²) reloads.
        """
        if self._suppress_reloads:
            logger.debug("_on_source_added: suppressed (batch in progress)")
            return
        self.sources_changed.emit()
        self.summary_changed.emit()

    def _on_source_removed(self, payload: SourcePayload) -> None:
        """Handle source removed event.

        Selection cleanup always runs; UI reload is suppressed during batches.
        """
        # Clear selection if deleted source was selected
        self._selected_source_ids.discard(payload.source_id)
        if self._current_source_id == payload.source_id:
            self._current_source_id = None
        if self._suppress_reloads:
            logger.debug("_on_source_removed: suppressed (batch in progress)")
            return
        self.sources_changed.emit()
        self.summary_changed.emit()

    def _on_source_renamed(self, payload: SourcePayload) -> None:
        """Handle source renamed event."""
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_updated.emit(source_dto)

    def _on_source_opened(self, payload: SourcePayload) -> None:
        """Handle source opened event."""
        self._current_source_id = payload.source_id
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_opened.emit(source_dto)

    def _on_source_status_changed(self, payload: SourcePayload) -> None:
        """Handle source status changed event."""
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_updated.emit(source_dto)
        self.summary_changed.emit()

    def _on_folder_created(self, _payload: FolderPayload) -> None:
        """Handle folder created event."""
        self.folders_changed.emit()

    def _on_folder_renamed(self, _payload: FolderPayload) -> None:
        """Handle folder renamed event."""
        self.folders_changed.emit()

    def _on_folder_deleted(self, _payload: FolderPayload) -> None:
        """Handle folder deleted event."""
        self.folders_changed.emit()

    def _on_source_moved(self, payload: SourceMovedPayload) -> None:
        """Handle source moved to folder event.

        Suppressed during batch operations to avoid O(n) reloads.
        """
        if self._suppress_reloads:
            logger.debug("_on_source_moved: suppressed (batch in progress)")
            return
        self.source_moved.emit(payload)
        self.folders_changed.emit()  # Folder source counts changed

    # =========================================================================
    # Load Data - Queries go direct to repo (CQRS)
    # =========================================================================

    def load_sources(self) -> list[SourceDTO]:
        """
        Load all sources and return as DTOs.

        Fetches cases once to avoid N+1 queries during DTO conversion.

        Returns:
            List of SourceDTO objects for UI display
        """
        sources = self._source_repo.get_all()
        cases = self._case_repo.get_all() if self._case_repo else []
        return [self._source_to_dto(s, cases=cases) for s in sources]

    def get_summary(self) -> ProjectSummaryDTO:
        """
        Get project summary statistics.

        Returns:
            ProjectSummaryDTO with counts by type
        """
        sources = self._source_repo.get_all()

        if not sources:
            return ProjectSummaryDTO()

        # Single pass over sources
        type_counts: dict[str, int] = {}
        total_segments = 0
        for s in sources:
            type_counts[s.source_type.value] = (
                type_counts.get(s.source_type.value, 0) + 1
            )
            total_segments += s.code_count

        total_codes = len(self._case_repo.get_all()) if self._case_repo else 0

        return ProjectSummaryDTO(
            total_sources=len(sources),
            text_count=type_counts.get("text", 0),
            audio_count=type_counts.get("audio", 0),
            video_count=type_counts.get("video", 0),
            image_count=type_counts.get("image", 0),
            pdf_count=type_counts.get("pdf", 0),
            total_codes=total_codes,
            total_segments=total_segments,
        )

    def get_current_source(self) -> SourceDTO | None:
        """
        Get the currently open source.

        Returns:
            SourceDTO if a source is open, None otherwise
        """
        if self._current_source_id is None:
            return None

        source = self._source_repo.get_by_id(SourceId(value=self._current_source_id))
        return self._source_to_dto(source) if source else None

    def get_source(self, source_id: str) -> SourceDTO | None:
        """
        Get a specific source by ID.

        Args:
            source_id: ID of the source to retrieve

        Returns:
            SourceDTO if found, None otherwise
        """
        source = self._source_repo.get_by_id(SourceId(value=source_id))
        return self._source_to_dto(source) if source else None

    # =========================================================================
    # Source Commands - Commands go through use cases
    # =========================================================================

    def add_source(
        self,
        path: str,
        origin: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Add a source file to the project.

        Args:
            path: Path to the source file
            origin: Optional origin/category
            memo: Optional memo

        Returns:
            True if successful, False otherwise
        """
        command = AddSourceCommand(
            source_path=path,
            origin=origin,
            memo=memo,
        )

        result = add_source(
            command=command,
            state=self._state,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    # =========================================================================
    # Batch Import — background extraction, main-thread persistence
    # =========================================================================

    @property
    def is_importing(self) -> bool:
        """True while a batch import is running."""
        return self._import_task is not None and not self._import_task.done()

    def import_sources_batch(
        self,
        file_paths: list[str],
        origin: str | None = None,
        memo: str | None = None,
    ) -> None:
        """Start an async batch import.

        Extraction runs in a thread-pool executor; persistence and event
        publishing resume on the main thread after each ``await``.

        Args:
            file_paths: Absolute paths to import.
            origin: Optional origin tag for all imported sources.
            memo: Optional memo for all imported sources.
        """
        if self.is_importing:
            logger.warning("import_sources_batch: import already in progress, ignoring")
            return

        self._import_cancelled = False

        logger.info(
            "import_sources_batch: starting async batch of %d files (origin=%s)",
            len(file_paths),
            origin,
        )

        loop = asyncio.get_event_loop()
        self._import_task = loop.create_task(
            self._import_sources_async(file_paths, origin, memo)
        )

    def cancel_import(self) -> None:
        """Request cancellation of the running batch import."""
        if self.is_importing:
            logger.info("cancel_import: setting cancellation flag")
            self._import_cancelled = True

    async def _import_sources_async(
        self,
        file_paths: list[str],
        origin: str | None,
        memo: str | None,
    ) -> None:
        """Async coroutine that imports files one at a time.

        Heavy extraction runs in a thread pool via ``run_in_executor``.
        After each ``await``, execution resumes on the main thread, so
        persistence and signal emission are automatically thread-safe.
        """
        from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
        from src.contexts.projects.core.events import SourceAdded
        from src.contexts.projects.core.invariants import detect_source_type
        from src.contexts.sources.core.commandHandlers.import_file_source import (
            extract_text,
        )
        from src.shared.common.types import SourceId

        loop = asyncio.get_running_loop()
        total = len(file_paths)
        imported = 0
        failed = 0
        imported_paths: list[str] = []
        batch_start = time.perf_counter()

        # Snapshot existing names for uniqueness check
        existing_names = frozenset(s.name.lower() for s in self._source_repo.get_all())
        seen_names: set[str] = set()

        self._suppress_reloads += 1
        try:
            for idx, raw_path in enumerate(file_paths):
                if self._import_cancelled:
                    logger.info("batch_import: cancelled after %d/%d files", idx, total)
                    break

                file_path = Path(raw_path)
                file_start = time.perf_counter()

                try:
                    # --- Validate (main thread, fast) ---
                    source_type = detect_source_type(file_path)
                    if source_type == SourceType.UNKNOWN:
                        raise ValueError(f"Unsupported file type: {file_path.suffix}")

                    name = file_path.name
                    if name.lower() in existing_names or name.lower() in seen_names:
                        raise ValueError(f"Duplicate source name: {name}")

                    file_size = file_path.stat().st_size

                    # --- Extract text in thread pool (THE SLOW PART) ---
                    fulltext = await loop.run_in_executor(
                        None, extract_text, source_type, file_path
                    )

                    # --- Back on main thread: build entity, persist, publish ---
                    source = Source(
                        id=SourceId.new(),
                        name=name,
                        source_type=source_type,
                        status=SourceStatus.IMPORTED,
                        file_path=file_path,
                        file_size=file_size,
                        origin=origin,
                        memo=memo,
                        fulltext=fulltext,
                    )

                    self._source_repo.save(source)

                    event = SourceAdded.create(
                        source_id=source.id,
                        name=source.name,
                        source_type=source.source_type,
                        file_path=source.file_path,
                        file_size=source.file_size,
                        origin=source.origin,
                        memo=source.memo,
                        owner=None,
                    )
                    self._event_bus.publish(event)

                    seen_names.add(name.lower())
                    imported += 1
                    imported_paths.append(raw_path)

                    elapsed_ms = (time.perf_counter() - file_start) * 1000
                    logger.info(
                        "batch_import: [%d/%d] imported %s (%.1fms)",
                        idx + 1,
                        total,
                        name,
                        elapsed_ms,
                    )

                except Exception as exc:
                    failed += 1
                    elapsed_ms = (time.perf_counter() - file_start) * 1000
                    logger.warning(
                        "batch_import: [%d/%d] failed %s: %s (%.1fms)",
                        idx + 1,
                        total,
                        file_path.name,
                        exc,
                        elapsed_ms,
                    )

                self.batch_import_progress.emit(idx + 1, total, file_path.name)

        finally:
            self._suppress_reloads = max(0, self._suppress_reloads - 1)

        batch_ms = (time.perf_counter() - batch_start) * 1000
        logger.info(
            "batch_import: done — %d imported, %d failed (%.1fms total)",
            imported,
            failed,
            batch_ms,
        )
        self._import_task = None  # Release coroutine frame + locals
        self.batch_import_finished.emit(imported, failed, imported_paths)
        self.sources_changed.emit()
        self.summary_changed.emit()

    def remove_source(self, source_id: str) -> bool:
        """
        Remove a source from the project.

        Args:
            source_id: ID of source to remove

        Returns:
            True if successful, False otherwise
        """
        command = RemoveSourceCommand(source_id=source_id)

        result = remove_source(
            command=command,
            state=self._state,
            source_repo=self._source_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        if result.is_success:
            self._selected_source_ids.discard(source_id)
            if self._current_source_id == source_id:
                self._current_source_id = None
            return True

        return False

    def remove_sources(self, source_ids: list[str]) -> bool:
        """
        Remove multiple sources from the project.

        Suppresses per-item UI reloads and does a single reload at the end.

        Args:
            source_ids: List of source IDs to remove

        Returns:
            True if all successful, False if any failed
        """
        total = len(source_ids)
        logger.info("remove_sources: removing %d source(s)", total)
        all_success = True
        with self.suppress_reloads():
            for i, source_id in enumerate(source_ids):
                logger.debug("remove_sources: [%d/%d] %s", i + 1, total, source_id)
                if not self.remove_source(source_id):
                    logger.warning("remove_sources: failed to remove %s", source_id)
                    all_success = False
        # suppress_reloads emits sources_changed on exit
        logger.info("remove_sources: done, all_success=%s", all_success)
        return all_success

    def get_segment_count_for_source(self, source_id: str) -> int:
        """
        Get the count of coded segments for a source.

        Use this before deleting a source to warn users if coded data exists.

        Args:
            source_id: ID of source to check

        Returns:
            Number of coded segments for this source
        """
        if self._segment_repo:
            return self._segment_repo.count_by_source(SourceId(value=source_id))
        return 0

    def open_source(self, source_id: str) -> bool:
        """
        Open a source for viewing/coding.

        Args:
            source_id: ID of source to open

        Returns:
            True if successful, False otherwise
        """
        command = OpenSourceCommand(source_id=source_id)

        result = open_source(
            command=command,
            state=self._state,
            event_bus=self._event_bus,
            source_repo=self._source_repo,
            session=self._session,
        )

        if result.is_success:
            self._current_source_id = source_id
            return True

        return False

    def update_source(
        self,
        source_id: str,
        memo: str | None = None,
        origin: str | None = None,
        status: str | None = None,
    ) -> bool:
        """
        Update source properties.

        Args:
            source_id: ID of source to update
            memo: Optional memo text
            origin: Optional origin/category
            status: Optional status

        Returns:
            True if successful, False otherwise
        """
        command = UpdateSourceCommand(
            source_id=source_id,
            memo=memo,
            origin=origin,
            status=status,
        )

        result = update_source(
            command=command,
            state=self._state,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    # =========================================================================
    # Selection
    # =========================================================================

    def select_sources(self, source_ids: list[str]) -> None:
        """
        Set the selected sources.

        Args:
            source_ids: List of source IDs to select
        """
        self._selected_source_ids = set(source_ids)

    def toggle_source_selection(self, source_id: str) -> None:
        """
        Toggle selection state of a source.

        Args:
            source_id: ID of source to toggle
        """
        if source_id in self._selected_source_ids:
            self._selected_source_ids.discard(source_id)
        else:
            self._selected_source_ids.add(source_id)

    def clear_selection(self) -> None:
        """Clear all selected sources."""
        self._selected_source_ids.clear()

    def get_selected_sources(self) -> list[SourceDTO]:
        """
        Get the currently selected sources.

        Returns:
            List of selected SourceDTO objects
        """
        sources = self._source_repo.get_all()
        return [
            self._source_to_dto(s)
            for s in sources
            if s.id.value in self._selected_source_ids
        ]

    def get_selected_count(self) -> int:
        """Get the number of selected sources."""
        return len(self._selected_source_ids)

    # =========================================================================
    # Filtering and Search - Queries go direct to repo
    # =========================================================================

    def filter_sources(
        self,
        source_type: str | None = None,
        status: str | None = None,
    ) -> list[SourceDTO]:
        """
        Filter sources by type and/or status.

        Args:
            source_type: Filter by type (text, audio, video, image, pdf)
            status: Filter by status (imported, coded, etc.)

        Returns:
            Filtered list of SourceDTO objects
        """
        sources = self._source_repo.get_all()

        if source_type:
            sources = [s for s in sources if s.source_type.value == source_type]

        if status:
            sources = [s for s in sources if s.status.value == status]

        return [self._source_to_dto(s) for s in sources]

    def search_sources(self, query: str) -> list[SourceDTO]:
        """
        Search sources by name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching SourceDTO objects
        """
        sources = self._source_repo.get_all()
        query_lower = query.lower()

        matching = [s for s in sources if query_lower in s.name.lower()]

        return [self._source_to_dto(s) for s in matching]

    # =========================================================================
    # Folder Commands - Commands go through use cases
    # =========================================================================

    def create_folder(self, name: str, parent_id: str | None = None) -> bool:
        """
        Create a new folder.

        Args:
            name: Name of the folder to create
            parent_id: Optional parent folder ID for nested folders

        Returns:
            True if successful, False otherwise
        """
        command = CreateFolderCommand(name=name, parent_id=parent_id)

        result = create_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    def rename_folder(self, folder_id: str, new_name: str) -> bool:
        """
        Rename a folder.

        Args:
            folder_id: ID of the folder to rename
            new_name: New name for the folder

        Returns:
            True if successful, False otherwise
        """
        command = RenameFolderCommand(folder_id=folder_id, new_name=new_name)

        result = rename_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    def delete_folder(self, folder_id: str) -> bool:
        """
        Delete an empty folder.

        Args:
            folder_id: ID of the folder to delete

        Returns:
            True if successful, False otherwise
        """
        command = DeleteFolderCommand(folder_id=folder_id)

        result = delete_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    def move_source_to_folder(self, source_id: str, folder_id: str | None) -> bool:
        """
        Move a source to a folder (or root if None).

        Args:
            source_id: ID of the source to move
            folder_id: Target folder ID, or None to move to root

        Returns:
            True if successful, False otherwise
        """
        command = MoveSourceToFolderCommand(source_id=source_id, folder_id=folder_id)

        result = move_source_to_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )

        return result.is_success

    def get_folders(self) -> list[FolderDTO]:
        """
        Get all folders as DTOs.

        Fetches sources once to avoid N+1 queries during folder count.

        Returns:
            List of FolderDTO objects for UI display
        """
        folders = self._folder_repo.get_all()
        sources = self._source_repo.get_all()
        # Pre-compute folder → source count map
        folder_counts: dict[str, int] = {}
        for s in sources:
            if s.folder_id:
                fid = s.folder_id.value
                folder_counts[fid] = folder_counts.get(fid, 0) + 1
        return [
            self._folder_to_dto(f, folder_source_count=folder_counts.get(f.id.value, 0))
            for f in folders
        ]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _source_to_dto(self, source: Source, cases: list | None = None) -> SourceDTO:
        """Convert a Source entity to DTO.

        Args:
            source: The source entity to convert.
            cases: Pre-fetched case list to avoid N+1 queries. If None, fetches from repo.
        """
        source_id_value = source.id.value
        if cases is None:
            cases = self._case_repo.get_all() if self._case_repo else []
        case_names = [case.name for case in cases if source_id_value in case.source_ids]

        return SourceDTO(
            id=str(source.id.value),
            name=source.name,
            source_type=source.source_type.value,
            status=source.status.value,
            file_size=source.file_size,
            code_count=source.code_count,
            memo=source.memo,
            origin=source.origin,
            cases=case_names,
            modified_at=source.modified_at.isoformat() if source.modified_at else None,
        )

    def _folder_to_dto(
        self, folder: Folder, folder_source_count: int | None = None
    ) -> FolderDTO:
        """Convert a Folder entity to DTO.

        Args:
            folder: The folder entity to convert.
            folder_source_count: Pre-computed source count. If None, fetches from repo.
        """
        if folder_source_count is None:
            sources = self._source_repo.get_all()
            folder_source_count = sum(
                1
                for s in sources
                if s.folder_id and s.folder_id.value == folder.id.value
            )

        return FolderDTO(
            id=str(folder.id.value),
            name=folder.name,
            parent_id=str(folder.parent_id.value) if folder.parent_id else None,
            source_count=folder_source_count,
        )
