"""
Document/Text components
Text panels, highlights, annotations, and transcript widgets
"""

from typing import List, Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QSizePolicy, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class TextPanel(QFrame):
    """
    Panel for displaying and editing text documents.

    Supports optional header with title, badge, and stats display.

    Usage:
        # Basic usage
        panel = TextPanel()
        panel.set_text("Interview transcript content...")
        panel.text_selected.connect(self.on_selection)

        # With header
        panel = TextPanel(
            title="ID2.odt",
            badge_text="Case: ID2",
            show_header=True
        )
        panel.set_stats([
            ("mdi6.layers", "2 overlapping"),
            ("mdi6.label", "5 codes applied"),
        ])
    """

    text_selected = pyqtSignal(str, int, int)  # text, start, end

    def __init__(
        self,
        title: str = "",
        badge_text: str = None,
        show_header: bool = False,
        editable: bool = False,
        show_line_numbers: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
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
            header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
            header_layout.setSpacing(SPACING.sm)

            # Title with icon
            title_layout = QHBoxLayout()
            title_layout.setSpacing(SPACING.sm)

            from .icons import Icon
            self._title_icon = Icon("mdi6.file-document-edit", size=16, color=self._colors.primary, colors=self._colors)
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
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)

    def set_stats(self, stats: List[Tuple[str, str]]):
        """Set stats in header. List of (icon_name, text) tuples."""
        if not hasattr(self, '_stats_layout'):
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

    def get_selection(self) -> Optional[Tuple[int, int]]:
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
        if hasattr(self, '_line_numbers'):
            count = self._text_edit.blockCount()
            self._line_numbers.set_line_count(count)


class LineNumberArea(QFrame):
    """Line number gutter for text editors"""

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
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
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setFixedHeight(22)  # Approximate line height
            self._labels.append(label)
            self._layout.addWidget(label)

        # Hide excess labels
        for i, label in enumerate(self._labels):
            label.setVisible(i < count)


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

    clicked = pyqtSignal(str)  # segment_id

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
        overlap_style = "text-decoration: overline; text-decoration-color: #FF9800;" if overlap_count > 1 else ""

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
            {overlap_style}
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

    clicked = pyqtSignal()

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
            "memo": ("📝", self._colors.info),
            "comment": ("💬", self._colors.warning),
            "link": ("🔗", self._colors.primary),
        }
        icon, color = type_config.get(annotation_type, ("📝", self._colors.info))

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

        label = QLabel(icon if count == 1 else f"{count}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            font-size: {TYPOGRAPHY.text_xs if count > 1 else 12}px;
            color: {color if count > 1 else 'inherit'};
        """)
        layout.addWidget(label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class SelectionPopup(QFrame):
    """
    Popup menu for text selection actions.

    Appears when text is selected, showing quick action buttons.

    Usage:
        popup = SelectionPopup()
        popup.action_clicked.connect(self.handle_action)
        popup.show_at(x, y)

        # With custom actions
        popup = SelectionPopup(actions=[
            ("mdi6.label", "Apply Code", "apply_code"),
            ("mdi6.plus", "Quick Code", "quick_code"),
        ])
    """

    action_clicked = pyqtSignal(str)  # action_id

    # Default actions matching the mockup
    DEFAULT_ACTIONS = [
        ("mdi6.label", "Apply selected code", "apply_code", True),  # primary
        ("mdi6.plus", "Quick code", "quick_code", False),
        ("mdi6.note-edit", "Add annotation", "annotate", False),
        ("mdi6.note-plus", "Add memo", "memo", False),
    ]

    def __init__(
        self,
        actions: List[Tuple[str, str, str]] = None,  # [(icon, tooltip, action_id), ...]
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

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
            btn.mousePressEvent = lambda e, aid=action_id: self._emit_action(aid)

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
        self.move(global_pos.x() - self.width() // 2, global_pos.y() - self.height() - 10)
        self.show()


class TranscriptPanel(QFrame):
    """
    Audio/video transcript panel with timestamps.

    Usage:
        panel = TranscriptPanel()
        panel.add_segment(0.0, 5.5, "Speaker 1", "Hello, how are you?")
        panel.timestamp_clicked.connect(self.seek_to)
    """

    timestamp_clicked = pyqtSignal(float)  # seconds

    def __init__(
        self,
        show_speakers: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
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

    def add_segment(
        self,
        start_time: float,
        end_time: float,
        speaker: str,
        text: str
    ):
        segment = TranscriptSegment(
            start_time=start_time,
            end_time=end_time,
            speaker=speaker if self._show_speakers else None,
            text=text,
            colors=self._colors
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

    timestamp_clicked = pyqtSignal(float)

    def __init__(
        self,
        start_time: float,
        end_time: float,
        speaker: str = None,
        text: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
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
                    background-color: {self._colors.primary}26;
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
