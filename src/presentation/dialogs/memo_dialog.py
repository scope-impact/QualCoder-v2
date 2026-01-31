"""
Memo Dialog Components

Implements QC-007.08 Memo System:
- AC #1: File memo dialog
- AC #2: Code memo dialog
- AC #3: Segment memo dialog
- AC #6: Memo author and timestamp display
- AC #7: Edit existing memos
"""

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)

# Import MemoListItem molecule
from src.presentation.molecules.memo import MemoListItem


class MemoDialog(QDialog):
    """
    Base memo dialog for editing memos.

    Provides a text editor with save/cancel buttons and optional metadata display.

    Signals:
        save_clicked(): Emitted when save button is clicked
        cancel_clicked(): Emitted when cancel button is clicked
        content_changed(str): Emitted when memo content changes
    """

    save_clicked = Signal()
    cancel_clicked = Signal()
    content_changed = Signal(str)

    def __init__(
        self,
        title: str = "Memo",
        content: str = "",
        author: str = "",
        timestamp: datetime | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._title = title
        self._author = author
        self._timestamp = timestamp

        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(400, 300)

        self._setup_ui(content)

    def _setup_ui(self, content: str):
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.md, SPACING.lg, SPACING.md
        )
        content_layout.setSpacing(SPACING.md)

        # Metadata display
        if self._author or self._timestamp:
            metadata_label = QLabel(self.get_metadata_text())
            metadata_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            content_layout.addWidget(metadata_label)

        # Text editor
        self._editor = QTextEdit()
        self._editor.setPlainText(content)
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QTextEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._editor.textChanged.connect(
            lambda: self.content_changed.emit(self._editor.toPlainText())
        )
        content_layout.addWidget(self._editor, 1)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout):
        """Setup the dialog header."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Icon (can be overridden in subclasses)
        self._icon = Icon(
            "mdi6.note-text",
            size=20,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(self._icon)

        # Title
        title_label = QLabel(self._title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def _setup_footer(self, layout: QVBoxLayout):
        """Setup the dialog footer with buttons."""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        footer_layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        self._cancel_btn.clicked.connect(self._on_cancel)
        footer_layout.addWidget(self._cancel_btn)

        # Save button
        self._save_btn = QPushButton("Save")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
        """)
        self._save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(self._save_btn)

        layout.addWidget(footer)

    def _on_save(self):
        """Handle save button click."""
        self.save_clicked.emit()
        self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancel_clicked.emit()
        self.reject()

    def get_content(self) -> str:
        """Get the current memo content."""
        return self._editor.toPlainText()

    def set_content(self, content: str):
        """Set the memo content."""
        self._editor.setPlainText(content)

    def get_metadata_text(self) -> str:
        """Get formatted metadata text."""
        parts = []
        if self._author:
            parts.append(f"Author: {self._author}")
        if self._timestamp:
            parts.append(f"Last modified: {self._timestamp.strftime('%Y-%m-%d %H:%M')}")
        return " | ".join(parts) if parts else ""

    def get_title(self) -> str:
        """Get the dialog title."""
        return self._title


