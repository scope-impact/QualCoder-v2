"""
Coding Toolbar Organism (QC-047.03 Simplified)

Minimal toolbar for the text coding screen containing:
- Media type selector (Text, A/V, Image, PDF) styled as tabs
- Search input
- Show Details toggle button

Structure:
┌─────────────────────────────────────────────────────────────────────────┐
│ [Text][A/V][Image][PDF]              Search transcript... [Show Details]│
└─────────────────────────────────────────────────────────────────────────┘
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    SearchBox,
    get_colors,
)


class MediaTypeTab(QPushButton):
    """Single media type tab button."""

    def __init__(self, label: str, tab_id: str, colors: ColorPalette, parent=None):
        super().__init__(label, parent)
        self._colors = colors
        self._tab_id = tab_id
        self._active = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: {self._colors.primary_foreground};
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
            """)


class CodingToolbar(QFrame):
    """
    Simplified toolbar for the text coding screen (QC-047.03).

    Contains: Media type tabs, search input, show details toggle.

    Signals:
        media_type_changed(str): Emitted when media type selection changes
        search_changed(str): Emitted when search text changes
        details_toggle_clicked(): Emitted when Show Details button is clicked
        action_triggered(str): Legacy signal (connected but never emitted)
    """

    media_type_changed = Signal(str)
    search_changed = Signal(str)
    details_toggle_clicked = Signal()

    # Legacy signal for backwards compatibility (connected but never emitted)
    action_triggered = Signal(str)

    def __init__(
        self,
        coders: list[str] = None,  # noqa: ARG002 - kept for backwards compat
        selected_coder: str = None,  # noqa: ARG002 - kept for backwards compat
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the coding toolbar.

        Args:
            coders: List of coder names (ignored in simplified layout)
            selected_coder: Initially selected coder (ignored in simplified layout)
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected_media_type = "text"
        self._details_visible = False

        self.setStyleSheet(f"""
            CodingToolbar {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Media type tabs
        self._media_tabs = {}
        for tab_id, label in [
            ("text", "Text"),
            ("av", "A/V"),
            ("image", "Image"),
            ("pdf", "PDF"),
        ]:
            tab = MediaTypeTab(label, tab_id, colors=self._colors)
            tab.clicked.connect(
                lambda _checked, tid=tab_id: self._on_media_tab_click(tid)
            )
            self._media_tabs[tab_id] = tab
            layout.addWidget(tab)

        # Set initial active tab
        self._media_tabs["text"].set_active(True)

        layout.addStretch()

        # Search box
        self._search = SearchBox(
            placeholder="Search transcript...",
            colors=self._colors,
        )
        self._search.setFixedWidth(220)
        self._search.text_changed.connect(self.search_changed.emit)
        layout.addWidget(self._search)

        # Show Details toggle button
        self._details_btn = QPushButton("Show Details")
        self._details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._details_btn.clicked.connect(self._on_details_click)
        self._style_details_button()
        layout.addWidget(self._details_btn)

    def _on_media_tab_click(self, tab_id: str):
        """Handle media tab click."""
        if tab_id != self._selected_media_type:
            # Deactivate old tab
            if self._selected_media_type in self._media_tabs:
                self._media_tabs[self._selected_media_type].set_active(False)
            # Activate new tab
            self._selected_media_type = tab_id
            self._media_tabs[tab_id].set_active(True)
            self.media_type_changed.emit(tab_id)

    def _on_details_click(self):
        """Handle details toggle click."""
        self._details_visible = not self._details_visible
        self._style_details_button()
        self.details_toggle_clicked.emit()

    def _style_details_button(self):
        """Style the details toggle button based on state."""
        if self._details_visible:
            self._details_btn.setText("Hide Details")
            self._details_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_lighter};
                }}
            """)
        else:
            self._details_btn.setText("Show Details")
            self._details_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: 1px solid {self._colors.border};
                    border-radius: {RADIUS.md}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
            """)

    def set_details_visible(self, visible: bool):
        """Set the details panel visibility state."""
        self._details_visible = visible
        self._style_details_button()

    def set_media_type(self, media_type: str):
        """Set the selected media type."""
        if media_type != self._selected_media_type:
            # Deactivate old tab
            if self._selected_media_type in self._media_tabs:
                self._media_tabs[self._selected_media_type].set_active(False)
            # Activate new tab
            self._selected_media_type = media_type
            if media_type in self._media_tabs:
                self._media_tabs[media_type].set_active(True)

    # Legacy methods for backwards compatibility
    def set_navigation(self, current: int, total: int):
        """Update the navigation display (no-op in simplified layout)."""
        pass

    def set_coder(self, coder: str):
        """Set the selected coder (no-op in simplified layout)."""
        pass
