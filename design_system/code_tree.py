"""
Code Tree components
Hierarchical tree widget for qualitative codes
"""

from typing import List, Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


@dataclass
class CodeItem:
    """Data class for a code item"""
    id: str
    name: str
    color: str
    count: int = 0
    children: List["CodeItem"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class CodeTree(QScrollArea):
    """
    Hierarchical tree widget for displaying qualitative codes.

    Usage:
        tree = CodeTree()
        tree.set_items([
            CodeItem("1", "Learning", "#FFC107", 24, children=[
                CodeItem("1.1", "Motivation", "#FFD54F", 12),
                CodeItem("1.2", "Engagement", "#FFCA28", 8),
            ]),
            CodeItem("2", "Challenges", "#F44336", 18),
        ])
        tree.item_clicked.connect(lambda id: print(f"Clicked: {id}"))
    """

    item_clicked = Signal(str)  # code_id
    item_double_clicked = Signal(str)  # code_id
    item_expanded = Signal(str, bool)  # code_id, is_expanded

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._items = []
        self._expanded = set()  # Set of expanded item IDs

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self._colors.surface};
                border: none;
            }}
        """)

        # Container widget
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self._container)

    def set_items(self, items: List[CodeItem]):
        """Set the tree items"""
        self._items = items
        self._rebuild_tree()

    def add_item(self, item: CodeItem, parent_id: str = None):
        """Add an item to the tree"""
        if parent_id:
            parent = self._find_item(parent_id, self._items)
            if parent:
                parent.children.append(item)
        else:
            self._items.append(item)
        self._rebuild_tree()

    def remove_item(self, item_id: str):
        """Remove an item from the tree"""
        self._remove_item_recursive(item_id, self._items)
        self._rebuild_tree()

    def expand_item(self, item_id: str, expanded: bool = True):
        """Expand or collapse an item"""
        if expanded:
            self._expanded.add(item_id)
        else:
            self._expanded.discard(item_id)
        self._rebuild_tree()
        self.item_expanded.emit(item_id, expanded)

    def _rebuild_tree(self):
        """Rebuild the tree widget"""
        # Clear existing widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build tree
        for item in self._items:
            self._add_tree_node(item, 0)

    def _add_tree_node(self, item: CodeItem, depth: int):
        """Add a tree node widget"""
        node = CodeTreeNode(
            item,
            depth=depth,
            expanded=item.id in self._expanded,
            has_children=len(item.children) > 0,
            colors=self._colors
        )

        node.clicked.connect(lambda: self.item_clicked.emit(item.id))
        node.double_clicked.connect(lambda: self.item_double_clicked.emit(item.id))
        node.toggle_expanded.connect(lambda: self._toggle_expanded(item.id))

        self._layout.addWidget(node)

        # Add children if expanded
        if item.id in self._expanded:
            for child in item.children:
                self._add_tree_node(child, depth + 1)

    def _toggle_expanded(self, item_id: str):
        """Toggle item expansion"""
        if item_id in self._expanded:
            self._expanded.remove(item_id)
        else:
            self._expanded.add(item_id)
        self._rebuild_tree()
        self.item_expanded.emit(item_id, item_id in self._expanded)

    def _find_item(self, item_id: str, items: List[CodeItem]) -> Optional[CodeItem]:
        """Find an item by ID"""
        for item in items:
            if item.id == item_id:
                return item
            found = self._find_item(item_id, item.children)
            if found:
                return found
        return None

    def _remove_item_recursive(self, item_id: str, items: List[CodeItem]) -> bool:
        """Remove an item recursively"""
        for i, item in enumerate(items):
            if item.id == item_id:
                items.pop(i)
                return True
            if self._remove_item_recursive(item_id, item.children):
                return True
        return False


class CodeTreeNode(QFrame):
    """Individual tree node widget"""

    clicked = Signal()
    double_clicked = Signal()
    toggle_expanded = Signal()

    def __init__(
        self,
        item: CodeItem,
        depth: int = 0,
        expanded: bool = False,
        has_children: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._item = item
        self._expanded = expanded
        self._has_children = has_children

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            SPACING.lg + (depth * SPACING.xl),  # Indent based on depth
            SPACING.sm,
            SPACING.md,
            SPACING.sm
        )
        layout.setSpacing(SPACING.sm)

        # Expand/collapse toggle
        if has_children:
            toggle = QLabel("▼" if expanded else "▶")
            toggle.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: 10px;
            """)
            toggle.setFixedWidth(16)
            toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle.mousePressEvent = lambda e: self.toggle_expanded.emit()
            layout.addWidget(toggle)
        else:
            # Spacer for alignment
            spacer = QWidget()
            spacer.setFixedWidth(16)
            layout.addWidget(spacer)

        # Color indicator
        color_dot = QFrame()
        color_dot.setFixedSize(12, 12)
        color_dot.setStyleSheet(f"""
            background-color: {item.color};
            border-radius: 3px;
        """)
        layout.addWidget(color_dot)

        # Label
        label = QLabel(item.name)
        label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(label, 1)

        # Count badge
        if item.count > 0:
            count = QLabel(str(item.count))
            count.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                background-color: {self._colors.surface_light};
                padding: 2px 6px;
                border-radius: 8px;
            """)
            layout.addWidget(count)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
