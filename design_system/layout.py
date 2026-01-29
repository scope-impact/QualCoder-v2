"""
Layout components
App structure and container components
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QSizePolicy, QMainWindow
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from .tokens import SPACING, RADIUS, TYPOGRAPHY, LAYOUT, ColorPalette, get_theme


class AppContainer(QWidget):
    """
    Main application container with full-height flex layout.

    Usage:
        app = AppContainer()
        app.set_title_bar(TitleBar("QualCoder"))
        app.set_menu_bar(MenuBar())
        app.set_content(main_widget)
        app.set_status_bar(StatusBar())
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
                color: {self._colors.text_primary};
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Placeholders
        self._title_bar = None
        self._menu_bar = None
        self._tab_bar = None
        self._toolbar = None
        self._content = None
        self._status_bar = None

    def set_title_bar(self, widget: QWidget):
        if self._title_bar:
            self._layout.removeWidget(self._title_bar)
        self._title_bar = widget
        self._layout.insertWidget(0, widget)

    def set_menu_bar(self, widget: QWidget):
        if self._menu_bar:
            self._layout.removeWidget(self._menu_bar)
        self._menu_bar = widget
        idx = 1 if self._title_bar else 0
        self._layout.insertWidget(idx, widget)

    def set_tab_bar(self, widget: QWidget):
        if self._tab_bar:
            self._layout.removeWidget(self._tab_bar)
        self._tab_bar = widget
        idx = sum([1 for w in [self._title_bar, self._menu_bar] if w])
        self._layout.insertWidget(idx, widget)

    def set_toolbar(self, widget: QWidget):
        if self._toolbar:
            self._layout.removeWidget(self._toolbar)
        self._toolbar = widget
        idx = sum([1 for w in [self._title_bar, self._menu_bar, self._tab_bar] if w])
        self._layout.insertWidget(idx, widget)

    def set_content(self, widget: QWidget):
        if self._content:
            self._layout.removeWidget(self._content)
        self._content = widget
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        idx = sum([1 for w in [self._title_bar, self._menu_bar, self._tab_bar, self._toolbar] if w])
        self._layout.insertWidget(idx, widget)

    def set_status_bar(self, widget: QWidget):
        if self._status_bar:
            self._layout.removeWidget(self._status_bar)
        self._status_bar = widget
        self._layout.addWidget(widget)


class TitleBar(QFrame):
    """
    Window title bar with logo and window controls.

    Usage:
        title_bar = TitleBar("QualCoder", show_controls=True)
        title_bar.close_clicked.connect(self.close)
    """

    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()

    def __init__(
        self,
        title: str = "",
        show_logo: bool = True,
        show_controls: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setFixedHeight(LAYOUT.titlebar_height)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        layout.setSpacing(SPACING.sm)

        # Logo and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(SPACING.sm)

        if show_logo:
            logo = QLabel("Q")
            logo.setFixedSize(24, 24)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo.setStyleSheet(f"""
                background-color: {self._colors.primary};
                color: white;
                border-radius: {RADIUS.xs}px;
                font-weight: bold;
                font-size: 12px;
            """)
            title_layout.addWidget(logo)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {self._colors.text_primary};
        """)
        title_layout.addWidget(title_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Window controls
        if show_controls:
            controls = QHBoxLayout()
            controls.setSpacing(SPACING.sm)

            for color, signal in [
                ("#FF5F56", self.close_clicked),
                ("#FFBD2E", self.minimize_clicked),
                ("#27C93F", self.maximize_clicked),
            ]:
                btn = QPushButton()
                btn.setFixedSize(12, 12)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: none;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        opacity: 0.8;
                    }}
                """)
                btn.clicked.connect(signal.emit)
                controls.addWidget(btn)

            layout.addLayout(controls)


class MenuBar(QFrame):
    """
    Horizontal menu bar with menu items.

    Usage:
        menu_bar = MenuBar()
        menu_bar.add_item("File", on_click=self.show_file_menu)
        menu_bar.add_item("Edit", on_click=self.show_edit_menu)
    """

    item_clicked = pyqtSignal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setFixedHeight(LAYOUT.menubar_height)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.sm, 0, SPACING.sm, 0)
        self._layout.setSpacing(SPACING.xs)
        self._layout.addStretch()

    def add_item(self, text: str, on_click=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: {RADIUS.xs}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)

        if on_click:
            btn.clicked.connect(on_click)
        btn.clicked.connect(lambda: self.item_clicked.emit(text))

        # Insert before stretch
        self._layout.insertWidget(self._layout.count() - 1, btn)
        return btn


