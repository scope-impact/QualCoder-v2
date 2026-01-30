"""
Coding Toolbar Organism

The main toolbar for the text coding screen containing:
- Media type selector (Text, Image, A/V, PDF)
- Coder dropdown
- Action buttons (help, text size, important, annotations)
- Navigation (prev/next)
- Auto-code buttons
- Memo/Annotate buttons
- Search box
"""

from typing import List
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

from design_system import (
    ColorPalette, get_theme, SPACING, RADIUS, TYPOGRAPHY,
    Icon, SearchBox,
    MediaTypeSelector, CoderSelector,
)


class CodingToolbar(QFrame):
    """
    Toolbar for the text coding screen.

    Contains: Media type selector, coder dropdown, action buttons, search.

    Signals:
        media_type_changed(str): Emitted when media type selection changes
        coder_changed(str): Emitted when coder selection changes
        action_triggered(str): Emitted when an action button is clicked
        search_changed(str): Emitted when search text changes
    """

    media_type_changed = Signal(str)
    coder_changed = Signal(str)
    action_triggered = Signal(str)
    search_changed = Signal(str)

    def __init__(
        self,
        coders: List[str] = None,
        selected_coder: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        """
        Initialize the coding toolbar.

        Args:
            coders: List of coder names for the dropdown
            selected_coder: Initially selected coder
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._coders = coders or ["default"]
        self._selected_coder = selected_coder or self._coders[0]

        self.setStyleSheet(f"""
            CodingToolbar {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Media type selector
        self._media_selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
                ("av", "A/V", "mdi6.video"),
                ("pdf", "PDF", "mdi6.file-pdf-box"),
            ],
            selected="text",
            colors=self._colors,
        )
        self._media_selector.selection_changed.connect(self.media_type_changed.emit)
        layout.addWidget(self._media_selector)

        # Divider
        layout.addWidget(self._divider())

        # Coder selector
        self._coder_selector = CoderSelector(
            coders=self._coders,
            selected=self._selected_coder,
            colors=self._colors,
        )
        self._coder_selector.coder_changed.connect(self.coder_changed.emit)
        layout.addWidget(self._coder_selector)

        # Action buttons group 1
        layout.addWidget(self._divider())
        for icon_name, tooltip, action_id in [
            ("mdi6.help-circle-outline", "Help", "help"),
            ("mdi6.format-size", "Text size", "text_size"),
            ("mdi6.star-outline", "Important only", "important"),
            ("mdi6.comment-outline", "Show annotations", "annotations"),
        ]:
            btn = self._action_button(icon_name, tooltip, action_id)
            layout.addWidget(btn)

        # Navigation
        layout.addWidget(self._divider())
        self._prev_btn = self._action_button("mdi6.chevron-left", "Previous", "prev")
        layout.addWidget(self._prev_btn)

        self._nav_label = QLabel("0 / 0")
        self._nav_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            min-width: 50px;
        """)
        self._nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._nav_label)

        self._next_btn = self._action_button("mdi6.chevron-right", "Next", "next")
        layout.addWidget(self._next_btn)

        # Auto-code buttons
        layout.addWidget(self._divider())
        for icon_name, tooltip, action_id in [
            ("mdi6.auto-fix", "Auto-code exact", "auto_exact"),
            ("mdi6.creation", "Auto-code fragment", "auto_fragment"),
            ("mdi6.account-voice", "Mark speakers", "speakers"),
            ("mdi6.undo", "Undo auto-code", "undo_auto"),
        ]:
            btn = self._action_button(icon_name, tooltip, action_id)
            layout.addWidget(btn)

        # Memo/Annotate
        layout.addWidget(self._divider())
        for icon_name, tooltip, action_id in [
            ("mdi6.note-plus", "Memo", "memo"),
            ("mdi6.note-edit", "Annotate", "annotate"),
        ]:
            btn = self._action_button(icon_name, tooltip, action_id)
            layout.addWidget(btn)

        layout.addStretch()

        # Search box
        self._search = SearchBox(placeholder="Search in text...", colors=self._colors)
        self._search.setFixedWidth(200)
        self._search.text_changed.connect(self.search_changed.emit)
        layout.addWidget(self._search)

    def _divider(self) -> QFrame:
        """Create a vertical divider."""
        div = QFrame()
        div.setFixedWidth(1)
        div.setStyleSheet(f"background-color: {self._colors.border};")
        return div

    def _action_button(self, icon_name: str, tooltip: str, action_id: str) -> QFrame:
        """Create an action button with icon."""
        btn = QFrame()
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(0, 0, 0, 0)
        icon = Icon(icon_name, size=18, color=self._colors.text_secondary, colors=self._colors)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        btn.mousePressEvent = lambda e: self.action_triggered.emit(action_id)
        return btn

    def set_navigation(self, current: int, total: int):
        """Update the navigation display."""
        self._nav_label.setText(f"{current} / {total}")

    def set_media_type(self, media_type: str):
        """Set the selected media type."""
        self._media_selector.set_selected(media_type)

    def set_coder(self, coder: str):
        """Set the selected coder."""
        self._coder_selector.set_coder(coder)
