"""
Text Coding ViewModel

Connects the TextCodingScreen to the CodingController and CodingSignalBridge.
Handles data transformation between domain entities and UI DTOs.

Architecture:
    User Action → ViewModel → Controller → Domain → Events
                                                       ↓
    UI Update ← ViewModel ← SignalBridge ←────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from returns.result import Success

from src.application.coding import (
    CategoryPayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)
from src.application.protocols import (
    ApplyCodeCommand,
    CreateCategoryCommand,
    CreateCodeCommand,
    DeleteCodeCommand,
    MoveCodeToCategoryCommand,
    RemoveCodeCommand,
    RenameCodeCommand,
    UpdateCodeMemoCommand,
)
from src.presentation.dto import (
    CodeCategoryDTO,
    CodeDTO,
    NavigationDTO,
    SelectedCodeDTO,
    TextCodingDataDTO,
)

if TYPE_CHECKING:
    from src.application.coding import CodingControllerImpl
    from src.domain.coding.entities import Code, TextSegment


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
        controller: CodingControllerImpl,
        signal_bridge: CodingSignalBridge,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            controller: The coding controller for commands
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
        """Set the current source being viewed."""
        self._current_source_id = source_id

    # =========================================================================
    # Public API - Commands
    # =========================================================================

    def create_code(
        self, name: str, color: str, category_id: int | None = None
    ) -> bool:
        """
        Create a new code.

        Args:
            name: Code name
            color: Hex color string
            category_id: Optional category ID

        Returns:
            True if successful, False otherwise
        """
        command = CreateCodeCommand(
            name=name,
            color=color,
            category_id=category_id,
        )
        result = self._controller.create_code(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def rename_code(self, code_id: int, new_name: str) -> bool:
        """
        Rename a code.

        Args:
            code_id: ID of code to rename
            new_name: New name

        Returns:
            True if successful
        """
        command = RenameCodeCommand(code_id=code_id, new_name=new_name)
        result = self._controller.rename_code(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def delete_code(self, code_id: int, delete_segments: bool = False) -> bool:
        """
        Delete a code.

        Args:
            code_id: ID of code to delete
            delete_segments: Whether to also delete associated segments

        Returns:
            True if successful
        """
        command = DeleteCodeCommand(code_id=code_id, delete_segments=delete_segments)
        result = self._controller.delete_code(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def update_code_memo(self, code_id: int, new_memo: str | None) -> bool:
        """
        Update a code's memo.

        Args:
            code_id: ID of code to update
            new_memo: New memo content (None to clear)

        Returns:
            True if successful
        """
        command = UpdateCodeMemoCommand(code_id=code_id, new_memo=new_memo)
        result = self._controller.update_code_memo(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def move_code_to_category(self, code_id: int, category_id: int | None) -> bool:
        """
        Move a code to a different category.

        Args:
            code_id: ID of code to move
            category_id: Target category ID (None = uncategorized)

        Returns:
            True if successful
        """
        command = MoveCodeToCategoryCommand(code_id=code_id, category_id=category_id)
        result = self._controller.move_code_to_category(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def apply_code_to_selection(
        self,
        code_id: int,
        source_id: int,
        start: int,
        end: int,
        memo: str | None = None,
    ) -> bool:
        """
        Apply a code to a text selection.

        Args:
            code_id: Code to apply
            source_id: Source document ID
            start: Start position
            end: End position
            memo: Optional memo

        Returns:
            True if successful
        """
        command = ApplyCodeCommand(
            code_id=code_id,
            source_id=source_id,
            start_position=start,
            end_position=end,
            memo=memo,
        )
        result = self._controller.apply_code(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def remove_segment(self, segment_id: int) -> bool:
        """
        Remove coding from a segment.

        Args:
            segment_id: ID of segment to remove

        Returns:
            True if successful
        """
        command = RemoveCodeCommand(segment_id=segment_id)
        result = self._controller.remove_code(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

    def create_category(self, name: str, parent_id: int | None = None) -> bool:
        """
        Create a new category.

        Args:
            name: Category name
            parent_id: Optional parent category ID

        Returns:
            True if successful
        """
        command = CreateCategoryCommand(name=name, parent_id=parent_id)
        result = self._controller.create_category(command)

        if isinstance(result, Success):
            return True
        else:
            self.error_occurred.emit(str(result.failure()))
            return False

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

    def _on_code_created(self, _payload: CodePayload) -> None:
        """Handle code created event."""
        self._emit_codes_changed()

    def _on_code_renamed(self, payload: CodePayload) -> None:
        """Handle code renamed event."""
        self._emit_codes_changed()
        # Update selection if this code is selected
        if self._selected_code_id == payload.code_id:
            self.select_code(payload.code_id)

    def _on_code_color_changed(self, payload: CodePayload) -> None:
        """Handle code color changed event."""
        self._emit_codes_changed()
        if self._selected_code_id == payload.code_id:
            self.select_code(payload.code_id)

    def _on_code_deleted(self, payload: CodePayload) -> None:
        """Handle code deleted event."""
        self._emit_codes_changed()
        if self._selected_code_id == payload.code_id:
            self._selected_code_id = None
            self.code_selection_changed.emit(None)

    def _on_code_memo_updated(self, payload: CodePayload) -> None:
        """Handle code memo updated event."""
        self._emit_codes_changed()
        if self._selected_code_id == payload.code_id:
            self.select_code(payload.code_id)

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

    def _build_categories_dto(self) -> list[CodeCategoryDTO]:
        """Build category DTOs from current data."""
        codes = self._controller.get_all_codes()
        categories = self._controller.get_all_categories()

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
                        codes=[self._code_to_dto(c) for c in cat_codes],
                    )
                )

        # Add uncategorized codes
        if uncategorized_codes:
            result.append(
                CodeCategoryDTO(
                    id="uncategorized",
                    name="Uncategorized",
                    codes=[self._code_to_dto(c) for c in uncategorized_codes],
                )
            )

        return result

    def _code_to_dto(self, code: Code) -> CodeDTO:
        """Convert a Code entity to DTO."""
        # Count segments for this code
        count = len(self._controller.get_segments_for_code(code.id.value))
        return CodeDTO(
            id=str(code.id.value),
            name=code.name,
            color=code.color.to_hex(),
            count=count,
            memo=code.memo,
        )

    def _segments_to_highlight_info(self, segments: list[TextSegment]) -> list[dict]:
        """Convert segments to highlight information for the editor."""
        result = []
        for seg in segments:
            code = self._controller.get_code(seg.code_id.value)
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
