"""
Context menu components
Material Design styled right-click menus
"""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors


class ContextMenu(QMenu):
    """
    Styled context menu with Material Design appearance.

    Usage:
        menu = ContextMenu()
        menu.add_item("Edit", icon="edit", on_click=self.edit)
        menu.add_item("Delete", icon="delete", variant="danger", on_click=self.delete)
        menu.add_separator()
        menu.add_submenu("Move to", submenu)
        menu.exec(QCursor.pos())
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QMenu {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px 0;
            }}
            QMenu::item {{
                padding: {SPACING.sm + 2}px {SPACING.lg}px;
                color: {self._colors.text_primary};
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: {self._colors.surface_light};
            }}
            QMenu::item:disabled {{
                color: {self._colors.text_disabled};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {self._colors.border};
                margin: {SPACING.sm}px 0;
            }}
            QMenu::indicator {{
                width: 18px;
                height: 18px;
                margin-left: {SPACING.sm}px;
            }}
        """)

    def add_item(
        self,
        text: str,
        icon: str = None,
        shortcut: str = None,
        variant: str = "default",
        on_click=None,
        enabled: bool = True,
    ) -> QAction:
        """
        Add a menu item.

        Args:
            text: Menu item text
            icon: Optional icon character/text
            shortcut: Optional keyboard shortcut
            variant: "default" or "danger"
            on_click: Click handler
            enabled: Whether item is enabled
        """
        action = ContextMenuItem(
            text,
            icon=icon,
            shortcut=shortcut,
            variant=variant,
            colors=self._colors,
            parent=self,
        )

        if on_click:
            action.triggered.connect(on_click)

        action.setEnabled(enabled)
        self.addAction(action)
        return action

    def add_separator(self):
        """Add a separator line"""
        self.addSeparator()

    def add_submenu(self, text: str, submenu: "ContextMenu" = None) -> "ContextMenu":
        """Add a submenu"""
        if submenu is None:
            submenu = ContextMenu(colors=self._colors, parent=self)

        submenu.setTitle(text)
        self.addMenu(submenu)
        return submenu


class ContextMenuItem(QAction):
    """
    Styled context menu item.
    """

    def __init__(
        self,
        text: str,
        icon: str = None,
        shortcut: str = None,
        variant: str = "default",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._variant = variant

        # Build display text with icon
        display_text = text
        if icon:
            display_text = f"  {text}"  # Space for icon placement

        self.setText(display_text)

        if shortcut:
            self.setShortcut(shortcut)

        # Store icon for custom rendering if needed
        self._icon_text = icon


class ContextMenuWidget(QFrame):
    """
    Custom widget-based context menu for more control over styling.
    Use this when you need more complex menu items.

    Usage:
        menu = ContextMenuWidget()
        menu.add_item("Edit", icon="✎", on_click=self.edit)
        menu.add_separator()
        menu.add_item("Delete", icon="🗑", variant="danger")
        menu.show_at(QCursor.pos())
    """

    item_clicked = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, SPACING.sm, 0, SPACING.sm)
        self._layout.setSpacing(0)

    def add_item(
        self, text: str, icon: str = None, variant: str = "default", on_click=None
    ) -> QWidget:
        """Add a menu item widget"""
        item = ContextMenuItemWidget(
            text, icon=icon, variant=variant, colors=self._colors
        )

        def handle_click():
            if on_click:
                on_click()
            self.item_clicked.emit(text)
            self.close()

        item.clicked.connect(handle_click)
        self._layout.addWidget(item)
        return item

    def add_separator(self):
        """Add a separator line"""
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self._colors.border};")
        separator.setContentsMargins(0, SPACING.sm, 0, SPACING.sm)
        self._layout.addWidget(separator)

    def show_at(self, pos):
        """Show menu at specified position"""
        self.adjustSize()
        self.move(pos)
        self.show()


class ContextMenuItemWidget(QFrame):
    """Widget for custom context menu item"""

    clicked = Signal()

    def __init__(
        self,
        text: str,
        icon: str = None,
        variant: str = "default",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._variant = variant

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        text_color = (
            self._colors.error if variant == "danger" else self._colors.text_primary
        )
        icon_color = (
            self._colors.error if variant == "danger" else self._colors.text_secondary
        )

        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                padding: {SPACING.sm + 2}px {SPACING.lg}px;
            }}
            QFrame:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            SPACING.lg, SPACING.sm + 2, SPACING.lg, SPACING.sm + 2
        )
        layout.setSpacing(SPACING.md)

        # Icon - support both mdi6 icons and emoji fallback
        if icon:
            icon_label = QLabel()
            if icon.startswith("mdi6."):
                icon_label.setPixmap(qta.icon(icon, color=icon_color).pixmap(18, 18))
            else:
                icon_label.setText(icon)
                icon_label.setStyleSheet(f"""
                    color: {icon_color};
                    font-size: 18px;
                """)
            icon_label.setFixedWidth(24)
            layout.addWidget(icon_label)

        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            color: {text_color};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(text_label, 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
