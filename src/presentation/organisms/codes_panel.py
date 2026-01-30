"""
Codes Panel Organism

A panel displaying the hierarchical code tree for qualitative coding.
Includes a header with add/search/expand actions, and navigation buttons.
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from design_system import (
    ColorPalette, get_theme, SPACING, RADIUS, TYPOGRAPHY,
    Icon, CodeTree, CodeItem,
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
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            CodesPanel {{
                background: transparent;
                border-top: 1px solid {self._colors.border};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header("Codes", "mdi6.label", [
            ("mdi6.plus", "Add code"),
            ("mdi6.magnify", "Search codes"),
            ("mdi6.unfold-more-horizontal", "Expand all"),
        ])
        layout.addWidget(header)

        # Code tree
        self._code_tree = CodeTree(colors=self._colors)
        self._code_tree.item_clicked.connect(self._on_code_click)
        layout.addWidget(self._code_tree, 1)

        # Navigation buttons
        nav = self._create_navigation()
        layout.addWidget(nav)

    def _create_header(self, title: str, icon_name: str, actions: List[tuple]) -> QFrame:
        """Create a panel header with icon and actions."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        h_layout.setSpacing(SPACING.sm)

        # Icon
        icon = Icon(icon_name, size=16, color=self._colors.primary, colors=self._colors)
        h_layout.addWidget(icon)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {self._colors.text_primary};
        """)
        h_layout.addWidget(title_label)
        h_layout.addStretch()

        # Actions
        for action_icon, tooltip in actions:
            btn = QFrame()
            btn.setFixedSize(24, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {RADIUS.xs}px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_lighter};
                }}
            """)
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            action_i = Icon(action_icon, size=14, color=self._colors.text_secondary, colors=self._colors)
            btn_layout.addWidget(action_i, alignment=Qt.AlignmentFlag.AlignCenter)
            h_layout.addWidget(btn)

        return header

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
            icon = Icon(icon_name, size=16, color=self._colors.text_secondary, colors=self._colors)
            btn_layout.addWidget(icon)

            # Capture action_id in closure
            btn.mousePressEvent = lambda e, aid=action_id: self.navigation_clicked.emit(aid)
            nav_layout.addWidget(btn, 1)

        return nav

    def set_codes(self, categories: List[Dict[str, Any]]):
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
        items = []
        for cat in categories:
            children = []
            for code in cat.get("codes", []):
                children.append(CodeItem(
                    id=code["name"],
                    name=code["name"],
                    color=code["color"],
                    count=code.get("count", 0),
                ))
            items.append(CodeItem(
                id=cat["name"],
                name=cat["name"],
                color=self._colors.text_secondary,
                count=len(children),
                children=children,
            ))
        self._code_tree.set_items(items)

    def _on_code_click(self, code_id: str):
        """Handle code click event."""
        self.code_selected.emit({"id": code_id})

    def get_selected_code(self) -> Dict[str, Any]:
        """Get the currently selected code data."""
        # TODO: Implement selection tracking in CodeTree
        return {}

    def expand_all(self):
        """Expand all code tree nodes."""
        self._code_tree.expand_all()

    def collapse_all(self):
        """Collapse all code tree nodes."""
        self._code_tree.collapse_all()
