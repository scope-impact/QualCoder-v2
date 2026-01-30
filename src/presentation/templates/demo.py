"""
Demo script to test the UI templates.

Run with: python -m ui.templates.demo
"""

import sys
from design_system.qt_compat import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    Qt,
)

from design_system import get_theme, Button, Card, SPACING

from .app_shell import AppShell
from .layouts import SidebarLayout, ThreePanelLayout, SinglePanelLayout
from ..screens import TextCodingScreen


def create_placeholder(text: str, color: str = None) -> QWidget:
    """Create a placeholder widget for testing"""
    widget = QWidget()
    colors = get_theme("dark")

    bg_color = color or colors.surface_light
    widget.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border-radius: 8px;
        }}
    """)

    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    label = QLabel(text)
    label.setStyleSheet(f"""
        color: {colors.text_secondary};
        font-size: 14px;
    """)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)

    return widget


class DemoToolbar(QWidget):
    """Demo toolbar content"""

    def __init__(self, colors):
        super().__init__()
        self._colors = colors

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Left buttons
        layout.addWidget(Button("Open", variant="secondary", colors=colors))
        layout.addWidget(Button("Save", variant="secondary", colors=colors))

        layout.addStretch()

        # Right buttons
        layout.addWidget(Button("Settings", variant="ghost", colors=colors))
        layout.addWidget(Button("Export", variant="primary", colors=colors))


class DemoSidebarScreen:
    """Demo screen using SidebarLayout"""

    def __init__(self, colors):
        self._colors = colors

    def get_toolbar_content(self):
        return DemoToolbar(self._colors)

    def get_content(self):
        layout = SidebarLayout(colors=self._colors)

        # Sidebar
        sidebar = create_placeholder("Sidebar\n(Navigation)")
        layout.set_sidebar(sidebar)

        # Main content
        main = create_placeholder("Main Content Area")
        layout.set_content(main)

        return layout

    def get_status_message(self):
        return "Sidebar Layout Demo"


class DemoThreePanelScreen:
    """Demo screen using ThreePanelLayout"""

    def __init__(self, colors):
        self._colors = colors

    def get_toolbar_content(self):
        return DemoToolbar(self._colors)

    def get_content(self):
        layout = ThreePanelLayout(colors=self._colors)

        # Left panel
        left = create_placeholder("Left Panel\n(Code Tree)")
        layout.set_left(left)

        # Center panel
        center = create_placeholder("Center Panel\n(Document)")
        layout.set_center(center)

        # Right panel
        right = create_placeholder("Right Panel\n(Details)")
        layout.set_right(right)

        return layout

    def get_status_message(self):
        return "Three Panel Layout Demo | 24 files | 156 codes"


class DemoSinglePanelScreen:
    """Demo screen using SinglePanelLayout"""

    def __init__(self, colors):
        self._colors = colors

    def get_toolbar_content(self):
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(Button("Reset", variant="secondary", colors=self._colors))
        layout.addWidget(Button("Save Changes", variant="primary", colors=self._colors))
        return toolbar

    def get_content(self):
        layout = SinglePanelLayout(
            padding=24,
            scrollable=True,
            max_width=800,
            colors=self._colors
        )

        content = create_placeholder("Settings Form\n(Centered, Max Width 800px)")
        content.setMinimumHeight(600)
        layout.set_content(content)

        return layout

    def get_status_message(self):
        return "Settings"


def main():
    app = QApplication(sys.argv)

    colors = get_theme("dark")

    # Create app shell
    shell = AppShell(colors=colors)
    shell.set_project("demo_project.qda")

    # Create demo screens
    screens = {
        "coding": TextCodingScreen(colors=colors),  # Real text coding screen
        "reports": DemoSidebarScreen(colors),
        "files": DemoSidebarScreen(colors),
        "project": DemoSinglePanelScreen(colors),
        "ai": DemoSidebarScreen(colors),
        "help": DemoSinglePanelScreen(colors),
    }

    # Set initial screen
    shell.set_screen(screens["coding"])
    shell.set_active_menu("coding")
    shell.set_active_tab("coding")

    # Connect navigation
    def on_menu_click(menu_id):
        if menu_id in screens:
            shell.set_screen(screens[menu_id])
            shell.set_active_menu(menu_id)

    def on_tab_click(tab_id):
        # Map tabs to menus for demo
        tab_to_menu = {
            "coding": "coding",
            "reports": "reports",
            "manage": "files",
            "action_log": "project",
        }
        menu_id = tab_to_menu.get(tab_id, tab_id)
        if menu_id in screens:
            shell.set_screen(screens[menu_id])
            shell.set_active_tab(tab_id)

    shell.menu_clicked.connect(on_menu_click)
    shell.tab_clicked.connect(on_tab_click)

    shell.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
