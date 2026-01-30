"""
Reusable UI components with Material Design styling
Based on mockups/css/material-theme.css
"""

from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class Button(QPushButton):
    """
    Styled button with variants: primary, secondary, outline, ghost, danger, success, icon

    Usage:
        btn = Button("Click me", variant="primary")
        btn = Button("Cancel", variant="secondary", size="sm")
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        size: str = "md",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(text, parent)
        self._colors = colors or get_theme("dark")
        self._variant = variant
        self._size = size
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        # Size configurations
        sizes = {
            "sm": (SPACING.xs, SPACING.md, TYPOGRAPHY.text_sm, 28),
            "md": (SPACING.sm, SPACING.lg, TYPOGRAPHY.text_sm, 36),
            "lg": (SPACING.sm + 2, SPACING.xl, TYPOGRAPHY.text_base, 44),
        }
        v_pad, h_pad, font_size, min_height = sizes.get(self._size, sizes["md"])

        # Variant configurations: (bg, fg, border, hover_bg)
        variants = {
            "primary": (
                self._colors.primary,
                self._colors.primary_foreground,
                "none",
                self._colors.primary_light
            ),
            "secondary": (
                self._colors.surface_light,
                self._colors.text_primary,
                "none",
                self._colors.surface_lighter
            ),
            "outline": (
                "transparent",
                self._colors.text_primary,
                f"1px solid {self._colors.border}",
                self._colors.surface_light
            ),
            "ghost": (
                "transparent",
                self._colors.text_secondary,
                "none",
                self._colors.surface_light
            ),
            "danger": (
                self._colors.error,
                self._colors.error_foreground,
                "none",
                self._colors.error_light if hasattr(self._colors, 'error_light') else "#ff6659"
            ),
            "success": (
                self._colors.success,
                self._colors.success_foreground,
                "none",
                self._colors.success_light if hasattr(self._colors, 'success_light') else "#66bb6a"
            ),
        }

        bg, fg, border, hover_bg = variants.get(self._variant, variants["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: {border};
                border-radius: {RADIUS.md}px;
                padding: {v_pad}px {h_pad}px;
                font-size: {font_size}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                min-height: {min_height}px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:pressed {{
                background-color: {hover_bg};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: {self._colors.surface_lighter};
                color: {self._colors.text_disabled};
            }}
        """)


class Input(QLineEdit):
    """
    Styled text input with validation support
    """

    def __init__(self, placeholder: str = "", colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self.setPlaceholderText(placeholder)
        self._error = False
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_base}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
            QLineEdit::placeholder {{
                color: {self._colors.text_hint};
            }}
            QLineEdit[error="true"] {{
                border-color: {self._colors.error};
            }}
        """)

    def set_error(self, error: bool):
        """Set error state for validation"""
        self._error = error
        self.setProperty("error", "true" if error else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def is_error(self) -> bool:
        return self._error


class Label(QLabel):
    """
    Styled label with variants: default, muted, secondary, title, description, hint, error
    """

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        super().__init__(text, parent)
        if variant != "default":
            self.setProperty("variant", variant)


class Card(QFrame):
    """
    Card container with optional shadow (Material Design elevation)
    """

    def __init__(self, colors: ColorPalette = None, parent=None, shadow: bool = True, elevation: int = 1):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self.setProperty("variant", "card")

        # Apply theme-aware styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        if shadow:
            self._shadow_effect = QGraphicsDropShadowEffect(self)
            # Material Design shadow levels
            shadows = {
                1: (4, 2, 30),   # blur, offset, opacity
                2: (8, 4, 30),
                3: (16, 8, 30),
                4: (24, 12, 40),
            }
            blur, offset, opacity = shadows.get(elevation, shadows[1])
            self._shadow_effect.setBlurRadius(blur)
            self._shadow_effect.setXOffset(0)
            self._shadow_effect.setYOffset(offset)
            self._shadow_effect.setColor(QColor(0, 0, 0, opacity))
            self.setGraphicsEffect(self._shadow_effect)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        self._layout.setSpacing(SPACING.md)

    def add_widget(self, widget: QWidget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)


class CardHeader(QWidget):
    """Card header section with title and description"""

    def __init__(self, title: str = "", description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        if title:
            self.title_label = Label(title, "title")
            layout.addWidget(self.title_label)

        if description:
            self.desc_label = Label(description, "description")
            layout.addWidget(self.desc_label)


class Badge(QLabel):
    """
    Small badge/tag component with Material Design colors
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "default",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(text, parent)
        colors = colors or get_theme("dark")

        variants = {
            "default": (colors.primary, colors.primary_foreground),
            "secondary": (colors.surface_light, colors.text_primary),
            "outline": ("transparent", colors.text_primary, colors.border),
            "destructive": (f"rgba(244, 67, 54, 0.2)", colors.error),
            "success": (f"rgba(76, 175, 80, 0.2)", colors.success),
            "warning": (f"rgba(255, 152, 0, 0.2)", colors.warning),
            "info": (f"rgba(33, 150, 243, 0.2)", colors.info),
            "primary": (f"rgba(0, 150, 136, 0.2)", colors.primary),
        }

        result = variants.get(variant, variants["default"])
        if len(result) == 3:
            bg, fg, border = result
            border_style = f"border: 1px solid {border};"
        else:
            bg, fg = result
            border_style = "border: none;"

        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            {border_style}
            border-radius: 12px;
            padding: {SPACING.xs}px {SPACING.sm + 2}px;
            font-size: {TYPOGRAPHY.text_xs + 1}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)


