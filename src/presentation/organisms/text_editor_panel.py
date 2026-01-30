"""
Text Editor Panel Organism

A panel for displaying and interacting with text documents for coding.
Shows the document content with header, stats, and selection capabilities.

Implements QC-007.01 Text Highlighting System:
- AC #1: highlight_range(start, end, color) applies background color
- AC #2: clear_highlights() removes all highlights
- AC #3: Overlapping highlights with transparency/blending
- AC #4: Bold formatting for text segments with memos
- AC #5: Underline formatting for overlapping code regions
- AC #6: Line numbers displayed in left margin
- AC #7: Dynamic text color based on background highlight

Implements QC-007.09 Search in Text:
- AC #1: search_text() returns list of match positions
- AC #2: Highlights are applied to matches
- AC #3: Navigate to next match
- AC #4: Navigate to previous match
- AC #5: Case sensitive search option
- AC #6: Regex search support
- AC #7: Clear search removes highlights
- AC #8: Match counter shows current/total
"""

import re
from dataclasses import dataclass, field

from PySide6.QtCore import Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    SelectionPopup,
    TextColor,
    get_colors,
)

# Import molecules
from src.presentation.molecules.editor import LineNumberGutter
from src.presentation.molecules.highlighting import OverlapDetector
from src.presentation.molecules.search import SearchBar
from src.presentation.molecules.selection import SelectionPopupController

# Backward compatibility aliases
LineNumberWidget = LineNumberGutter
SearchWidget = SearchBar


@dataclass
class HighlightRange:
    """Represents a highlighted text range."""

    start: int
    end: int
    color: str
    memo: str = ""
    metadata: dict = field(default_factory=dict)


