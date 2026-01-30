"""
Memo List Item Molecule

A clickable card that displays a memo preview with type icon, name,
content preview, timestamp, and author.

Pure presentation component - emits clicked signal with memo data,
receives memo data to display.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    Icon,
    get_colors,
)


class MemoListItem(QFrame):
    """
    Single memo item for display in a list or panel.

    Displays:
    - Type icon (file, code, segment)
    - Name/title
    - Content preview (truncated)
    - Timestamp
    - Author

    Signals:
        clicked(dict): Emitted when item is clicked, with the memo data

    Example:
        memo_data = {
            "type": "code",
            "name": "Theme Analysis",
            "content": "Key themes identified...",
            "timestamp": "2024-01-15 10:30",
            "author": "Researcher"
        }
        item = MemoListItem(memo_data)
        item.clicked.connect(lambda data: print(f"Clicked: {data['name']}"))
    """

    clicked = Signal(dict)

    def __init__(
        self,
        memo_data: dict[str, Any],
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the memo list item.

        Args:
            memo_data: Dictionary with memo information:
                - type: "file", "code", or "segment"
                - name: Memo title/name
                - content: Memo text content
                - timestamp: Display timestamp string
                - author: Author name
            colors: Color palette for styling
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._memo_data = memo_data
        self._visible = True

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        """Build the item UI."""
        self.setStyleSheet(f"""
            MemoListItem {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
            MemoListItem:hover {{
                background-color: {self._colors.surface_light};
                border-color: {self._colors.primary};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING.sm)

        # Type icon
        icons = {
            "file": "mdi6.file-document",
            "code": "mdi6.label",
            "segment": "mdi6.text-box",
        }
        icon_name = icons.get(self._memo_data.get("type", "file"), "mdi6.note")
        icon = Icon(
            icon_name,
            size=14,
            color=self._colors.text_secondary,
            colors=self._colors,
        )
        header_layout.addWidget(icon)

        # Name
        name_label = QLabel(self._memo_data.get("name", "Untitled"))
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header_layout.addWidget(name_label, 1)

        # Timestamp
        timestamp_label = QLabel(self._memo_data.get("timestamp", ""))
        timestamp_label.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        header_layout.addWidget(timestamp_label)

        layout.addLayout(header_layout)

        # Content preview
        content = self._memo_data.get("content", "")
        if content:
            preview = content[:100] + "..." if len(content) > 100 else content
            content_label = QLabel(preview)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(content_label)

        # Author
        author = self._memo_data.get("author", "")
        if author:
            author_label = QLabel(f"by {author}")
            author_label.setStyleSheet(f"""
                color: {self._colors.text_disabled};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(author_label)

    def mousePressEvent(self, event):
        """Handle click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._memo_data)

    # =========================================================================
    # Public API
    # =========================================================================

    def get_type(self) -> str:
        """Get the memo type."""
        return self._memo_data.get("type", "")

    def get_name(self) -> str:
        """Get the memo name."""
        return self._memo_data.get("name", "")

    def get_memo_data(self) -> dict[str, Any]:
        """Get the full memo data."""
        return self._memo_data

    def set_visible_state(self, visible: bool):
        """Set visibility based on filter."""
        self._visible = visible
        self.setVisible(visible)

    def is_visible_state(self) -> bool:
        """Check if item should be visible."""
        return self._visible