class Separator(QFrame):
    """Horizontal or vertical separator line"""

    def __init__(self, orientation: str = "horizontal", colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        colors = colors or get_theme("dark")

        if orientation == "horizontal":
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(1)

        self.setStyleSheet(f"background-color: {colors.border}; border: none;")


class Alert(QFrame):
    """
    Alert/callout component with variants: default, destructive, success, warning, info
    """

    def __init__(
        self,
        title: str = "",
        description: str = "",
        variant: str = "default",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        colors = colors or get_theme("dark")

        variants = {
            "default": (colors.surface, colors.text_primary, colors.border),
            "destructive": (colors.surface, colors.error, colors.error),
            "success": (colors.surface, colors.success, colors.success),
            "warning": (colors.surface, colors.warning, colors.warning),
            "info": (colors.surface, colors.info, colors.info),
        }

        bg, fg, border = variants.get(variant, variants["default"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-left: 4px solid {border};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.xs)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                color: {fg};
                font-weight: {TYPOGRAPHY.weight_medium};
                font-size: {TYPOGRAPHY.text_base}px;
                background: transparent;
                border: none;
            """)
            layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"""
                color: {colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
                background: transparent;
                border: none;
            """)
            layout.addWidget(desc_label)


class Avatar(QLabel):
    """Circular avatar component"""

    def __init__(
        self,
        text: str = "",
        size: int = 40,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(text, parent)
        colors = colors or get_theme("dark")

        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            background-color: {colors.surface_lighter};
            color: {colors.text_primary};
            border-radius: {size // 2}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            font-size: {size // 3}px;
        """)


class Chip(QFrame):
    """
    Chip/tag component with optional close button
    """

    close_clicked = Signal()

    def __init__(
        self,
        text: str = "",
        closable: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md if not closable else SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        label = QLabel(text)
        label.setStyleSheet(f"color: {colors.text_primary}; background: transparent;")
        layout.addWidget(label)

        if closable:
            close_btn = QPushButton("×")
            close_btn.setFixedSize(20, 20)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors.text_secondary};
                    border: none;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors.surface_lighter};
                }}
            """)
            close_btn.clicked.connect(self.close_clicked.emit)
            layout.addWidget(close_btn)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.surface_light};
                border-radius: 16px;
            }}
        """)


class FileIcon(QFrame):
    """
    File type icon with colored background
    """

    def __init__(
        self,
        file_type: str = "text",
        icon_text: str = "",
        size: int = 36,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        colors = colors or get_theme("dark")

        type_colors = {
            "text": (colors.file_text, "rgba(33, 150, 243, 0.15)"),
            "audio": (colors.file_audio, "rgba(156, 39, 176, 0.15)"),
            "video": (colors.file_video, "rgba(244, 67, 54, 0.15)"),
            "image": (colors.file_image, "rgba(76, 175, 80, 0.15)"),
            "pdf": (colors.file_pdf, "rgba(255, 87, 34, 0.15)"),
        }

        fg, bg = type_colors.get(file_type, type_colors["text"])

        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: {RADIUS.md}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon_text:
            label = QLabel(icon_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                color: {fg};
                font-size: {size // 2}px;
                background: transparent;
            """)
            layout.addWidget(label)
