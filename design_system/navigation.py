"""
Navigation components
Menu items, tabs, and navigation elements
"""

from typing import List, Optional

import qtawesome as qta

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_colors, hex_to_rgba


class MenuItem(QPushButton):
    """
    Individual menu item.

    Usage:
        item = MenuItem("File", shortcut="Ctrl+F")
        item.clicked.connect(self.show_file_menu)
    """

    def __init__(
        self,
        text: str,
        icon: str = None,
        shortcut: str = None,
        active: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._active = active
        self._icon_name = icon

        if icon and icon.startswith("mdi6."):
            self.setIcon(qta.icon(icon, color=self._colors.text_secondary))
            self.setText(text)
        else:
            display = f"{icon}  {text}" if icon else text
            self.setText(display)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

        if shortcut:
            self.setShortcut(shortcut)

    def setActive(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.primary};
                    border: none;
                    border-radius: {RADIUS.xs}px;
                    padding: {SPACING.sm}px {SPACING.lg}px;
                    font-size: {TYPOGRAPHY.text_sm}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
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


class Tab(QPushButton):
    """
    Individual tab item.

    Usage:
        tab = Tab("Coding", icon="mdi6.tag", active=True)
    """

    def __init__(
        self,
        text: str,
        icon: str = None,
        active: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._active = active
        self._icon_name = icon

        if icon and icon.startswith("mdi6."):
            self.setIcon(qta.icon(icon, color=self._colors.primary if active else self._colors.text_secondary))
            self.setText(text)
        else:
            display = f"{icon}  {text}" if icon else text
            self.setText(display)

        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def setActive(self, active: bool):
        self._active = active
        self._apply_style()

    def isActive(self) -> bool:
        return self._active

    def _apply_style(self):
        # Update icon color if using mdi6 icon
        if hasattr(self, '_icon_name') and self._icon_name and self._icon_name.startswith("mdi6."):
            icon_color = self._colors.primary if self._active else self._colors.text_secondary
            self.setIcon(qta.icon(self._icon_name, color=icon_color))

        if self._active:
            self.setStyleSheet(f"""
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
            self.setStyleSheet(f"""
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


class TabGroup(QFrame):
    """
    Group of tabs with exclusive selection.

    Usage:
        tabs = TabGroup()
        tabs.add_tab("Coding", icon="mdi6.tag")
        tabs.add_tab("Reports", icon="mdi6.chart-bar")
        tabs.tab_changed.connect(self.on_tab_change)
    """

    tab_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._tabs = []
        self._active = None

        # Ensure minimum height for tabs to be visible
        self.setMinimumHeight(40)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def add_tab(self, text: str, icon: str = None, active: bool = False) -> Tab:
        tab = Tab(text, icon=icon, active=active, colors=self._colors)
        tab.clicked.connect(lambda: self._on_tab_click(text))
        self._tabs.append((text, tab))
        self._layout.addWidget(tab)

        if active or len(self._tabs) == 1:
            self._set_active(text)

        return tab

    def _on_tab_click(self, text: str):
        self._set_active(text)
        self.tab_changed.emit(text)

    def _set_active(self, text: str):
        self._active = text
        for name, tab in self._tabs:
            tab.setActive(name == text)

    def active_tab(self) -> Optional[str]:
        return self._active


class Breadcrumb(QFrame):
    """
    Breadcrumb navigation.

    Usage:
        breadcrumb = Breadcrumb()
        breadcrumb.set_path(["Home", "Projects", "QualCoder"])
        breadcrumb.item_clicked.connect(self.navigate_to)
    """

    item_clicked = Signal(str, int)  # text, index

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._items = []

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.xs)

    def set_path(self, items: List[str]):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._items = items

        for i, text in enumerate(items):
            is_last = i == len(items) - 1

            # Add separator except for first item
            if i > 0:
                sep = QLabel("/")
                sep.setStyleSheet(f"color: {self._colors.text_disabled}; font-size: {TYPOGRAPHY.text_sm}px;")
                self._layout.addWidget(sep)

            # Add item
            if is_last:
                label = QLabel(text)
                label.setStyleSheet(f"color: {self._colors.text_primary}; font-size: {TYPOGRAPHY.text_sm}px;")
                self._layout.addWidget(label)
            else:
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {self._colors.text_secondary};
                        border: none;
                        font-size: {TYPOGRAPHY.text_sm}px;
                        padding: 0;
                    }}
                    QPushButton:hover {{
                        color: {self._colors.primary};
                        text-decoration: underline;
                    }}
                """)
                idx = i
                btn.clicked.connect(lambda checked, t=text, idx=idx: self.item_clicked.emit(t, idx))
                self._layout.addWidget(btn)

        self._layout.addStretch()


class NavList(QScrollArea):
    """
    Vertical navigation list.

    Usage:
        nav = NavList()
        nav.add_section("Main")
        nav.add_item("Dashboard", icon="mdi6.view-dashboard", active=True)
        nav.add_item("Settings", icon="mdi6.cog")
        nav.item_clicked.connect(self.navigate)
    """

    item_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._items = []
        self._active = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        self._layout.setSpacing(SPACING.xs)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(container)

    def add_section(self, title: str):
        label = QLabel(title)
        label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            text-transform: uppercase;
            padding: {SPACING.md}px {SPACING.sm}px {SPACING.xs}px;
        """)
        self._layout.addWidget(label)

    def add_item(
        self,
        text: str,
        icon: str = None,
        active: bool = False,
        on_click=None
    ) -> QPushButton:
        btn = QPushButton()
        if icon and icon.startswith("mdi6."):
            btn.setIcon(qta.icon(icon, color=self._colors.primary if active else self._colors.text_primary))
            btn.setText(text)
        else:
            btn.setText(f"{icon}  {text}" if icon else text)
        btn.setProperty("nav_item", text)
        btn.setProperty("icon_name", icon)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self._items.append(btn)

        def handle_click():
            self._set_active(text)
            if on_click:
                on_click()
            self.item_clicked.emit(text)

        btn.clicked.connect(handle_click)
        self._layout.addWidget(btn)

        if active:
            self._set_active(text)
        else:
            self._style_item(btn, False)

        return btn

    def _set_active(self, text: str):
        self._active = text
        for btn in self._items:
            is_active = btn.property("nav_item") == text
            self._style_item(btn, is_active)

    def _style_item(self, btn: QPushButton, active: bool):
        # Update icon color if using mdi6 icon
        icon_name = btn.property("icon_name")
        if icon_name and icon_name.startswith("mdi6."):
            icon_color = self._colors.primary if active else self._colors.text_primary
            btn.setIcon(qta.icon(icon_name, color=icon_color))

        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_to_rgba(self._colors.primary, 0.10)};
                    color: {self._colors.primary};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {SPACING.sm}px {SPACING.md}px;
                    text-align: left;
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
            """)
        else:
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


class StepIndicator(QFrame):
    """
    Step/wizard progress indicator.

    Usage:
        steps = StepIndicator(["Select Files", "Configure", "Process", "Review"])
        steps.set_current(1)  # "Configure" is active
    """

    step_clicked = Signal(int)

    def __init__(
        self,
        steps: List[str],
        current: int = 0,
        clickable: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._steps = steps
        self._current = current
        self._clickable = clickable
        self._step_widgets = []

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._build_steps()

    def _build_steps(self):
        for i, step in enumerate(self._steps):
            # Step circle and label
            step_widget = self._create_step(i, step)
            self._step_widgets.append(step_widget)
            self._layout.addWidget(step_widget)

            # Connector line (except after last step)
            if i < len(self._steps) - 1:
                line = QFrame()
                line.setFixedHeight(2)
                line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                completed = i < self._current
                line.setStyleSheet(f"""
                    background-color: {self._colors.primary if completed else self._colors.border};
                """)
                self._layout.addWidget(line)

    def _create_step(self, index: int, text: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Circle
        is_completed = index < self._current
        is_current = index == self._current

        circle = QPushButton()
        if is_completed:
            circle.setIcon(qta.icon("mdi6.check", color="white"))
        else:
            circle.setText(str(index + 1))
        circle.setFixedSize(32, 32)

        if self._clickable and index <= self._current:
            circle.setCursor(Qt.CursorShape.PointingHandCursor)
            circle.clicked.connect(lambda checked, i=index: self.step_clicked.emit(i))

        if is_completed:
            circle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    border: none;
                    border-radius: 16px;
                }}
            """)
        elif is_current:
            circle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors.primary};
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-weight: bold;
                }}
            """)
        else:
            circle.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: 2px solid {self._colors.border};
                    border-radius: 16px;
                }}
            """)

        layout.addWidget(circle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {self._colors.text_primary if is_current else self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium if is_current else TYPOGRAPHY.weight_normal};
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        return container

    def set_current(self, index: int):
        self._current = index
        # Rebuild to update styles
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._step_widgets = []
        self._build_steps()

    def current_step(self) -> int:
        return self._current


class MediaTypeSelector(QFrame):
    """
    Tab-style selector for media types (Text, Image, A/V, PDF).

    Used in coding toolbar to switch between different media coding modes.

    Usage:
        selector = MediaTypeSelector(
            options=[
                ("text", "Text", "mdi6.file-document"),
                ("image", "Image", "mdi6.image"),
                ("av", "A/V", "mdi6.video"),
                ("pdf", "PDF", "mdi6.file-pdf-box"),
            ],
            selected="text",
        )
        selector.selection_changed.connect(on_media_type_changed)
    """

    selection_changed = Signal(str)  # option_id

    def __init__(
        self,
        options: List[tuple],  # [(id, label, icon), ...]
        selected: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._options = options
        self._selected = selected or (options[0][0] if options else None)
        self._buttons = {}

        self.setStyleSheet(f"""
            MediaTypeSelector {{
                background-color: transparent;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for option_id, label, icon_name in options:
            btn = self._create_button(option_id, label, icon_name)
            self._buttons[option_id] = btn
            layout.addWidget(btn)

        self._update_styles()

    def _create_button(self, option_id: str, label: str, icon_name: str) -> QFrame:
        """Create a media type button"""
        btn = QFrame()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("option_id", option_id)

        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        btn_layout.setSpacing(SPACING.xs)

        from .icons import Icon
        icon = Icon(icon_name, size=16, colors=self._colors)
        btn_layout.addWidget(icon)
        btn._icon = icon

        text = QLabel(label)
        btn_layout.addWidget(text)
        btn._label = text

        btn.mousePressEvent = lambda e, oid=option_id: self._on_click(oid)

        return btn

    def _on_click(self, option_id: str):
        if option_id != self._selected:
            self._selected = option_id
            self._update_styles()
            self.selection_changed.emit(option_id)

    def _update_styles(self):
        """Update button styles based on selection"""
        for option_id, btn in self._buttons.items():
            is_selected = option_id == self._selected

            if is_selected:
                btn.setStyleSheet(f"""
                    QFrame {{
                        background-color: {hex_to_rgba(self._colors.primary, 0.10)};
                        border: 1px solid {self._colors.primary};
                        border-radius: {RADIUS.sm}px;
                    }}
                """)
                btn._icon.set_color(self._colors.primary)
                btn._label.setStyleSheet(f"""
                    color: {self._colors.primary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                """)
            else:
                btn.setStyleSheet(f"""
                    QFrame {{
                        background-color: transparent;
                        border: 1px solid transparent;
                        border-radius: {RADIUS.sm}px;
                    }}
                    QFrame:hover {{
                        background-color: {self._colors.surface_light};
                    }}
                """)
                btn._icon.set_color(self._colors.text_secondary)
                btn._label.setStyleSheet(f"""
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                """)

    def set_selected(self, option_id: str):
        """Programmatically select an option"""
        if option_id in self._buttons and option_id != self._selected:
            self._selected = option_id
            self._update_styles()

    def selected(self) -> str:
        """Get currently selected option id"""
        return self._selected
