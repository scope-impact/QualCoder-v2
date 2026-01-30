"""
Three Panel Layout

A three-panel layout with left sidebar, center content, and right panel.

┌──────────┬────────────────────┬──────────┐
│          │                    │          │
│   LEFT   │      CENTER        │  RIGHT   │
│  (codes) │    (document)      │ (details)│
│          │                    │          │
└──────────┴────────────────────┴──────────┘

This is the classic coding interface layout.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_theme


class ThreePanelLayout(QWidget):
    """
    Layout with left panel + center + right panel.

    All panels are resizable via splitters.
    Center panel expands to fill available space.

    Usage:
        layout = ThreePanelLayout(colors=colors)

        # Set left panel (e.g., code tree)
        layout.set_left(code_tree)

        # Set center panel (e.g., document)
        layout.set_center(text_panel)

        # Set right panel (e.g., details)
        layout.set_right(details_panel)
    """

    def __init__(
        self,
        left_width: int = 280,
        right_width: int = 280,
        left_min: int = 200,
        left_max: int = 400,
        right_min: int = 200,
        right_max: int = 400,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._left_width = left_width
        self._right_width = right_width
        self._left_min = left_min
        self._left_max = left_max
        self._right_min = right_min
        self._right_max = right_max

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {self._colors.border};
            }}
            QSplitter::handle:hover {{
                background-color: {self._colors.primary};
            }}
        """)

        # Left panel
        self._left = QFrame()
        self._left.setMinimumWidth(self._left_min)
        self._left.setMaximumWidth(self._left_max)
        self._left.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        self._left_layout = QVBoxLayout(self._left)
        self._left_layout.setContentsMargins(0, 0, 0, 0)
        self._left_layout.setSpacing(0)

        self._splitter.addWidget(self._left)

        # Center panel
        self._center = QFrame()
        self._center.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.background};
            }}
        """)
        self._center.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._center_layout = QVBoxLayout(self._center)
        self._center_layout.setContentsMargins(0, 0, 0, 0)
        self._center_layout.setSpacing(0)

        self._splitter.addWidget(self._center)

        # Right panel
        self._right = QFrame()
        self._right.setMinimumWidth(self._right_min)
        self._right.setMaximumWidth(self._right_max)
        self._right.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-left: 1px solid {self._colors.border};
            }}
        """)

        self._right_layout = QVBoxLayout(self._right)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(0)

        self._splitter.addWidget(self._right)

        # Set initial sizes
        center_width = 1000 - self._left_width - self._right_width
        self._splitter.setSizes([self._left_width, center_width, self._right_width])

        layout.addWidget(self._splitter)

    def set_left(self, widget: QWidget):
        """Set left panel content"""
        self._clear_layout(self._left_layout)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._left_layout.addWidget(widget)

    def set_center(self, widget: QWidget):
        """Set center panel content"""
        self._clear_layout(self._center_layout)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._center_layout.addWidget(widget)

    def set_right(self, widget: QWidget):
        """Set right panel content"""
        self._clear_layout(self._right_layout)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._right_layout.addWidget(widget)

    def _clear_layout(self, layout: QVBoxLayout):
        """Remove all widgets from a layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def hide_left(self):
        """Hide left panel"""
        self._left.hide()

    def show_left(self):
        """Show left panel"""
        self._left.show()

    def hide_right(self):
        """Hide right panel"""
        self._right.hide()

    def show_right(self):
        """Show right panel"""
        self._right.show()

    @property
    def left(self) -> QFrame:
        """Access left panel container"""
        return self._left

    @property
    def center(self) -> QFrame:
        """Access center panel container"""
        return self._center

    @property
    def right(self) -> QFrame:
        """Access right panel container"""
        return self._right

    @property
    def splitter(self) -> QSplitter:
        """Access splitter for custom configuration"""
        return self._splitter
