"""
Sidebar Layout

A two-panel layout with a sidebar and main content area.

┌──────────┬────────────────────────────┐
│          │                            │
│ SIDEBAR  │       MAIN CONTENT         │
│  (fixed) │       (flexible)           │
│          │                            │
└──────────┴────────────────────────────┘
"""

from design_system.qt_compat import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QSizePolicy,
    Qt,
)

from design_system import ColorPalette, get_theme, SPACING


class SidebarLayout(QWidget):
    """
    Layout with sidebar + main content.

    The sidebar is resizable within min/max bounds.
    Main content expands to fill remaining space.

    Usage:
        layout = SidebarLayout(colors=colors)

        # Set sidebar content
        nav_list = NavList(...)
        layout.set_sidebar(nav_list)

        # Set main content
        settings_form = SettingsForm(...)
        layout.set_content(settings_form)
    """

    def __init__(
        self,
        sidebar_width: int = 280,
        sidebar_min: int = 200,
        sidebar_max: int = 400,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._sidebar_width = sidebar_width
        self._sidebar_min = sidebar_min
        self._sidebar_max = sidebar_max

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter for resizable panels
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

        # Sidebar container
        self._sidebar = QFrame()
        self._sidebar.setMinimumWidth(self._sidebar_min)
        self._sidebar.setMaximumWidth(self._sidebar_max)
        self._sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar_layout.setSpacing(0)

        self._splitter.addWidget(self._sidebar)

        # Main content container
        self._main = QFrame()
        self._main.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.background};
            }}
        """)
        self._main.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self._main_layout = QVBoxLayout(self._main)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._splitter.addWidget(self._main)

        # Set initial sizes
        self._splitter.setSizes([self._sidebar_width, 1000 - self._sidebar_width])

        layout.addWidget(self._splitter)

    def set_sidebar(self, widget: QWidget):
        """Set sidebar content"""
        self._clear_layout(self._sidebar_layout)
        widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
        self._sidebar_layout.addWidget(widget)

    def set_content(self, widget: QWidget):
        """Set main content"""
        self._clear_layout(self._main_layout)
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._main_layout.addWidget(widget)

    def _clear_layout(self, layout: QVBoxLayout):
        """Remove all widgets from a layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    @property
    def sidebar(self) -> QFrame:
        """Access sidebar container"""
        return self._sidebar

    @property
    def main(self) -> QFrame:
        """Access main content container"""
        return self._main

    @property
    def splitter(self) -> QSplitter:
        """Access splitter for custom configuration"""
        return self._splitter