class TextEditorPanel(QFrame):
    """
    Panel for displaying and coding text content.

    Features:
    - Text highlighting with background colors
    - Overlapping highlight detection and underline indicator
    - Bold formatting for segments with memos
    - Dynamic text color based on background
    - Optional line numbers in left margin
    - Selection popup for quick actions

    Signals:
        text_selected(str, int, int): Emitted when text is selected (text, start, end)
        text_deselected(): Emitted when text selection is cleared (AC #3)
        code_applied(str, int, int): Emitted when a code is applied to selection
        highlight_applied(int, int, str): Emitted when highlight is applied (start, end, color)
        highlights_cleared(): Emitted when all highlights are cleared
    """

    text_selected = Signal(str, int, int)  # text, start, end
    text_deselected = Signal()  # AC #3: Emitted when selection cleared
    code_applied = Signal(str, int, int)  # code_id, start, end
    highlight_applied = Signal(int, int, str)  # start, end, color
    highlights_cleared = Signal()

    # Popup action signals (QC-007.04)
    popup_code_clicked = Signal()  # Quick code action
    popup_in_vivo_clicked = Signal()  # In-vivo action
    popup_memo_clicked = Signal()  # Memo action
    popup_annotate_clicked = Signal()  # Annotate action

    # Search signals (QC-007.09)
    search_results_changed = Signal(int, int)  # match_count, current_index

    def __init__(
        self,
        show_line_numbers: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the text editor panel.

        Args:
            show_line_numbers: Whether to show line numbers in left margin
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._show_line_numbers = show_line_numbers
        self._highlights: list[HighlightRange] = []
        self._text = ""

        # Search state (QC-007.09)
        self._search_matches: list[tuple[int, int]] = []
        self._search_current_index: int = -1
        self._search_highlight_color = "#FFEB3B"  # Yellow for search highlights

        self._setup_ui()

    def _setup_ui(self):
        """Build the UI components."""
        self.setStyleSheet(f"""
            TextEditorPanel {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._setup_header(main_layout)

        # Content area (line numbers + text editor)
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
                margin: {SPACING.lg}px;
            }}
        """)
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Line numbers (optional)
        self._line_numbers = LineNumberWidget(colors=self._colors)
        self._line_numbers.setVisible(self._show_line_numbers)
        content_layout.addWidget(self._line_numbers)

        # Text editor - using QTextEdit for rich text support
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.xl}px {SPACING.xxl}px;
                font-family: {TYPOGRAPHY.font_family};
                font-size: {TYPOGRAPHY.text_lg}px;
                selection-background-color: {self._colors.primary}40;
            }}
        """)

        # Connect signals
        self._text_edit.selectionChanged.connect(self._on_selection_changed)
        self._text_edit.textChanged.connect(self._on_text_changed)

        content_layout.addWidget(self._text_edit, 1)
        main_layout.addWidget(content_frame, 1)

        # Selection popup with coding-specific actions (QC-007.04)
        coding_actions = [
            ("mdi6.tag-plus", "Quick Code (Q)", "code", True),
            ("mdi6.creation", "In-vivo (V)", "in_vivo", False),
            ("mdi6.note-plus", "Memo (M)", "memo", False),
            ("mdi6.comment-plus", "Annotate (A)", "annotate", False),
        ]
        self._selection_popup = SelectionPopup(
            actions=coding_actions, colors=self._colors
        )
        self._selection_popup.action_clicked.connect(self._on_popup_action)
        self._selection_popup.hide()

        # Use SelectionPopupController for timer-based popup management
        self._popup_controller = SelectionPopupController(
            popup=self._selection_popup,
            delay_ms=400,
            parent=self,
        )

        # Overlap detector for highlight overlap detection
        self._overlap_detector = OverlapDetector()

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the header with title and stats."""
        from design_system import Icon

        self._header = QFrame()
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        header_layout.setSpacing(SPACING.sm)

        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(SPACING.sm)

        self._title_icon = Icon(
            "mdi6.file-document-edit",
            size=16,
            color=self._colors.primary,
            colors=self._colors,
        )
        title_layout.addWidget(self._title_icon)

        self._title_label = QLabel("")
        self._title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        title_layout.addWidget(self._title_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Stats container
        self._stats_layout = QHBoxLayout()
        self._stats_layout.setSpacing(SPACING.md)
        header_layout.addLayout(self._stats_layout)

        layout.addWidget(self._header)

    # =========================================================================
    # Public API - Document Management
    # =========================================================================

    def set_document(self, title: str, badge: str = None, text: str = ""):  # noqa: ARG002
        """
        Set the document to display.

        Args:
            title: Document title to show in header
            badge: Optional badge text (e.g., case ID) - reserved for future use
            text: Document text content
        """
        self._title_label.setText(title)
        self._text = text
        self._text_edit.setPlainText(text)
        self._highlights.clear()
        self._update_line_numbers()

    def get_text(self) -> str:
        """Get the current text content."""
        return self._text_edit.toPlainText()

    def set_stats(self, stats: list[tuple[str, str]]):
        """
        Update the stats display in the header.

        Args:
            stats: List of (icon_name, text) tuples
        """
        from design_system import Icon

        # Clear existing stats
        while self._stats_layout.count():
            item = self._stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for icon_name, text in stats:
            stat_widget = QFrame()
            stat_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface_light};
                    border-radius: {RADIUS.md}px;
                    padding: 2px 8px;
                }}
            """)
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(
                SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs
            )
            stat_layout.setSpacing(SPACING.xs)

            icon = Icon(
                icon_name,
                size=14,
                color=self._colors.text_secondary,
                colors=self._colors,
            )
            stat_layout.addWidget(icon)

            label = QLabel(text)
            label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            stat_layout.addWidget(label)

            self._stats_layout.addWidget(stat_widget)

    # =========================================================================
    # Public API - Highlighting (AC #1, #2)
    # =========================================================================

    def highlight_range(
        self,
        start: int,
        end: int,
        color: str,
        memo: str = "",
    ):
        """
        Highlight a range of text with a color.

        Implements AC #1: highlight_range(start, end, color) applies background color.
        Also implements AC #4 (bold for memos) and AC #7 (dynamic text color).

        Args:
            start: Start position
            end: End position
            color: Highlight color (hex string like "#FFC107")
            memo: Optional memo text - if provided, text will be bold (AC #4)
        """
        if start >= end or start < 0:
            return

        text_len = len(self._text_edit.toPlainText())
        if end > text_len:
            end = text_len
        if start >= text_len:
            return

        # Store the highlight
        highlight = HighlightRange(start=start, end=end, color=color, memo=memo)
        self._highlights.append(highlight)

        # Apply the highlight formatting
        self._apply_highlight(highlight)

        # Check and apply overlap underlines (AC #5)
        self._apply_overlap_underlines()

        # Emit signal
        self.highlight_applied.emit(start, end, color)

    def _apply_highlight(self, highlight: HighlightRange):
        """Apply formatting for a single highlight."""
        fmt = QTextCharFormat()

        # Background color
        bg_color = QColor(highlight.color)
        if not bg_color.isValid():
            bg_color = QColor(self._colors.fallback_code_color)
        fmt.setBackground(QBrush(bg_color))

        # Dynamic text color based on background (AC #7)
        text_color = TextColor(highlight.color).recommendation
        fmt.setForeground(QBrush(QColor(text_color)))

        # Bold if has memo (AC #4)
        if highlight.memo:
            fmt.setFontWeight(QFont.Weight.Bold)

        # Apply to text range
        cursor = self._text_edit.textCursor()
        cursor.setPosition(highlight.start, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(highlight.end, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(fmt)

    def clear_highlights(self):
        """
        Clear all text highlights.

        Implements AC #2: clear_highlights() removes all highlights.
        """
        if not self._highlights:
            return

        self._highlights.clear()

        # Remove all formatting
        text = self._text_edit.toPlainText()
        if text:
            cursor = self._text_edit.textCursor()
            cursor.setPosition(0, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(len(text), QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(QTextCharFormat())
            self._text_edit.setTextCursor(cursor)

        self.highlights_cleared.emit()

    def get_highlight_count(self) -> int:
        """Get the number of highlights applied."""
        return len(self._highlights)

    # =========================================================================
    # Public API - Overlap Detection (AC #3, #5)
    # =========================================================================

    def get_overlap_regions(self) -> list[tuple[int, int]]:
        """
        Detect and return overlapping highlight regions.

        Implements AC #3: Overlapping highlights detection.

        Returns:
            List of (start, end) tuples for overlapping regions
        """
        overlaps = self._overlap_detector.find_overlaps(self._highlights)
        return [(r.start, r.end) for r in overlaps]

    def _apply_overlap_underlines(self):
        """
        Apply underline to overlapping regions.

        Implements AC #5: Underline formatting for overlapping code regions.
        """
        overlaps = self.get_overlap_regions()

        for start, end in overlaps:
            cursor = self._text_edit.textCursor()
            cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            fmt = QTextCharFormat()
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
            fmt.setUnderlineColor(QColor(self._colors.text_on_dark))
            cursor.mergeCharFormat(fmt)  # Merge to preserve background

    # =========================================================================
    # Public API - Line Numbers (AC #6)
    # =========================================================================

    def has_line_numbers(self) -> bool:
        """Check if line numbers are enabled."""
        return self._show_line_numbers

    def set_line_numbers_visible(self, visible: bool):
        """
        Toggle line numbers visibility.

        Implements AC #6: Line numbers displayed in left margin.

        Args:
            visible: Whether to show line numbers
        """
        self._show_line_numbers = visible
        self._line_numbers.setVisible(visible)
        if visible:
            self._update_line_numbers()

    def get_line_count(self) -> int:
        """Get the number of lines in the document."""
        return self._line_numbers.get_line_count()

    def _update_line_numbers(self):
        """Update line numbers based on text content."""
        text = self._text_edit.toPlainText()
        line_count = text.count("\n") + 1 if text else 1
        self._line_numbers.set_line_count(line_count)

    def _on_text_changed(self):
        """Handle text content changes."""
        self._update_line_numbers()

    # =========================================================================
    # Public API - Selection & Navigation
    # =========================================================================

    def get_selection(self) -> tuple[int, int] | None:
        """
        Get the current text selection.

        Returns:
            Tuple of (start, end) positions or None if no selection
        """
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            return (cursor.selectionStart(), cursor.selectionEnd())
        return None

    def get_selected_text(self) -> str:
        """
        Get the currently selected text.

        Returns:
            Selected text string or empty string if no selection
        """
        cursor = self._text_edit.textCursor()
        return cursor.selectedText() if cursor.hasSelection() else ""

    def select_range(self, start: int, end: int):
        """
        Select a range of text.

        Args:
            start: Start position
            end: End position
        """
        cursor = self._text_edit.textCursor()
        cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self._text_edit.setTextCursor(cursor)

    def scroll_to_position(self, position: int):
        """
        Scroll to a specific position in the text.

        Args:
            position: Character position to scroll to
        """
        cursor = self._text_edit.textCursor()
        cursor.setPosition(position)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    # =========================================================================
    # Public API - Format Inspection (for testing)
    # =========================================================================

    def get_char_format_at(self, position: int) -> QTextCharFormat | None:
        """
        Get the character format at a specific position.

        Useful for testing that highlights were applied correctly.

        Args:
            position: Character position

        Returns:
            QTextCharFormat at the position or None if invalid
        """
        text = self._text_edit.toPlainText()
        if position < 0 or position >= len(text):
            return None

        cursor = self._text_edit.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            1,
        )
        return cursor.charFormat()

    # =========================================================================
    # Public API - Selection Management
    # =========================================================================

    def clear_selection(self):
        """
        Clear the current text selection.

        Implements AC #3: Clears selection and emits text_deselected.
        """
        cursor = self._text_edit.textCursor()
        cursor.clearSelection()
        self._text_edit.setTextCursor(cursor)
        self.text_deselected.emit()

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_selection_changed(self):
        """Handle text selection changes."""
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            self.text_selected.emit(text, start, end)

            # Use popup controller for delayed popup display
            self._popup_controller.on_selection_changed(
                has_selection=True,
                selection_text=text,
                get_position=self._get_popup_position,
            )
        else:
            # Selection was cleared
            self._popup_controller.on_selection_changed(has_selection=False)
            self.text_deselected.emit()

    def _get_popup_position(self):
        """Get the position for the selection popup."""
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            cursor_rect = self._text_edit.cursorRect(cursor)
            return self._text_edit.mapToGlobal(cursor_rect.topRight())
        return None

    def set_selection_popup_enabled(self, enabled: bool):
        """Enable or disable the selection popup."""
        self._popup_controller.set_enabled(enabled)

    def is_selection_popup_visible(self) -> bool:
        """Check if selection popup is currently visible."""
        return self._popup_controller.is_visible()

    def _on_popup_action(self, action_id: str):
        """Handle selection popup action."""
        selection = self.get_selection()
        if not selection:
            return

        # Hide popup after action
        self._selection_popup.hide()

        # Emit appropriate signal based on action
        if action_id == "code":
            self.popup_code_clicked.emit()
        elif action_id == "in_vivo":
            self.popup_in_vivo_clicked.emit()
        elif action_id == "memo":
            self.popup_memo_clicked.emit()
        elif action_id == "annotate":
            self.popup_annotate_clicked.emit()

    # =========================================================================
    # Public API - Search in Text (QC-007.09)
    # =========================================================================

    def search_text(
        self,
        query: str,
        case_sensitive: bool = False,
        use_regex: bool = False,
    ) -> list[tuple[int, int]]:
        """
        Search for text and highlight matches.

        Implements AC #1: search_text() returns list of match positions.
        Implements AC #2: Highlights are applied to matches.
        Implements AC #5: Case sensitive search option.
        Implements AC #6: Regex search support.

        Args:
            query: Search query string
            case_sensitive: If True, match case exactly
            use_regex: If True, interpret query as regex pattern

        Returns:
            List of (start, end) tuples for each match
        """
        # Clear previous search
        self._clear_search_highlights()
        self._search_matches.clear()
        self._search_current_index = -1

        if not query:
            self.search_results_changed.emit(0, -1)
            return []

        text = self._text_edit.toPlainText()
        if not text:
            self.search_results_changed.emit(0, -1)
            return []

        # Find all matches
        try:
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
                for match in pattern.finditer(text):
                    self._search_matches.append((match.start(), match.end()))
            else:
                search_text = text if case_sensitive else text.lower()
                search_query = query if case_sensitive else query.lower()
                start = 0
                while True:
                    pos = search_text.find(search_query, start)
                    if pos == -1:
                        break
                    self._search_matches.append((pos, pos + len(query)))
                    start = pos + 1
        except re.error:
            # Invalid regex pattern
            self._search_matches.clear()
            self.search_results_changed.emit(0, -1)
            return []

        # Apply highlights to matches
        self._apply_search_highlights()

        # Select first match if any
        if self._search_matches:
            self._search_current_index = 0
            self._select_current_match()
            self.search_results_changed.emit(len(self._search_matches), 0)
        else:
            self.search_results_changed.emit(0, -1)

        return self._search_matches.copy()

    def search_next(self):
        """
        Navigate to the next search match.

        Implements AC #3: search_next() moves cursor to next match.
        """
        self._navigate_to_match(1)

    def search_prev(self):
        """
        Navigate to the previous search match.

        Implements AC #4: search_prev() moves cursor to previous match.
        """
        self._navigate_to_match(-1)

    def _navigate_to_match(self, direction: int):
        """Navigate to the next or previous match based on direction (+1 or -1)."""
        if not self._search_matches:
            return

        self._search_current_index = (self._search_current_index + direction) % len(
            self._search_matches
        )
        self._select_current_match()
        self.search_results_changed.emit(
            len(self._search_matches), self._search_current_index
        )

    def clear_search(self):
        """
        Clear search highlights and reset search state.

        Implements AC #7: clear_search() removes all search highlights.
        """
        self._clear_search_highlights()
        self._search_matches.clear()
        self._search_current_index = -1
        self.search_results_changed.emit(0, -1)

    def get_search_highlight_count(self) -> int:
        """Get the number of search matches highlighted."""
        return len(self._search_matches)

    def get_current_match_index(self) -> int:
        """Get the current match index (0-indexed, -1 if no matches)."""
        return self._search_current_index

    def get_search_status(self) -> tuple[int, int]:
        """
        Get the current search status.

        Implements AC #8: Match counter shows current/total.

        Returns:
            Tuple of (current, total) where current is 1-indexed for display
        """
        if not self._search_matches:
            return (0, 0)
        return (self._search_current_index + 1, len(self._search_matches))

    def _apply_search_highlights(self):
        """Apply highlight formatting to all search matches."""
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor(self._search_highlight_color)))
        fmt.setForeground(QBrush(QColor("#000000")))  # Black text on yellow

        for start, end in self._search_matches:
            cursor = self._text_edit.textCursor()
            cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(fmt)

    def _clear_search_highlights(self):
        """Remove search highlight formatting."""
        if not self._search_matches:
            return

        # Re-apply original formatting by clearing and re-applying code highlights
        text = self._text_edit.toPlainText()
        if text:
            # Clear all formatting first
            cursor = self._text_edit.textCursor()
            cursor.setPosition(0, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(len(text), QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(QTextCharFormat())

            # Re-apply code highlights
            for highlight in self._highlights:
                self._apply_highlight(highlight)

            # Re-apply overlap underlines
            self._apply_overlap_underlines()

    def _select_current_match(self):
        """Select and scroll to the current search match."""
        if self._search_current_index < 0 or not self._search_matches:
            return

        start, end = self._search_matches[self._search_current_index]
        self.select_range(start, end)
        self._text_edit.ensureCursorVisible()
