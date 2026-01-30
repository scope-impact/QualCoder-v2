"""
Codes Panel Organism

A panel displaying the hierarchical code tree for qualitative coding.
Includes a header with add/search/expand actions, and navigation buttons.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from design_system import (
    RADIUS,
    SPACING,
    CodeItem,
    CodeTree,
    ColorPalette,
    Icon,
    PanelHeader,
    get_colors,
)


class CodesPanel(QFrame):
    """
    Panel showing code tree and navigation.

    Signals:
        code_selected(dict): Emitted when a code is selected, with code data
        navigation_clicked(str): Emitted when navigation button is clicked (prev, next, all)
    """

    code_selected = Signal(dict)
    navigation_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the codes panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._selected_code: dict[str, Any] = {}

        self.setStyleSheet(f"""
            CodesPanel {{
                background: {self._colors.transparent};
                border-top: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = PanelHeader("Codes", icon="mdi6.label", colors=self._colors)
        header.add_action("mdi6.plus", tooltip="Add code")
        header.add_action("mdi6.magnify", tooltip="Search codes")
        header.add_action("mdi6.unfold-more-horizontal", tooltip="Expand all")
        layout.addWidget(header)

        # Code tree
        self._code_tree = CodeTree(colors=self._colors)
        self._code_tree.item_clicked.connect(self._on_code_click)
        layout.addWidget(self._code_tree, 1)

        # Navigation buttons
        nav = self._create_navigation()
        layout.addWidget(nav)

    def _create_navigation(self) -> QFrame:
        """Create the navigation buttons bar."""
        nav = QFrame()
        nav.setStyleSheet(f"border-top: 1px solid {self._colors.border};")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        nav_layout.setSpacing(SPACING.xs)

        nav_buttons = [
            ("mdi6.skip-previous", "Previous code instance", "prev"),
            ("mdi6.skip-next", "Next code instance", "next"),
            ("mdi6.view-grid", "Show all instances", "all"),
        ]

        for icon_name, tooltip, action_id in nav_buttons:
            btn = QFrame()
            btn.setFixedHeight(28)
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
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(SPACING.md, 0, SPACING.md, 0)
            icon = Icon(
                icon_name,
                size=16,
                color=self._colors.text_secondary,
                colors=self._colors,
            )
            btn_layout.addWidget(icon)

            # Capture action_id in closure
            btn.mousePressEvent = (
                lambda _e, aid=action_id: self.navigation_clicked.emit(aid)
            )
            nav_layout.addWidget(btn, 1)

        return nav

    def set_codes(self, categories: list[dict[str, Any]]):
        """
        Set the code tree data.

        Args:
            categories: List of category dictionaries with keys:
                - name: Category name
                - codes: List of code dictionaries with:
                    - name: Code name
                    - color: Code color hex string
                    - count (optional): Number of instances
        """
        if not categories:
            self._code_tree.set_items([])
            return

        items = []
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            cat_name = cat.get("name", "Unnamed")
            children = []
            for code in cat.get("codes", []):
                if not isinstance(code, dict):
                    continue
                code_name = code.get("name", "")
                if not code_name:
                    continue
                children.append(
                    CodeItem(
                        id=code_name,
                        name=code_name,
                        color=code.get("color", self._colors.fallback_code_color),
                        count=code.get("count", 0),
                    )
                )
            items.append(
                CodeItem(
                    id=cat_name,
                    name=cat_name,
                    color=self._colors.text_secondary,
                    count=len(children),
                    children=children,
                )
            )
        self._code_tree.set_items(items)

    def _on_code_click(self, code_id: str):
        """Handle code click event."""
        self._selected_code = {"id": code_id}
        self.code_selected.emit(self._selected_code)

    def get_selected_code(self) -> dict[str, Any]:
        """Get the currently selected code data."""
        return self._selected_code.copy() if self._selected_code else {}

    def expand_all(self):
        """Expand all code tree nodes."""
        self._code_tree.expand_all()

    def collapse_all(self):
        """Collapse all code tree nodes."""
        self._code_tree.collapse_all()