class TabBar(QFrame):
    """
    Tab navigation bar with icons.

    Usage:
        tab_bar = TabBar()
        tab_bar.add_tab("Coding", icon="code", active=True)
        tab_bar.add_tab("Reports", icon="assessment")
        tab_bar.tab_changed.connect(self.on_tab_change)
    """

    tab_changed = pyqtSignal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._tabs = []
        self._active_tab = None

        self.setFixedHeight(LAYOUT.tabbar_height)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()

    def add_tab(self, text: str, icon: str = None, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setProperty("tab_name", text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._set_active(text))

        self._tabs.append(btn)
        self._layout.insertWidget(self._layout.count() - 1, btn)

        if active or len(self._tabs) == 1:
            self._set_active(text)
        else:
            self._style_tab(btn, False)

        return btn

    def _set_active(self, tab_name: str):
        self._active_tab = tab_name
        for btn in self._tabs:
            is_active = btn.property("tab_name") == tab_name
            self._style_tab(btn, is_active)
        self.tab_changed.emit(tab_name)

    def _style_tab(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.primary};
                    border: none;
                    border-bottom: 2px solid {self._colors.primary};
                    padding: 0 {SPACING.xxl}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-bottom: 2px solid transparent;
                    padding: 0 {SPACING.xxl}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{
                    color: {self._colors.text_primary};
                    background-color: {self._colors.surface_light};
                }}
            """)


class Toolbar(QFrame):
    """
    Action toolbar with button groups and dividers.

    Usage:
        toolbar = Toolbar()
        group1 = toolbar.add_group()
        group1.add_button("Save", icon="💾", on_click=self.save)
        group1.add_button("Undo", icon="↩")
        toolbar.add_divider()
        group2 = toolbar.add_group()
        group2.add_button("Code", icon="🏷️", active=True)
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setMinimumHeight(LAYOUT.toolbar_height)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        self._layout.setSpacing(SPACING.sm)
        self._layout.addStretch()

    def add_group(self) -> "ToolbarGroup":
        group = ToolbarGroup(colors=self._colors)
        self._layout.insertWidget(self._layout.count() - 1, group)
        return group

    def add_divider(self):
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"background-color: {self._colors.border};")
        self._layout.insertWidget(self._layout.count() - 1, divider)

    def add_button(self, text: str = "", icon: str = None, on_click=None) -> QPushButton:
        """Convenience method to add a button directly"""
        btn = ToolbarButton(text, icon=icon, colors=self._colors)
        if on_click:
            btn.clicked.connect(on_click)
        self._layout.insertWidget(self._layout.count() - 1, btn)
        return btn


class ToolbarGroup(QFrame):
    """Group of toolbar buttons"""

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.xs)

    def add_button(
        self,
        text: str = "",
        icon: str = None,
        active: bool = False,
        on_click=None
    ) -> "ToolbarButton":
        btn = ToolbarButton(text, icon=icon, active=active, colors=self._colors)
        if on_click:
            btn.clicked.connect(on_click)
        self._layout.addWidget(btn)
        return btn