class FileMemoDialog(MemoDialog):
    """
    Memo dialog for file-level memos.

    Displays file icon and name in header.
    """

    def __init__(
        self,
        filename: str,
        content: str = "",
        author: str = "",
        timestamp: datetime | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        self._filename = filename
        super().__init__(
            title=f"File Memo: {filename}",
            content=content,
            author=author,
            timestamp=timestamp,
            colors=colors,
            parent=parent,
        )

    def _setup_header(self, layout: QVBoxLayout):
        """Setup header with file icon."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # File icon
        self._icon = Icon(
            "mdi6.file-document",
            size=20,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(self._icon)

        # Title
        title_label = QLabel(self._title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

    def get_title(self) -> str:
        """Get the dialog title including filename."""
        return f"File Memo: {self._filename}"


class CodeMemoDialog(MemoDialog):
    """
    Memo dialog for code-level memos.

    Displays code color indicator and name in header.
    """

    def __init__(
        self,
        code_name: str,
        code_color: str = "#808080",
        content: str = "",
        author: str = "",
        timestamp: datetime | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        self._code_name = code_name
        self._code_color = code_color
        super().__init__(
            title=f"Code Memo: {code_name}",
            content=content,
            author=author,
            timestamp=timestamp,
            colors=colors,
            parent=parent,
        )

    def _setup_header(self, layout: QVBoxLayout):
        """Setup header with code color indicator."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Color indicator
        self._color_indicator = QFrame()
        self._color_indicator.setFixedSize(20, 20)
        self._color_indicator.setStyleSheet(f"""
            QFrame {{
                background-color: {self._code_color};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        header_layout.addWidget(self._color_indicator)

        # Icon
        self._icon = Icon(
            "mdi6.label",
            size=20,
            color=self._colors.primary,
            colors=self._colors,
        )
        header_layout.addWidget(self._icon)

        # Title
        title_label = QLabel(self._title)
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)


class SegmentMemoDialog(MemoDialog):
    """
    Memo dialog for coded segment memos.

    Shows preview of the coded text segment.
    """

    def __init__(
        self,
        segment_text: str,
        code_name: str,
        code_color: str = "#808080",
        content: str = "",
        author: str = "",
        timestamp: datetime | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        self._segment_text = segment_text
        self._code_name = code_name
        self._code_color = code_color
        super().__init__(
            title=f"Segment Memo: {code_name}",
            content=content,
            author=author,
            timestamp=timestamp,
            colors=colors,
            parent=parent,
        )

    def _setup_ui(self, content: str):
        """Build the dialog UI with segment preview."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(
            SPACING.lg, SPACING.md, SPACING.lg, SPACING.md
        )
        content_layout.setSpacing(SPACING.md)

        # Segment preview
        preview_label = QLabel("Coded Text:")
        preview_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(preview_label)

        self._segment_preview = QLabel(self._truncate_text(self._segment_text, 200))
        self._segment_preview.setWordWrap(True)
        self._segment_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {self._code_color}40;
                color: {self._colors.text_primary};
                border-left: 3px solid {self._code_color};
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-style: italic;
            }}
        """)
        content_layout.addWidget(self._segment_preview)

        # Metadata display
        if self._author or self._timestamp:
            metadata_label = QLabel(self.get_metadata_text())
            metadata_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            content_layout.addWidget(metadata_label)

        # Memo label
        memo_label = QLabel("Memo:")
        memo_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        content_layout.addWidget(memo_label)

        # Text editor
        self._editor = QTextEdit()
        self._editor.setPlainText(content)
        self._editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QTextEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        self._editor.textChanged.connect(
            lambda: self.content_changed.emit(self._editor.toPlainText())
        )
        content_layout.addWidget(self._editor, 1)

        layout.addWidget(content_frame, 1)

        # Footer with buttons
        self._setup_footer(layout)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis if too long."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def get_segment_preview(self) -> str:
        """Get the segment text preview."""
        return self._segment_text


class MemosPanel(QFrame):
    """
    Panel showing all memos with filtering capability.

    Implements AC #5: View all memos panel.

    Signals:
        memo_clicked(dict): Emitted when a memo item is clicked
    """

    memo_clicked = Signal(dict)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._memos: list[dict[str, Any]] = []
        self._memo_items: list[MemoListItem] = []
        self._current_filter: str = ""

        self._setup_ui()

    def _setup_ui(self):
        """Build the panel UI."""
        self.setStyleSheet(f"""
            MemosPanel {{
                background-color: {self._colors.background};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with filter
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        title = QLabel("All Memos")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Filter buttons
        filter_types = [
            ("All", ""),
            ("Files", "file"),
            ("Codes", "code"),
            ("Segments", "segment"),
        ]
        for label, filter_type in filter_types:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(filter_type == "")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    padding: {SPACING.xs}px {SPACING.sm}px;
                    font-size: {TYPOGRAPHY.text_xs}px;
                }}
                QPushButton:hover {{
                    color: {self._colors.text_primary};
                }}
                QPushButton:checked {{
                    color: {self._colors.primary};
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
            btn.clicked.connect(lambda _checked, ft=filter_type: self.set_filter(ft))
            header_layout.addWidget(btn)

        layout.addWidget(header)

        # Scrollable memo list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self._colors.background};
            }}
        """)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(
            SPACING.md, SPACING.md, SPACING.md, SPACING.md
        )
        self._list_layout.setSpacing(SPACING.sm)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def set_memos(self, memos: list[dict[str, Any]]):
        """Set the list of memos to display."""
        self._memos = memos

        # Clear existing items
        for item in self._memo_items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._memo_items.clear()

        # Add new items
        for memo in memos:
            item = MemoListItem(memo, colors=self._colors)
            item.clicked.connect(self.memo_clicked.emit)
            self._memo_items.append(item)
            # Insert before the stretch
            self._list_layout.insertWidget(self._list_layout.count() - 1, item)

        # Apply current filter
        self._apply_filter()

    def set_filter(self, filter_type: str):
        """Filter memos by type."""
        self._current_filter = filter_type
        self._apply_filter()

    def _apply_filter(self):
        """Apply the current filter to memo items."""
        for item in self._memo_items:
            if not self._current_filter or item.get_type() == self._current_filter:
                item.set_visible_state(True)
            else:
                item.set_visible_state(False)

    def get_memo_count(self) -> int:
        """Get total number of memos."""
        return len(self._memos)

    def get_visible_memo_count(self) -> int:
        """Get number of currently visible memos."""
        return sum(1 for item in self._memo_items if item.is_visible_state())
