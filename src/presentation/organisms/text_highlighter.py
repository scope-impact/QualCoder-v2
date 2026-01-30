"""
Text Highlighter - QualCoder-specific text highlighting components.

These components implement qualitative coding-specific functionality:
- Code segments with highlighting
- Overlapping code detection
- Annotation markers
- Coded text display

For generic text display, use design_system.TextPanel instead.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from design_system.qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, Qt, Signal,
    QTextCursor, QTextCharFormat, QColor, QFont, QBrush,
)

from design_system import (
    ColorPalette, get_theme,
    SPACING, RADIUS, TYPOGRAPHY,
    SelectionPopup, TextColor,
)


# =============================================================================
# Domain Data Classes
# =============================================================================

@dataclass
class CodeSegment:
    """
    Represents a coded text segment in qualitative analysis.

    Attributes:
        segment_id: Unique identifier for this segment
        code_id: ID of the code applied
        code_name: Display name of the code
        code_color: Hex color of the code (e.g., "#FFC107")
        pos0: Start position in text
        pos1: End position in text
        text: The selected text content
        memo: Optional memo/note attached to this coding
        important: Whether this coding is marked as important
        owner: Who created this coding
        date: When this coding was created
    """
    segment_id: str = ""
    code_id: int = 0
    code_name: str = ""
    code_color: str = "#777777"
    pos0: int = 0
    pos1: int = 0
    text: str = ""
    memo: str = ""
    important: bool = False
    owner: str = ""
    date: str = ""

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Annotation:
    """
    Represents a text annotation (note/comment without a code).

    Attributes:
        annotation_id: Unique identifier
        pos0: Start position
        pos1: End position
        text: Annotation content
        owner: Who created it
        date: When created
    """
    annotation_id: str = ""
    pos0: int = 0
    pos1: int = 0
    text: str = ""
    owner: str = ""
    date: str = ""


# =============================================================================
# Text Highlighter Component
# =============================================================================

class TextHighlighter(QFrame):
    """
    Rich text panel with qualitative code highlighting support.

    Based on QualCoder's battle-tested approach using QTextEdit with
    QTextCharFormat for inline highlighting. Supports:

    - Multiple code highlights with distinct colors
    - Overlapping codes indicated by underline
    - Memos shown as italic text
    - Important codes shown as bold
    - Annotations shown as bold
    - Integrated selection popup for coding actions

    Usage:
        # Basic usage
        highlighter = TextHighlighter()
        highlighter.set_text("Interview transcript content...")

        # Add coded segments
        highlighter.add_segment(CodeSegment(
            segment_id="1",
            code_id=101,
            code_name="Learning",
            code_color="#FFC107",
            pos0=10,
            pos1=25,
            text="important passage"
        ))

        # Apply highlighting
        highlighter.highlight()

        # Listen for selection
        highlighter.text_selected.connect(self.on_selection)
        highlighter.segment_clicked.connect(self.on_segment_click)

    Signals:
        text_selected(str, int, int): Emitted when text is selected (text, start, end)
        segment_clicked(str): Emitted when a coded segment is clicked (segment_id)
        selection_action(str, int, int): Emitted when popup action is triggered
    """

    # Signals
    text_selected = Signal(str, int, int)  # text, start, end
    segment_clicked = Signal(str)  # segment_id
    selection_action = Signal(str, int, int)  # action_id, start, end

    def __init__(
        self,
        title: str = "",
        show_header: bool = False,
        editable: bool = False,
        show_selection_popup: bool = True,
        dark_mode: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        """
        Initialize the TextHighlighter.

        Args:
            title: Optional title for header
            show_header: Show header with title and stats
            editable: Allow text editing
            show_selection_popup: Show popup on text selection
            dark_mode: Use dark theme (affects overlap underline color)
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._dark_mode = dark_mode
        self._editable = editable
        self._show_selection_popup = show_selection_popup
        self._title = title

        # Data storage
        self._text = ""
        self._segments: List[CodeSegment] = []
        self._annotations: List[Annotation] = []
        self._codes: Dict[int, Dict] = {}  # code_id -> {name, color, ...}

        # File offset (for partial file loading like QualCoder)
        self._file_start = 0

        # Selection popup
        self._popup = None

        self._setup_ui(show_header, title)

    def _setup_ui(self, show_header: bool, title: str):
        """Build the UI."""
        self.setStyleSheet(f"""
            TextHighlighter {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (optional)
        if show_header:
            self._setup_header(main_layout, title)

        # Text area - using QTextEdit for rich text support
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(not self._editable)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: none;
                border-radius: {RADIUS.lg}px;
                padding: {SPACING.xl}px {SPACING.xxl}px;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                font-size: 15px;
                selection-background-color: {self._colors.primary}40;
            }}
        """)

        # Connect signals
        self._text_edit.selectionChanged.connect(self._on_selection_changed)
        self._text_edit.cursorPositionChanged.connect(self._on_cursor_changed)

        main_layout.addWidget(self._text_edit, 1)

        # Create selection popup
        if self._show_selection_popup:
            self._popup = SelectionPopup(colors=self._colors, parent=self)
            self._popup.action_clicked.connect(self._on_popup_action)
            self._popup.hide()

    def _setup_header(self, layout: QVBoxLayout, title: str):
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
            colors=self._colors
        )
        title_layout.addWidget(self._title_icon)

        self._title_label = QLabel(title)
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
    # Public API - Text Management
    # =========================================================================

    def set_text(self, text: str, file_start: int = 0):
        """
        Set the text content.

        Args:
            text: The text to display
            file_start: Offset for partial file (positions adjusted by this)
        """
        self._text = text
        self._file_start = file_start
        self._text_edit.setPlainText(text)

    def get_text(self) -> str:
        """Get the current text content."""
        return self._text_edit.toPlainText()

    def set_title(self, title: str):
        """Update the header title."""
        self._title = title
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)

    def set_stats(self, stats: List[Tuple[str, str]]):
        """
        Set stats in header.

        Args:
            stats: List of (icon_name, text) tuples
        """
        if not hasattr(self, '_stats_layout'):
            return

        # Clear existing
        while self._stats_layout.count():
            item = self._stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        from design_system import Icon
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
            stat_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
            stat_layout.setSpacing(SPACING.xs)

            icon = Icon(icon_name, size=14, color=self._colors.text_secondary, colors=self._colors)
            stat_layout.addWidget(icon)

            label = QLabel(text)
            label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            stat_layout.addWidget(label)

            self._stats_layout.addWidget(stat_widget)

    # =========================================================================
    # Public API - Code Segments
    # =========================================================================

    def add_segment(self, segment: CodeSegment):
        """Add a coded segment."""
        self._segments.append(segment)

    def add_segments(self, segments: List[CodeSegment]):
        """Add multiple coded segments."""
        self._segments.extend(segments)

    def clear_segments(self):
        """Remove all coded segments."""
        self._segments.clear()

    def set_segments(self, segments: List[CodeSegment]):
        """Replace all segments."""
        self._segments = list(segments)

    def get_segments(self) -> List[CodeSegment]:
        """Get all coded segments."""
        return list(self._segments)

    def remove_segment(self, segment_id: str):
        """Remove a segment by ID."""
        self._segments = [s for s in self._segments if s.segment_id != segment_id]

    # =========================================================================
    # Public API - Annotations
    # =========================================================================

    def add_annotation(self, annotation: Annotation):
        """Add an annotation."""
        self._annotations.append(annotation)

    def clear_annotations(self):
        """Remove all annotations."""
        self._annotations.clear()

    def set_annotations(self, annotations: List[Annotation]):
        """Replace all annotations."""
        self._annotations = list(annotations)

    # =========================================================================
    # Public API - Highlighting
    # =========================================================================

    def highlight(self, show_important_only: bool = False):
        """
        Apply highlighting to all coded segments and annotations.

        This clears existing formatting and reapplies based on current
        segments and annotations.

        Args:
            show_important_only: Only highlight segments marked as important
        """
        if not self._text:
            return

        # Remove existing highlighting
        self.unlight()

        # Apply code highlights
        for segment in self._segments:
            if show_important_only and not segment.important:
                continue
            self._apply_segment_highlight(segment)

        # Apply annotation highlights (bold)
        for annotation in self._annotations:
            self._apply_annotation_highlight(annotation)

        # Apply underline to overlapping regions
        if not show_important_only:
            self._apply_overlap_underlines()

    def unlight(self):
        """Remove all highlighting from the text."""
        if not self._text:
            return

        cursor = self._text_edit.textCursor()
        cursor.setPosition(0, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(len(self._text), QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())
        self._text_edit.setTextCursor(cursor)

    def _apply_segment_highlight(self, segment: CodeSegment):
        """Apply highlighting for a single segment."""
        fmt = QTextCharFormat()

        # Background color
        color = QColor(segment.code_color)
        fmt.setBackground(QBrush(color))

        # Contrasting text color
        text_color = TextColor(segment.code_color).recommendation
        fmt.setForeground(QBrush(QColor(text_color)))

        # Memo indicator: italic
        if segment.memo:
            fmt.setFontItalic(True)

        # Important indicator: bold
        if segment.important:
            fmt.setFontWeight(QFont.Weight.Bold)

        # Apply to text range (adjusted for file offset)
        pos0 = segment.pos0 - self._file_start
        pos1 = segment.pos1 - self._file_start

        if 0 <= pos0 < pos1 <= len(self._text):
            cursor = self._text_edit.textCursor()
            cursor.setPosition(pos0, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos1, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(fmt)

    def _apply_annotation_highlight(self, annotation: Annotation):
        """Apply bold formatting for annotations."""
        pos0 = annotation.pos0 - self._file_start
        pos1 = annotation.pos1 - self._file_start

        if 0 <= pos0 < pos1 <= len(self._text):
            cursor = self._text_edit.textCursor()
            cursor.setPosition(pos0, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(pos1, QTextCursor.MoveMode.KeepAnchor)

            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Weight.Bold)
            cursor.mergeCharFormat(fmt)  # Merge to preserve background

    def _apply_overlap_underlines(self):
        """Apply underline to overlapping coded regions."""
        overlaps = self._detect_overlaps()

        # Underline color: white on dark, black on light
        underline_color = QColor("#FFFFFF") if self._dark_mode else QColor("#000000")

        for start, end in overlaps:
            pos0 = start - self._file_start
            pos1 = end - self._file_start

            if 0 <= pos0 < pos1 <= len(self._text):
                cursor = self._text_edit.textCursor()
                cursor.setPosition(pos0, QTextCursor.MoveMode.MoveAnchor)
                cursor.setPosition(pos1, QTextCursor.MoveMode.KeepAnchor)

                fmt = QTextCharFormat()
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                fmt.setUnderlineColor(underline_color)
                cursor.mergeCharFormat(fmt)  # Merge to preserve background

    def _detect_overlaps(self) -> List[Tuple[int, int]]:
        """
        Detect overlapping coded regions.

        Returns list of (start, end) tuples for overlapping ranges.
        Based on QualCoder's apply_underline_to_overlaps() logic.
        """
        overlaps = []
        segments = self._segments

        for i, seg_i in enumerate(segments):
            for j, seg_j in enumerate(segments):
                if i >= j:
                    continue  # Avoid duplicate comparisons

                # Check for overlap
                if seg_j.pos0 <= seg_i.pos0 < seg_j.pos1 or seg_i.pos0 <= seg_j.pos0 < seg_i.pos1:
                    # Calculate overlap region
                    overlap_start = max(seg_i.pos0, seg_j.pos0)
                    overlap_end = min(seg_i.pos1, seg_j.pos1)

                    if overlap_start < overlap_end:
                        overlaps.append((overlap_start, overlap_end))

        # Remove duplicates and merge adjacent
        return self._merge_overlaps(overlaps)

    def _merge_overlaps(self, overlaps: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Merge adjacent/overlapping ranges."""
        if not overlaps:
            return []

        # Sort by start position
        sorted_overlaps = sorted(set(overlaps), key=lambda x: x[0])
        merged = [sorted_overlaps[0]]

        for start, end in sorted_overlaps[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                # Merge with previous
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    # =========================================================================
    # Public API - Selection & Navigation
    # =========================================================================

    def get_selection(self) -> Optional[Tuple[int, int]]:
        """Get current selection range (start, end) or None."""
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            return (cursor.selectionStart(), cursor.selectionEnd())
        return None

    def get_selected_text(self) -> str:
        """Get currently selected text."""
        cursor = self._text_edit.textCursor()
        return cursor.selectedText() if cursor.hasSelection() else ""

    def scroll_to_position(self, pos: int):
        """Scroll to a specific text position."""
        cursor = self._text_edit.textCursor()
        cursor.setPosition(pos - self._file_start)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    def select_range(self, start: int, end: int):
        """Select a range of text."""
        cursor = self._text_edit.textCursor()
        cursor.setPosition(start - self._file_start, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(end - self._file_start, QTextCursor.MoveMode.KeepAnchor)
        self._text_edit.setTextCursor(cursor)

    # =========================================================================
    # Public API - Statistics
    # =========================================================================

    def get_overlap_count(self) -> int:
        """Get number of overlapping regions."""
        return len(self._detect_overlaps())

    def get_segment_count(self) -> int:
        """Get total number of coded segments."""
        return len(self._segments)

    def get_codes_at_position(self, pos: int) -> List[CodeSegment]:
        """Get all code segments that include the given position."""
        pos_adjusted = pos + self._file_start
        return [s for s in self._segments if s.pos0 <= pos_adjusted < s.pos1]

    def update_stats_display(self):
        """Update the header stats based on current data."""
        if hasattr(self, '_stats_layout'):
            overlap_count = self.get_overlap_count()
            segment_count = self.get_segment_count()

            stats = []
            if overlap_count > 0:
                stats.append(("mdi6.layers", f"{overlap_count} overlapping"))
            stats.append(("mdi6.label", f"{segment_count} codes applied"))

            self.set_stats(stats)

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_selection_changed(self):
        """Handle text selection changes."""
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            start = cursor.selectionStart() + self._file_start
            end = cursor.selectionEnd() + self._file_start
            self.text_selected.emit(text, start, end)

            # Show popup near selection
            if self._popup and self._show_selection_popup:
                # Get cursor rectangle for positioning
                cursor_rect = self._text_edit.cursorRect()
                global_pos = self._text_edit.mapToGlobal(cursor_rect.topLeft())
                self._popup.show_near_selection(global_pos)
        else:
            # Hide popup when selection cleared
            if self._popup:
                self._popup.hide()

    def _on_cursor_changed(self):
        """Handle cursor position changes (for detecting segment clicks)."""
        cursor = self._text_edit.textCursor()
        if not cursor.hasSelection():
            pos = cursor.position()
            segments = self.get_codes_at_position(pos)
            if segments:
                # Emit click for first segment at position
                self.segment_clicked.emit(segments[0].segment_id)

    def _on_popup_action(self, action_id: str):
        """Handle selection popup actions."""
        selection = self.get_selection()
        if selection:
            start, end = selection
            self.selection_action.emit(action_id, start, end)

    # =========================================================================
    # Popup Configuration
    # =========================================================================

    def set_popup_actions(self, actions: List[Tuple[str, str, str, bool]]):
        """
        Configure custom actions for the selection popup.

        Args:
            actions: List of (icon, tooltip, action_id, is_primary) tuples
        """
        if self._popup:
            self._popup.deleteLater()

        self._popup = SelectionPopup(actions=actions, colors=self._colors, parent=self)
        self._popup.action_clicked.connect(self._on_popup_action)
        self._popup.hide()

    def show_popup(self):
        """Manually show the selection popup."""
        if self._popup:
            cursor_rect = self._text_edit.cursorRect()
            global_pos = self._text_edit.mapToGlobal(cursor_rect.topLeft())
            self._popup.show_near_selection(global_pos)

    def hide_popup(self):
        """Manually hide the selection popup."""
        if self._popup:
            self._popup.hide()


# =============================================================================
# Coded Text Highlight Component
# =============================================================================

class CodedTextHighlight(QFrame):
    """
    Highlighted text segment with code indicator.

    Supports single codes, overlapping codes, and inline display.

    Usage:
        # Simple highlight
        highlight = CodedTextHighlight(
            text="important passage",
            code_name="Learning",
            code_color="#FFC107"
        )

        # With overlap indicator
        highlight = CodedTextHighlight(
            text="overlapping passage",
            code_name="Learning",
            code_color="#FFC107",
            overlap_count=2
        )

        # Inline mode (for use in rich text)
        highlight = CodedTextHighlight(
            text="inline text",
            code_color="#FFC107",
            inline=True
        )
    """

    clicked = Signal(str)  # segment_id

    def __init__(
        self,
        text: str,
        code_name: str = "",
        code_color: str = "#009688",
        segment_id: str = "",
        overlap_count: int = 0,
        inline: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._segment_id = segment_id
        self._code_color = code_color
        self._overlap_count = overlap_count

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if inline:
            # Inline mode - like HTML span with highlight
            self._setup_inline(text, code_color, overlap_count)
        else:
            # Block mode - card-like display
            self._setup_block(text, code_name, code_color, overlap_count)

    def _setup_inline(self, text: str, color: str, overlap_count: int):
        """Setup inline highlight (for use in text flow)"""
        self.setStyleSheet(f"""
            CodedTextHighlight {{
                background-color: {color}4D;
                border-bottom: 2px solid {color};
                border-radius: 2px;
                padding: 2px 0;
            }}
            CodedTextHighlight:hover {{
                filter: brightness(1.2);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
        """)
        layout.addWidget(text_label)

        # Overlap badge
        if overlap_count > 1:
            badge = OverlapIndicator(count=overlap_count, colors=self._colors)
            layout.addWidget(badge)

    def _setup_block(self, text: str, code_name: str, color: str, overlap_count: int):
        """Setup block highlight (card-like display)"""
        self.setStyleSheet(f"""
            CodedTextHighlight {{
                background-color: {color}26;
                border-left: 3px solid {color};
                border-radius: 0 {RADIUS.sm}px {RADIUS.sm}px 0;
            }}
            CodedTextHighlight:hover {{
                background-color: {color}40;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Header with code badge and optional overlap indicator
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        if code_name:
            badge = QLabel(code_name)
            badge.setStyleSheet(f"""
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: bold;
            """)
            header.addWidget(badge)

        header.addStretch()

        if overlap_count > 1:
            overlap_badge = OverlapIndicator(count=overlap_count, colors=self._colors)
            header.addWidget(overlap_badge)

        layout.addLayout(header)

        # Text content
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            line-height: 1.4;
        """)
        layout.addWidget(text_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._segment_id)


# =============================================================================
# Indicator Components
# =============================================================================

class OverlapIndicator(QFrame):
    """
    Badge showing number of overlapping codes on a text segment.

    Usage:
        indicator = OverlapIndicator(count=3)
    """

    def __init__(
        self,
        count: int = 2,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._count = count

        self.setFixedSize(18, 18)
        self.setStyleSheet(f"""
            OverlapIndicator {{
                background-color: {self._colors.primary};
                border-radius: 9px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(str(count))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            color: white;
            font-size: 9px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(label)


class AnnotationIndicator(QFrame):
    """
    Inline annotation marker.

    Usage:
        indicator = AnnotationIndicator(
            annotation_type="memo",
            count=3
        )
    """

    clicked = Signal()

    def __init__(
        self,
        annotation_type: str = "memo",  # memo, comment, link
        count: int = 1,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        type_config = {
            "memo": ("mdi6.note-edit", self._colors.info),
            "comment": ("mdi6.comment", self._colors.warning),
            "link": ("mdi6.link", self._colors.primary),
        }
        icon_name, color = type_config.get(annotation_type, ("mdi6.note-edit", self._colors.info))

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(24, 24)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color}26;
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {color}40;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if count == 1:
            from design_system import Icon
            icon = Icon(icon_name, size=14, color=color, colors=self._colors)
            layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            label = QLabel(str(count))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                font-size: {TYPOGRAPHY.text_xs}px;
                color: {color};
            """)
            layout.addWidget(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
