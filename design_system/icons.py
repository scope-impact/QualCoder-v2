"""
Material Icons support for PySide6 using qtawesome.

This design system uses qtawesome for all icons. Use Material Design Icons 6
with the 'mdi6.' prefix.

Browse available icons: https://pictogrammers.com/library/mdi/

Usage:
    from design_system import Icon

    # Use any mdi6 icon name (color defaults to theme's text_secondary)
    icon = Icon("mdi6.folder", size=20)
    layout.addWidget(icon)

    # Or specify color from theme
    icon = Icon("mdi6.folder", size=20, color=colors.primary)

    # Common icons:
    # mdi6.folder, mdi6.file-document, mdi6.code-tags
    # mdi6.magnify, mdi6.cog, mdi6.plus, mdi6.close
    # mdi6.check, mdi6.alert, mdi6.information
"""

import qtawesome as qta

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt

from .tokens import ColorPalette, get_colors


class Icon(QLabel):
    """
    Icon widget using qtawesome.

    Args:
        name: qtawesome icon name (e.g., "mdi6.folder", "mdi6.code-tags")
        size: Icon size in pixels (default 20)
        color: Icon color (default from theme)
        colors: ColorPalette for theming

    Usage:
        icon = Icon("mdi6.code-tags", size=24, color=colors.primary)
        icon = Icon("mdi6.folder")  # Uses default size and theme color
    """

    def __init__(
        self,
        name: str,
        size: int = 20,
        color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._name = name
        self._size = size
        self._color = color or self._colors.text_secondary

        self._setup_icon()

    def _setup_icon(self):
        """Setup the icon display"""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(self._size + 4, self._size + 4)

        try:
            icon = qta.icon(self._name, color=self._color)
            pixmap = icon.pixmap(self._size, self._size)
            self.setPixmap(pixmap)
        except Exception as e:
            # Show icon name as text if icon not found
            self.setText(self._name.split(".")[-1][:3])
            font = self.font()
            font.setPixelSize(max(8, self._size - 8))
            self.setFont(font)

        self.setStyleSheet("QLabel { background: transparent; }")

    def set_color(self, color: str):
        """Update icon color"""
        self._color = color
        try:
            icon = qta.icon(self._name, color=self._color)
            pixmap = icon.pixmap(self._size, self._size)
            self.setPixmap(pixmap)
        except Exception:
            self.setStyleSheet(f"QLabel {{ color: {self._color}; background: transparent; }}")

    def set_size(self, size: int):
        """Update icon size"""
        self._size = size
        self._setup_icon()

    @property
    def name(self) -> str:
        """Get the icon name"""
        return self._name


class IconText(QWidget):
    """
    Icon with text label side by side.

    Args:
        icon: qtawesome icon name (e.g., "mdi6.folder")
        text: Label text
        icon_size: Icon size in pixels
        spacing: Space between icon and text
        color: Color for both icon and text
        colors: ColorPalette for theming

    Usage:
        item = IconText("mdi6.folder", "Documents", icon_size=18)
    """

    def __init__(
        self,
        icon: str,
        text: str,
        icon_size: int = 18,
        spacing: int = 8,
        color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._color = color or self._colors.text_primary

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)

        self._icon = Icon(icon, size=icon_size, color=self._color, colors=self._colors)
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        self._label.setStyleSheet(f"color: {self._color};")
        layout.addWidget(self._label)

        layout.addStretch()

    def set_color(self, color: str):
        """Update color for both icon and text"""
        self._color = color
        self._icon.set_color(color)
        self._label.setStyleSheet(f"color: {color};")

    def set_text(self, text: str):
        """Update label text"""
        self._label.setText(text)


def icon(name: str, size: int = 20, color: str = None, colors: ColorPalette = None) -> Icon:
    """Create an Icon widget"""
    return Icon(name, size=size, color=color, colors=colors)


def get_pixmap(name: str, size: int = 20, color: str = None, colors: ColorPalette = None):
    """Get a QPixmap for an icon (useful for buttons, etc.)"""
    colors = colors or get_colors()
    color = color or colors.text_secondary
    return qta.icon(name, color=color).pixmap(size, size)


def get_qicon(name: str, color: str = None, colors: ColorPalette = None):
    """Get a QIcon for use with Qt widgets that accept QIcon"""
    colors = colors or get_colors()
    color = color or colors.text_secondary
    return qta.icon(name, color=color)
