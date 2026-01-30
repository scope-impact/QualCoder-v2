"""
Document/Text components - Generic UI primitives for text display.

This module provides reusable text display components that can be used
in any PySide6 application. For qualitative coding-specific components
(highlighting, code segments, annotations), see:
    src/presentation/organisms/text_highlighter.py
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors, hex_to_rgba

# =============================================================================
# Text Color Helper
# =============================================================================


class TextColor:
    """
    Determines contrasting text color (black or white) for a given background.

    Based on luminance calculation with a curated list of known dark colors
    that need white text for readability.

    Usage:
        color = TextColor("#FFC107")
        text_color = color.recommendation  # "#000000" (black)

        color = TextColor("#1B5E20")
        text_color = color.recommendation  # "#eeeeee" (white)
    """

    # Colors that need white text for contrast
    # Updated for Scholar's Desk palette
    DARK_COLORS = {
        "#EB7333",
        "#E65100",
        "#C54949",
        "#B71C1C",
        "#CB5E3C",
        "#BF360C",
        "#FA58F4",
        "#B76E95",
        "#9F3E72",
        "#880E4F",
        "#7D26CD",
        "#1B5E20",
        "#487E4B",
        "#5E9179",
        "#AC58FA",
        "#9090E3",
        "#6B6BDA",
        "#4646D1",
        "#3498DB",
        "#6D91C6",
        "#3D6CB3",
        "#0D47A1",
        "#5882FA",
        "#9651D7",
        "#673AB7",
        "#3F51B5",
        "#2196F3",
        "#4F46E5",
        "#00BCD4",
        "#4CAF50",
        "#8BC34A",
        "#795548",
        "#607D8B",
        "#9C27B0",
        "#E91E63",
        "#F44336",
        # Scholar's Desk palette additions
        "#1E3A5F",
        "#3B5998",
        "#152238",  # Prussian ink family
        "#C84B31",
        "#9A3412",  # Vermilion family
        "#2D6A4F",
        "#40916C",  # Forest green family
        "#9B2226",
        "#AE2012",  # Carmine family
        "#2A6F97",
        "#468FAF",  # Steel blue family
    }

    def __init__(self, hex_color: str):
        """
        Initialize with a hex color string.

        Args:
            hex_color: Hex color like "#FFC107"
        """
        self._color = hex_color.upper()
        self.recommendation = self._calculate_recommendation()

    def _calculate_recommendation(self) -> str:
        """Calculate whether black or white text provides better contrast."""
        # Check against known dark colors
        if self._color in self.DARK_COLORS:
            return "#EEEEEE"

        # Fallback: calculate luminance
        try:
            hex_clean = self._color.lstrip("#")
            if len(hex_clean) == 6:
                r = int(hex_clean[0:2], 16)
                g = int(hex_clean[2:4], 16)
                b = int(hex_clean[4:6], 16)
                # Perceived luminance formula
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                return "#000000" if luminance > 0.5 else "#EEEEEE"
        except (ValueError, IndexError):
            pass

        return "#000000"  # Default to black text


# =============================================================================
# Text Panel Component
# =============================================================================


class TextPanel(QFrame):
    """
    Generic panel for displaying text documents.

    Supports optional header with title, badge, and stats display.
    This is a pure display component - for qualitative coding features,
    see TextHighlighter in the presentation layer.

    Usage:
        # Basic usage
        panel = TextPanel()
        panel.set_text("Document content...")
        panel.text_selected.connect(self.on_selection)

        # With header
        panel = TextPanel(
            title="Document.txt",
            badge_text="Draft",
            show_header=True
        )
        panel.set_stats([
            ("mdi6.file-word", "1,234 words"),
            ("mdi6.clock", "5 min read"),
        ])
    """

    text_selected = Signal(str, int, int)  # text, start, end

    def __init__(
        self,
        title: str = "",
        badge_text: str = None,
        show_header: bool = False,
        editable: bool = False,
        show_line_numbers: bool = False,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._editable = editable
        self._title = title

        self.setStyleSheet(f"""
            TextPanel {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (optional)
        if show_header:
            self._header = QFrame()
            self._header.setStyleSheet(f"""
                QFrame {{
                    background-color: {self._colors.surface};
                    border-bottom: 1px solid {self._colors.border};
                }}
            """)
            header_layout = QHBoxLayout(self._header)
            header_layout.setContentsMargins(
                SPACING.lg, SPACING.md, SPACING.lg, SPACING.md
            )
            header_layout.setSpacing(SPACING.sm)

            # Title with icon
            title_layout = QHBoxLayout()
            title_layout.setSpacing(SPACING.sm)

            from .icons import Icon

            self._title_icon = Icon(
                "mdi6.file-document-edit",
                size=16,
                color=self._colors.primary,
                colors=self._colors,
            )
            title_layout.addWidget(self._title_icon)

            self._title_label = QLabel(title)
            self._title_label.setStyleSheet(f"""
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            title_layout.addWidget(self._title_label)

            # Badge
            if badge_text:
                from .components import Badge

                self._badge = Badge(badge_text, variant="info", colors=self._colors)
                title_layout.addWidget(self._badge)

            header_layout.addLayout(title_layout)
            header_layout.addStretch()

            # Stats container
            self._stats_layout = QHBoxLayout()
            self._stats_layout.setSpacing(SPACING.md)
            header_layout.addLayout(self._stats_layout)

            main_layout.addWidget(self._header)

        # Content area
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

        # Line numbers
        if show_line_numbers:
            self._line_numbers = LineNumberArea(colors=self._colors)
            content_layout.addWidget(self._line_numbers)

        # Text area
        self._text_edit = QPlainTextEdit()
        self._text_edit.setReadOnly(not editable)
        self._text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                padding: {SPACING.xl}px {SPACING.xxl}px;
                font-family: 'Roboto', sans-serif;
                font-size: 15px;
                line-height: 1.8;
            }}
        """)
        self._text_edit.selectionChanged.connect(self._on_selection_changed)

        if show_line_numbers:
            self._text_edit.blockCountChanged.connect(self._update_line_numbers)
            self._text_edit.updateRequest.connect(self._line_numbers.update)

        content_layout.addWidget(self._text_edit, 1)
        main_layout.addWidget(content_frame, 1)

    def set_text(self, text: str):
        self._text_edit.setPlainText(text)

    def get_text(self) -> str:
        return self._text_edit.toPlainText()

    def set_title(self, title: str):
        """Update the header title"""
        self._title = title
        if hasattr(self, "_title_label"):
            self._title_label.setText(title)

    def set_stats(self, stats: list[tuple[str, str]]):
        """Set stats in header. List of (icon_name, text) tuples."""
        if not hasattr(self, "_stats_layout"):
            return

        # Clear existing stats
        while self._stats_layout.count():
            item = self._stats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new stats as icon+text widgets
        from .icons import Icon

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

    def get_selection(self) -> tuple[int, int] | None:
        """Get current text selection range (start, end) or None if no selection"""
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            return (cursor.selectionStart(), cursor.selectionEnd())
        return None

    def scroll_to_position(self, pos: int):
        """Scroll to a specific text position"""
        cursor = self._text_edit.textCursor()
        cursor.setPosition(pos)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.ensureCursorVisible()

    def _on_selection_changed(self):
        cursor = self._text_edit.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            self.text_selected.emit(text, start, end)

    def _update_line_numbers(self):
        if hasattr(self, "_line_numbers"):
            count = self._text_edit.blockCount()
            self._line_numbers.set_line_count(count)


# =============================================================================
# Line Number Area
# =============================================================================


class LineNumberArea(QFrame):
    """
    Line number gutter for text editors.

    Usage:
        line_numbers = LineNumberArea()
        line_numbers.set_line_count(100)
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._line_count = 1

        self.setFixedWidth(50)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, SPACING.md, 0, SPACING.md)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._labels = []

    def set_line_count(self, count: int):
        self._line_count = count
        # Update line number labels
        while len(self._labels) < count:
            label = QLabel(str(len(self._labels) + 1))
            label.setStyleSheet(f"""
                color: {self._colors.text_disabled};
                font-family: 'Menlo';
                font-size: {TYPOGRAPHY.text_sm}px;
                padding-right: {SPACING.sm}px;
            """)
            label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            label.setFixedHeight(22)  # Approximate line height
            self._labels.append(label)
            self._layout.addWidget(label)

        # Hide excess labels
        for i, label in enumerate(self._labels):
            label.setVisible(i < count)


# =============================================================================
# Selection Popup
# =============================================================================


class SelectionPopup(QFrame):
    """
    Generic popup menu for text selection actions.

    Appears when text is selected, showing quick action buttons.
    Configure your own actions or use with default placeholder actions.

    Usage:
        popup = SelectionPopup()
        popup.action_clicked.connect(self.handle_action)
        popup.show_at(x, y)

        # With custom actions
        popup = SelectionPopup(actions=[
            ("mdi6.content-copy", "Copy", "copy", True),
            ("mdi6.magnify", "Search", "search", False),
        ])
    """

    action_clicked = Signal(str)  # action_id

    # Default actions - generic text operations
    DEFAULT_ACTIONS = [
        ("mdi6.content-copy", "Copy", "copy", True),
        ("mdi6.note-plus", "Add note", "note", False),
        ("mdi6.magnify", "Search", "search", False),
        ("mdi6.share", "Share", "share", False),
    ]

    def __init__(
        self,
        actions: list[tuple[str, str, str]] = None,  # [(icon, tooltip, action_id), ...]
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setStyleSheet(f"""
            SelectionPopup {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        actions_to_use = actions or self.DEFAULT_ACTIONS

        from .icons import Icon

        for action_tuple in actions_to_use:
            if len(action_tuple) == 4:
                icon_name, tooltip, action_id, is_primary = action_tuple
            else:
                icon_name, tooltip, action_id = action_tuple
                is_primary = False

            btn = QFrame()
            btn.setFixedSize(32, 32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)

            if is_primary:
                btn.setStyleSheet(f"""
                    QFrame {{
                        background-color: {self._colors.primary};
                        border-radius: {RADIUS.sm}px;
                    }}
                    QFrame:hover {{
                        background-color: {self._colors.primary_light};
                    }}
                """)
                icon_color = "white"
            else:
                btn.setStyleSheet(f"""
                    QFrame {{
                        background-color: transparent;
                        border-radius: {RADIUS.sm}px;
                    }}
                    QFrame:hover {{
                        background-color: {self._colors.surface_light};
                    }}
                """)
                icon_color = self._colors.text_secondary

            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(0, 0, 0, 0)

            icon = Icon(icon_name, size=16, color=icon_color, colors=self._colors)
            btn_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

            # Store action_id and connect click
            btn._action_id = action_id
            btn.mousePressEvent = lambda _e, aid=action_id: self._emit_action(aid)

            layout.addWidget(btn)

    def _emit_action(self, action_id: str):
        self.action_clicked.emit(action_id)
        self.hide()

    def show_at(self, x: int, y: int):
        """Show popup at specific screen coordinates"""
        self.move(x, y)
        self.show()

    def show_near_selection(self, global_pos):
        """Show popup near a selection point, offset slightly above"""
        self.move(
            global_pos.x() - self.width() // 2, global_pos.y() - self.height() - 10
        )
        self.show()


# =============================================================================
# Transcript Panel
# =============================================================================


class TranscriptPanel(QFrame):
    """
    Generic audio/video transcript panel with timestamps.

    Usage:
        panel = TranscriptPanel()
        panel.add_segment(0.0, 5.5, "Speaker 1", "Hello, how are you?")
        panel.timestamp_clicked.connect(self.seek_to)
    """

    timestamp_clicked = Signal(float)  # seconds

    def __init__(
        self, show_speakers: bool = True, colors: ColorPalette = None, parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._show_speakers = show_speakers
        self._segments = []

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        self._layout.setSpacing(SPACING.sm)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._container)
        main_layout.addWidget(scroll)

    def add_segment(self, start_time: float, end_time: float, speaker: str, text: str):
        segment = TranscriptSegment(
            start_time=start_time,
            end_time=end_time,
            speaker=speaker if self._show_speakers else None,
            text=text,
            colors=self._colors,
        )
        segment.timestamp_clicked.connect(self.timestamp_clicked.emit)
        self._segments.append(segment)
        self._layout.addWidget(segment)

    def clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._segments = []

    def highlight_time(self, seconds: float):
        for segment in self._segments:
            segment.set_highlighted(segment._start_time <= seconds < segment._end_time)


class TranscriptSegment(QFrame):
    """Individual transcript segment with timestamp"""

    timestamp_clicked = Signal(float)

    def __init__(
        self,
        start_time: float,
        end_time: float,
        speaker: str = None,
        text: str = "",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._start_time = start_time
        self._end_time = end_time
        self._highlighted = False

        self._update_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Timestamp
        time_str = self._format_time(start_time)
        time_btn = QPushButton(time_str)
        time_btn.setFixedWidth(60)
        time_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        time_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.primary};
                border: none;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-family: 'Menlo';
                text-align: left;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        time_btn.clicked.connect(lambda: self.timestamp_clicked.emit(start_time))
        layout.addWidget(time_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(SPACING.xs)

        if speaker:
            speaker_label = QLabel(speaker)
            speaker_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            """)
            content_layout.addWidget(speaker_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            line-height: 1.4;
        """)
        content_layout.addWidget(text_label)

        layout.addLayout(content_layout, 1)

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def _update_style(self):
        if self._highlighted:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {hex_to_rgba(self._colors.primary, 0.15)};
                    border-radius: {RADIUS.sm}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {RADIUS.sm}px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)

    def set_highlighted(self, highlighted: bool):
        self._highlighted = highlighted
        self._update_style()