class ToolbarButton(QPushButton):
    """Individual toolbar button"""

    def __init__(
        self,
        text: str = "",
        icon: str = None,
        active: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._active = active

        display_text = f"{icon} {text}" if icon and text else (icon or text)
        self.setText(display_text)

        self.setMinimumHeight(36)
        # If there's text, ensure button is wide enough
        if text:
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        else:
            self.setMinimumWidth(36)
            self.setMaximumWidth(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def setActive(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: 0 {SPACING.md}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: {RADIUS.md}px;
                    padding: 0 {SPACING.md}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.primary};
                }}
            """)


class StatusBar(QFrame):
    """
    Bottom status bar with status items.

    Usage:
        status_bar = StatusBar()
        status_bar.add_item("Ready")
        status_bar.add_item("Ln 42, Col 18", align="right")
        status_bar.set_item("status", "Saving...")
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._items = {}

        self.setFixedHeight(LAYOUT.statusbar_height)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.primary_dark};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        self._layout.setSpacing(SPACING.lg)

        # Left and right containers
        self._left = QHBoxLayout()
        self._left.setSpacing(SPACING.lg)
        self._right = QHBoxLayout()
        self._right.setSpacing(SPACING.lg)

        self._layout.addLayout(self._left)
        self._layout.addStretch()
        self._layout.addLayout(self._right)

    def add_item(self, text: str, key: str = None, icon: str = None, align: str = "left") -> QLabel:
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(SPACING.xs)

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: white; font-size: 14px;")
            container_layout.addWidget(icon_label)

        label = QLabel(text)
        label.setStyleSheet(f"""
            color: white;
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        container_layout.addWidget(label)

        if align == "right":
            self._right.addWidget(container)
        else:
            self._left.addWidget(container)

        if key:
            self._items[key] = label

        return label

    def set_item(self, key: str, text: str):
        if key in self._items:
            self._items[key].setText(text)


class Panel(QFrame):
    """
    Resizable content panel.

    Usage:
        panel = Panel("Codes", width=300)
        panel.set_content(code_tree)
    """

    def __init__(
        self,
        title: str = "",
        width: int = None,
        position: str = "left",  # left, center, right
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._position = position

        if width:
            self.setFixedWidth(width)

        border_side = "right" if position == "left" else "left" if position == "right" else "none"
        border_style = f"border-{border_side}: 1px solid {self._colors.border};" if border_side != "none" else ""

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                {border_style}
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header
        if title:
            self._header = PanelHeader(title, colors=self._colors)
            self._layout.addWidget(self._header)

        # Content container
        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.addWidget(self._content_container, 1)

    def set_content(self, widget: QWidget):
        # Clear existing
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._content_layout.addWidget(widget)

    def add_header_action(self, icon: str, on_click=None) -> QPushButton:
        if hasattr(self, '_header'):
            return self._header.add_action(icon, on_click)


class PanelHeader(QFrame):
    """Panel header with title and actions"""

    def __init__(self, title: str, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {self._colors.text_primary};
        """)
        self._layout.addWidget(title_label)
        self._layout.addStretch()

        # Actions container
        self._actions = QHBoxLayout()
        self._actions.setSpacing(SPACING.xs)
        self._layout.addLayout(self._actions)

    def add_action(self, icon: str, on_click=None) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: {RADIUS.sm}px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
                color: {self._colors.primary};
            }}
        """)
        if on_click:
            btn.clicked.connect(on_click)
        self._actions.addWidget(btn)
        return btn


class Sidebar(Panel):
    """
    Navigation sidebar (specialized Panel).

    Usage:
        sidebar = Sidebar(width=280)
        sidebar.add_section("Files")
        sidebar.add_item("Interview_01.txt", icon="📄")
    """

    item_clicked = pyqtSignal(str)

    def __init__(self, width: int = 280, colors: ColorPalette = None, parent=None):
        super().__init__(width=width, position="left", colors=colors, parent=parent)
        self._colors = colors or get_theme("dark")

        # Replace content layout
        self._items_layout = QVBoxLayout()
        self._items_layout.setSpacing(0)
        self._items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._content_layout.addLayout(self._items_layout)
        self._content_layout.addStretch()

    def add_section(self, title: str):
        label = QLabel(title)
        label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            text-transform: uppercase;
            padding: {SPACING.md}px {SPACING.sm}px {SPACING.xs}px;
        """)
        self._items_layout.addWidget(label)

    def add_item(self, text: str, icon: str = None, on_click=None) -> QPushButton:
        btn = QPushButton(f"{icon}  {text}" if icon else text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_primary};
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                text-align: left;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        if on_click:
            btn.clicked.connect(on_click)
        btn.clicked.connect(lambda: self.item_clicked.emit(text))
        self._items_layout.addWidget(btn)
        return btn


class MainContent(QSplitter):
    """
    Main content area with resizable panels.

    Usage:
        content = MainContent()
        content.add_panel(left_panel, "left")
        content.add_panel(center_panel, "center")
        content.add_panel(right_panel, "right")
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {self._colors.border};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
        """)

    def add_panel(self, widget: QWidget, position: str = "center"):
        self.addWidget(widget)
