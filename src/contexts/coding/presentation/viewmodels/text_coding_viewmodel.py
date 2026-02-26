"""
Text Coding ViewModel

Connects the TextCodingScreen to the Coordinator and CodingSignalBridge.
Handles data transformation between domain entities and UI DTOs.

Architecture:
    User Action → ViewModel → Coordinator → Use Cases → Domain → Events
                                                                    ↓
    UI Update ← ViewModel ← SignalBridge ←─────────────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from PySide6.QtCore import QObject, Signal

from src.contexts.coding.core.commands import (
    ApplyCodeCommand,
    CreateCategoryCommand,
    CreateCodeCommand,
    DeleteCodeCommand,
    MoveCodeToCategoryCommand,
    RemoveCodeCommand,
    RenameCodeCommand,
    UpdateCodeMemoCommand,
)
from src.contexts.coding.interface.signal_bridge import (
    CategoryPayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)
from src.shared.infra.telemetry import traced
from src.shared.presentation.dto import (
    CodeCategoryDTO,
    CodeDTO,
    NavigationDTO,
    SelectedCodeDTO,
    TextCodingDataDTO,
)

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Code, TextSegment
    from src.shared.common.operation_result import OperationResult


class CodingProvider(Protocol):
    """Protocol for coding operations."""

    def create_code(self, command: CreateCodeCommand) -> OperationResult: ...
    def rename_code(self, command: RenameCodeCommand) -> OperationResult: ...
    def delete_code(self, command: DeleteCodeCommand) -> OperationResult: ...
    def update_code_memo(self, command: UpdateCodeMemoCommand) -> OperationResult: ...
    def move_code_to_category(
        self, command: MoveCodeToCategoryCommand
    ) -> OperationResult: ...
    def apply_code(self, command: ApplyCodeCommand) -> OperationResult: ...
    def remove_segment(self, command: RemoveCodeCommand) -> OperationResult: ...
    def create_category(self, command: CreateCategoryCommand) -> OperationResult: ...
    def get_all_codes(self) -> list: ...
    def get_all_categories(self) -> list: ...
    def get_segments_for_source(self, source_id: int) -> list: ...
    def get_segment_counts_by_code(self) -> dict[int, int]: ...


class TextCodingViewModel(QObject):
    """
    ViewModel for the Text Coding screen.

    Responsibilities:
    - Transform domain entities to UI DTOs
    - Handle user actions by calling controller commands
    - React to domain events via SignalBridge
    - Emit signals when UI should update

    Signals:
        data_changed: Emitted when any data changes, with full DTO
        codes_changed: Emitted when codes list changes
        segments_changed: Emitted when segments change for current source
        code_selected: Emitted when a code is selected
        error_occurred: Emitted when an operation fails
    """

    data_changed = Signal(object)  # TextCodingDataDTO
    codes_changed = Signal(list)  # list[CodeCategoryDTO]
    segments_changed = Signal(list)  # list of segment info
    code_selection_changed = Signal(object)  # SelectedCodeDTO
    error_occurred = Signal(str)

    def __init__(
        self,
        controller: CodingProvider,
        signal_bridge: CodingSignalBridge,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            controller: The coding provider (coordinator) for commands
            signal_bridge: The signal bridge for reactive updates
            parent: Optional Qt parent
        """
        super().__init__(parent)
        self._controller = controller
        self._signal_bridge = signal_bridge

        # Current state
        self._current_source_id: int | None = None
        self._selected_code_id: int | None = None

        # Connect to signal bridge
        self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to CodingSignalBridge signals."""
        self._signal_bridge.code_created.connect(self._on_code_created)
        self._signal_bridge.code_renamed.connect(self._on_code_renamed)
        self._signal_bridge.code_color_changed.connect(self._on_code_color_changed)
        self._signal_bridge.code_deleted.connect(self._on_code_deleted)
        self._signal_bridge.code_memo_updated.connect(self._on_code_memo_updated)
        self._signal_bridge.code_moved.connect(self._on_code_moved)
        self._signal_bridge.codes_merged.connect(self._on_codes_merged)
        self._signal_bridge.category_created.connect(self._on_category_created)
        self._signal_bridge.category_deleted.connect(self._on_category_deleted)
        self._signal_bridge.segment_coded.connect(self._on_segment_coded)
        self._signal_bridge.segment_uncoded.connect(self._on_segment_uncoded)

    def teardown(self) -> None:
        """Disconnect all signal bridge connections. Call before replacing this ViewModel."""
        self._signal_bridge.code_created.disconnect(self._on_code_created)
        self._signal_bridge.code_renamed.disconnect(self._on_code_renamed)
        self._signal_bridge.code_color_changed.disconnect(self._on_code_color_changed)
        self._signal_bridge.code_deleted.disconnect(self._on_code_deleted)
        self._signal_bridge.code_memo_updated.disconnect(self._on_code_memo_updated)
        self._signal_bridge.code_moved.disconnect(self._on_code_moved)
        self._signal_bridge.codes_merged.disconnect(self._on_codes_merged)
        self._signal_bridge.category_created.disconnect(self._on_category_created)
        self._signal_bridge.category_deleted.disconnect(self._on_category_deleted)
        self._signal_bridge.segment_coded.disconnect(self._on_segment_coded)
        self._signal_bridge.segment_uncoded.disconnect(self._on_segment_uncoded)

    # =========================================================================
    # Public API - Load Data
    # =========================================================================

    def load_initial_data(self) -> TextCodingDataDTO:
        """
        Load all initial data and return as DTO.

        Returns:
            Complete data bundle for the text coding screen
        """
        categories = self._build_categories_dto()
        return TextCodingDataDTO(
            files=[],  # TODO: Load from sources context
            categories=categories,
            document=None,
            document_stats=None,
            selected_code=None,
            overlapping_segments=[],
            file_memo=None,
            navigation=NavigationDTO(current=1, total=1),
            coders=["default"],
            selected_coder="default",
        )

    def load_codes(self) -> list[CodeCategoryDTO]:
        """
        Load all codes grouped by category.

        Returns:
            List of category DTOs with their codes
        """
        return self._build_categories_dto()

    @traced("load_segments_for_source")
    def load_segments_for_source(self, source_id: int) -> list[dict]:
        """
        Load segments for a source document.

        Args:
            source_id: The source document ID

        Returns:
            List of segment information for highlighting
        """
        self._current_source_id = source_id
        segments = self._controller.get_segments_for_source(source_id)
        return self._segments_to_highlight_info(segments)

    def set_current_source(self, source_id: int) -> None:
        """Set the current source being viewed and load its segments."""
        self._current_source_id = source_id
        self._emit_segments_changed()

    # =========================================================================
    # Public API - Commands
    # =========================================================================

    def _execute(self, method_name: str, command, error_label: str) -> bool:
        """Execute a command on the controller and handle the result.

        Args:
            method_name: Name of the controller method to call
            command: The command object to pass
            error_label: Label for error messages if the command fails

        Returns:
            True if successful, False otherwise
        """
        result = getattr(self._controller, method_name)(command)
        if result.is_success:
            return True
        self.error_occurred.emit(result.error or f"{error_label} failed")
        return False

    def create_code(
        self, name: str, color: str, category_id: int | None = None
    ) -> bool:
        """Create a new code."""
        return self._execute(
            "create_code",
            CreateCodeCommand(name=name, color=color, category_id=category_id),
            "Create code",
        )

    def rename_code(self, code_id: int, new_name: str) -> bool:
        """Rename a code."""
        return self._execute(
            "rename_code",
            RenameCodeCommand(code_id=code_id, new_name=new_name),
            "Rename code",
        )

    def delete_code(self, code_id: int, delete_segments: bool = False) -> bool:
        """Delete a code."""
        return self._execute(
            "delete_code",
            DeleteCodeCommand(code_id=code_id, delete_segments=delete_segments),
            "Delete code",
        )

    def update_code_memo(self, code_id: int, new_memo: str | None) -> bool:
        """Update a code's memo."""
        return self._execute(
            "update_code_memo",
            UpdateCodeMemoCommand(code_id=code_id, new_memo=new_memo),
            "Update code memo",
        )

    def move_code_to_category(self, code_id: int, category_id: int | None) -> bool:
        """Move a code to a different category."""
        return self._execute(
            "move_code_to_category",
            MoveCodeToCategoryCommand(code_id=code_id, category_id=category_id),
            "Move code",
        )

    def apply_code_to_selection(
        self,
        code_id: int,
        source_id: int,
        start: int,
        end: int,
        memo: str | None = None,
    ) -> bool:
        """Apply a code to a text selection."""
        return self._execute(
            "apply_code",
            ApplyCodeCommand(
                code_id=code_id,
                source_id=source_id,
                start_position=start,
                end_position=end,
                memo=memo,
            ),
            "Apply code",
        )

    def remove_segment(self, segment_id: int) -> bool:
        """Remove coding from a segment."""
        return self._execute(
            "remove_segment",
            RemoveCodeCommand(segment_id=segment_id),
            "Remove segment",
        )

    def create_category(self, name: str, parent_id: int | None = None) -> bool:
        """Create a new category."""
        return self._execute(
            "create_category",
            CreateCategoryCommand(name=name, parent_id=parent_id),
            "Create category",
        )

    def select_code(self, code_id: int) -> None:
        """
        Select a code and emit selection changed.

        Args:
            code_id: ID of code to select
        """
        self._selected_code_id = code_id
        code = self._controller.get_code(code_id)

        if code:
            dto = SelectedCodeDTO(
                id=str(code.id.value),
                name=code.name,
                color=code.color.to_hex(),
                memo=code.memo or "",
                example_text=None,
            )
            self.code_selection_changed.emit(dto)

    def find_segment_at_position(
        self, source_id: int, start: int, end: int
    ) -> int | None:
        """
        Find a segment that overlaps with the given position range.

        Used for unmark operations to find the segment to remove.

        Args:
            source_id: The source document ID
            start: Start position of range to check
            end: End position of range to check

        Returns:
            Segment ID if found, None otherwise
        """
        segments = self._controller.get_segments_for_source(source_id)
        for seg in segments:
            # Check if segment overlaps with the query range
            seg_start = seg.position.start
            seg_end = seg.position.end
            if seg_start < end and start < seg_end:
                return seg.id.value
        return None

    # =========================================================================
    # Signal Handlers - React to domain events
    # =========================================================================

    def _refresh_codes_and_selection(self, payload: CodePayload) -> None:
        """Refresh codes list and re-select if the changed code is selected."""
        self._emit_codes_changed()
        if self._selected_code_id == payload.code_id:
            self.select_code(payload.code_id)

    def _on_code_created(self, _payload: CodePayload) -> None:
        """Handle code created event."""
        self._emit_codes_changed()

    def _on_code_renamed(self, payload: CodePayload) -> None:
        """Handle code renamed event."""
        self._refresh_codes_and_selection(payload)

    def _on_code_color_changed(self, payload: CodePayload) -> None:
        """Handle code color changed event."""
        self._refresh_codes_and_selection(payload)

    def _on_code_deleted(self, payload: CodePayload) -> None:
        """Handle code deleted event."""
        self._emit_codes_changed()
        if self._selected_code_id == payload.code_id:
            self._selected_code_id = None
            self.code_selection_changed.emit(None)

    def _on_code_memo_updated(self, payload: CodePayload) -> None:
        """Handle code memo updated event."""
        self._refresh_codes_and_selection(payload)

    def _on_code_moved(self, _payload: CodePayload) -> None:
        """Handle code moved to category event."""
        self._emit_codes_changed()

    def _on_codes_merged(self, _payload) -> None:
        """Handle codes merged event."""
        self._emit_codes_changed()
        self._emit_segments_changed()

    def _on_category_created(self, _payload: CategoryPayload) -> None:
        """Handle category created event."""
        self._emit_codes_changed()

    def _on_category_deleted(self, _payload: CategoryPayload) -> None:
        """Handle category deleted event."""
        self._emit_codes_changed()

    def _on_segment_coded(self, payload: SegmentPayload) -> None:
        """Handle segment coded event."""
        if self._current_source_id == payload.source_id:
            self._emit_segments_changed()

    def _on_segment_uncoded(self, payload: SegmentPayload) -> None:
        """Handle segment uncoded event."""
        if self._current_source_id == payload.source_id:
            self._emit_segments_changed()

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _emit_codes_changed(self) -> None:
        """Emit codes_changed with current codes."""
        categories = self._build_categories_dto()
        self.codes_changed.emit(categories)

    def _emit_segments_changed(self) -> None:
        """Emit segments_changed for current source."""
        if self._current_source_id is not None:
            segments = self._controller.get_segments_for_source(self._current_source_id)
            info = self._segments_to_highlight_info(segments)
            self.segments_changed.emit(info)

    @traced("build_categories_dto")
    def _build_categories_dto(self) -> list[CodeCategoryDTO]:
        """Build category DTOs from current data."""
        codes = self._controller.get_all_codes()
        categories = self._controller.get_all_categories()
        # Get all segment counts in a single query (fixes N+1 count problem)
        segment_counts = self._controller.get_segment_counts_by_code()

        # Group codes by category
        uncategorized_codes: list[Code] = []
        category_codes: dict[int, list[Code]] = {cat.id.value: [] for cat in categories}

        for code in codes:
            if code.category_id is None:
                uncategorized_codes.append(code)
            elif code.category_id.value in category_codes:
                category_codes[code.category_id.value].append(code)
            else:
                uncategorized_codes.append(code)

        # Build DTOs
        result: list[CodeCategoryDTO] = []

        # Add categorized codes
        for cat in categories:
            cat_codes = category_codes.get(cat.id.value, [])
            if cat_codes:  # Only show categories with codes
                result.append(
                    CodeCategoryDTO(
                        id=str(cat.id.value),
                        name=cat.name,
                        codes=[self._code_to_dto(c, segment_counts) for c in cat_codes],
                    )
                )

        # Add uncategorized codes
        if uncategorized_codes:
            result.append(
                CodeCategoryDTO(
                    id="uncategorized",
                    name="Uncategorized",
                    codes=[
                        self._code_to_dto(c, segment_counts)
                        for c in uncategorized_codes
                    ],
                )
            )

        return result

    def _code_to_dto(self, code: Code, segment_counts: dict[int, int]) -> CodeDTO:
        """Convert a Code entity to DTO."""
        # Use pre-fetched count (avoids N+1 query)
        count = segment_counts.get(code.id.value, 0)
        return CodeDTO(
            id=str(code.id.value),
            name=code.name,
            color=code.color.to_hex(),
            count=count,
            memo=code.memo,
        )

    @traced("segments_to_highlight_info")
    def _segments_to_highlight_info(self, segments: list[TextSegment]) -> list[dict]:
        """Convert segments to highlight information for the editor."""
        # Build code lookup map upfront (fixes N+1 query problem)
        codes = self._controller.get_all_codes()
        code_map = {code.id.value: code for code in codes}

        result = []
        for seg in segments:
            code = code_map.get(seg.code_id.value)
            result.append(
                {
                    "id": seg.id.value,
                    "start": seg.position.start,
                    "end": seg.position.end,
                    "color": code.color.to_hex() if code else "#999999",
                    "code_name": code.name if code else "Unknown",
                    "text": seg.selected_text,
                }
            )
        return result
