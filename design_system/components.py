"""
Reusable UI components with refined styling.

Design principles:
- Consistent spacing and typography from tokens
- Accessible focus states
- Smooth hover transitions with animations
- Clear visual hierarchy
- Gradient backgrounds for visual depth
"""

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor
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

from .tokens import (
    ANIMATION,
    GRADIENTS,
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
    hex_to_rgba,
)


def _blend_color(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors together."""
    c1 = color1.lstrip("#")
    c2 = color2.lstrip("#")
    r = int(int(c1[0:2], 16) * (1 - ratio) + int(c2[0:2], 16) * ratio)
    g = int(int(c1[2:4], 16) * (1 - ratio) + int(c2[2:4], 16) * ratio)
    b = int(int(c1[4:6], 16) * (1 - ratio) + int(c2[4:6], 16) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


class Button(QPushButton):
    """
    Styled button with multiple variants, sizes, and animations.

    Features:
        - Gradient backgrounds for visual depth
        - Animated hover effects with shadow glow
        - Smooth transitions

    Variants:
        - primary: Main call-to-action (indigo gradient)
        - secondary: Less prominent action (subtle background)
        - outline: Border only, transparent background
        - ghost: No background or border
        - danger: Destructive actions (red gradient)
        - success: Positive actions (green gradient)
        - link: Text-only button styled as link
        - icon: Square button for icons only

    Sizes:
        - sm: Compact (28px height)
        - md: Default (36px height)
        - lg: Large (44px height)

    Usage:
        btn = Button("Save Changes", variant="primary")
        btn = Button("Cancel", variant="ghost", size="sm")
        btn = Button("Delete", variant="danger")
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        size: str = "md",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(text, parent)
        self._colors = colors or get_colors()
        self._variant = variant
        self._size = size
        self._shadow_effect = None
        self._shadow_animation = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_shadow()
        self._apply_style()

    def _setup_shadow(self):
        """Setup animated shadow for hover effects."""
        # Only add shadow animation to gradient buttons
        if self._variant in ("primary", "danger", "success", "secondary"):
            self._shadow_effect = QGraphicsDropShadowEffect(self)
            self._shadow_effect.setBlurRadius(0)
            self._shadow_effect.setXOffset(0)
            self._shadow_effect.setYOffset(2)

            # Set shadow color based on variant
            shadow_colors = {
                "primary": QColor(79, 70, 229, 0),  # Indigo
                "danger": QColor(239, 68, 68, 0),  # Red
                "success": QColor(16, 185, 129, 0),  # Green
                "secondary": QColor(0, 0, 0, 0),  # Neutral
            }
            self._shadow_color = shadow_colors.get(self._variant, QColor(0, 0, 0, 0))
            self._shadow_effect.setColor(self._shadow_color)
            self.setGraphicsEffect(self._shadow_effect)

    def _get_shadow_blur(self):
        return self._shadow_effect.blurRadius() if self._shadow_effect else 0

    def _set_shadow_blur(self, blur):
        if self._shadow_effect:
            self._shadow_effect.setBlurRadius(blur)
            # Also increase shadow opacity as blur increases
            alpha = min(int(blur * 6), 100)
            color = QColor(self._shadow_color)
            color.setAlpha(alpha)
            self._shadow_effect.setColor(color)

    shadow_blur = Property(float, _get_shadow_blur, _set_shadow_blur)

    def enterEvent(self, event):
        """Animate shadow on hover enter."""
        super().enterEvent(event)
        if self._shadow_effect and self._variant in ("primary", "danger", "success"):
            self._shadow_animation = QPropertyAnimation(self, b"shadow_blur")
            self._shadow_animation.setDuration(ANIMATION.duration_fast)
            self._shadow_animation.setStartValue(0)
            self._shadow_animation.setEndValue(16)
            self._shadow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._shadow_animation.start()

    def leaveEvent(self, event):
        """Animate shadow on hover leave."""
        super().leaveEvent(event)
        if self._shadow_effect and self._variant in ("primary", "danger", "success"):
            self._shadow_animation = QPropertyAnimation(self, b"shadow_blur")
            self._shadow_animation.setDuration(ANIMATION.duration_fast)
            self._shadow_animation.setStartValue(self._shadow_effect.blurRadius())
            self._shadow_animation.setEndValue(0)
            self._shadow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._shadow_animation.start()

    def _apply_style(self):
        # Size configurations: (v_pad, h_pad, font_size, min_height, min_width)
        sizes = {
            "xs": (SPACING.xs, SPACING.sm, TYPOGRAPHY.text_xs, 24, 48),
            "sm": (SPACING.xs, SPACING.md, TYPOGRAPHY.text_sm, 30, 56),
            "md": (SPACING.sm, SPACING.lg, TYPOGRAPHY.text_sm, 36, 64),
            "lg": (SPACING.sm + 2, SPACING.xl, TYPOGRAPHY.text_base, 44, 80),
        }
        v_pad, h_pad, font_size, min_height, min_width = sizes.get(
            self._size, sizes["md"]
        )

        # Special handling for link variant
        if self._variant == "link":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.primary};
                    border: none;
                    padding: 0;
                    font-size: {font_size}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                    min-height: 0;
                    min-width: 0;
                }}
                QPushButton:hover {{
                    color: {self._colors.primary_dark};
                    text-decoration: underline;
                }}
                QPushButton:disabled {{
                    color: {self._colors.text_disabled};
                }}
            """)
            return

        # Icon button: square with no min-width
        if self._variant == "icon":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {SPACING.sm}px;
                    min-width: {min_height}px;
                    max-width: {min_height}px;
                    min-height: {min_height}px;
                    max-height: {min_height}px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                    color: {self._colors.text_primary};
                }}
                QPushButton:pressed {{
                    background-color: {self._colors.surface_lighter};
                }}
                QPushButton:focus {{
                    border: 2px solid {self._colors.ring};
                }}
                QPushButton:disabled {{
                    color: {self._colors.text_disabled};
                }}
            """)
            return

        # Primary button with gradient
        if self._variant == "primary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {GRADIENTS.primary_button};
                    color: {self._colors.primary_foreground};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {v_pad}px {h_pad}px;
                    font-size: {font_size}px;
                    font-weight: {TYPOGRAPHY.weight_semibold};
                    min-height: {min_height}px;
                    min-width: {min_width}px;
                }}
                QPushButton:hover {{
                    background: {GRADIENTS.primary_button_hover};
                }}
                QPushButton:pressed {{
                    background: {GRADIENTS.primary_button_pressed};
                }}
                QPushButton:focus {{
                    border: 2px solid {self._colors.ring};
                    padding: {v_pad - 1}px {h_pad - 1}px;
                }}
                QPushButton:disabled {{
                    background: {self._colors.surface_lighter};
                    color: {self._colors.text_disabled};
                }}
            """)
            return

        # Danger button with gradient
        if self._variant == "danger":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {GRADIENTS.danger_button};
                    color: {self._colors.error_foreground};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {v_pad}px {h_pad}px;
                    font-size: {font_size}px;
                    font-weight: {TYPOGRAPHY.weight_semibold};
                    min-height: {min_height}px;
                    min-width: {min_width}px;
                }}
                QPushButton:hover {{
                    background: {GRADIENTS.danger_button_hover};
                }}
                QPushButton:pressed {{
                    background: {GRADIENTS.danger_button_pressed};
                }}
                QPushButton:focus {{
                    border: 2px solid {self._colors.error};
                    padding: {v_pad - 1}px {h_pad - 1}px;
                }}
                QPushButton:disabled {{
                    background: {self._colors.surface_lighter};
                    color: {self._colors.text_disabled};
                }}
            """)
            return

        # Success button with gradient
        if self._variant == "success":
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {GRADIENTS.success_button};
                    color: {self._colors.success_foreground};
                    border: none;
                    border-radius: {RADIUS.sm}px;
                    padding: {v_pad}px {h_pad}px;
                    font-size: {font_size}px;
                    font-weight: {TYPOGRAPHY.weight_semibold};
                    min-height: {min_height}px;
                    min-width: {min_width}px;
                }}
                QPushButton:hover {{
                    background: {GRADIENTS.success_button_hover};
                }}
                QPushButton:pressed {{
                    background: {self._colors.success};
                }}
                QPushButton:focus {{
                    border: 2px solid {self._colors.success};
                    padding: {v_pad - 1}px {h_pad - 1}px;
                }}
                QPushButton:disabled {{
                    background: {self._colors.surface_lighter};
                    color: {self._colors.text_disabled};
                }}
            """)
            return

        # Variant configurations: (bg, fg, border, hover_bg, pressed_bg, focus_ring)
        variants = {
            "secondary": (
                self._colors.surface_light,
                self._colors.text_primary,
                "none",
                self._colors.surface_lighter,
                self._colors.border,
                self._colors.ring,
            ),
            "outline": (
                "transparent",
                self._colors.text_primary,
                f"1px solid {self._colors.border}",
                self._colors.surface_light,
                self._colors.surface_lighter,
                self._colors.ring,
            ),
            "ghost": (
                "transparent",
                self._colors.text_primary,
                "none",
                self._colors.surface_light,
                self._colors.surface_lighter,
                self._colors.ring,
            ),
        }

        config = variants.get(self._variant, variants["secondary"])
        bg, fg, border, hover_bg, pressed_bg, focus_ring = config

        # Standard button styling for secondary/outline/ghost
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: {border};
                border-radius: {RADIUS.sm}px;
                padding: {v_pad}px {h_pad}px;
                font-size: {font_size}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                min-height: {min_height}px;
                min-width: {min_width}px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}
            QPushButton:focus {{
                border: 2px solid {focus_ring};
                padding: {v_pad - 1}px {h_pad - 1}px;
            }}
            QPushButton:disabled {{
                background-color: {self._colors.surface_lighter};
                color: {self._colors.text_disabled};
                border: none;
            }}
        """)


class Input(QLineEdit):
    """
    Styled text input with validation support.

    Features:
        - Hover and focus states
        - Error state with visual feedback
        - Placeholder text styling
        - Accessible focus ring

    Usage:
        inp = Input(placeholder="Enter your name")
        inp.set_error(True)  # Show error state
    """

    def __init__(self, placeholder: str = "", colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self.setPlaceholderText(placeholder)
        self._error = False
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_base}px;
                min-height: 36px;
                selection-background-color: {self._colors.primary};
                selection-color: {self._colors.primary_foreground};
            }}
            QLineEdit:hover {{
                border-color: {self._colors.text_disabled};
            }}
            QLineEdit:focus {{
                border: 2px solid {self._colors.primary};
                padding: {SPACING.sm - 1}px {SPACING.md - 1}px;
            }}
            QLineEdit:disabled {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_disabled};
                border-color: {self._colors.border_light};
            }}
            QLineEdit::placeholder {{
                color: {self._colors.text_hint};
            }}
            QLineEdit[error="true"] {{
                border: 2px solid {self._colors.error};
                padding: {SPACING.sm - 1}px {SPACING.md - 1}px;
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

    def __init__(
        self,
        colors: ColorPalette = None,
        parent=None,
        shadow: bool = True,
        elevation: int = 1,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
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
                1: (4, 2, 30),  # blur, offset, opacity
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
        parent=None,
    ):
        super().__init__(text, parent)
        colors = colors or get_colors()

        variants = {
            "default": (colors.primary, colors.primary_foreground),
            "secondary": (colors.surface_light, colors.text_primary),
            "outline": ("transparent", colors.text_primary, colors.border),
            "destructive": (hex_to_rgba(colors.error, 0.2), colors.error),
            "success": (hex_to_rgba(colors.success, 0.2), colors.success),
            "warning": (hex_to_rgba(colors.warning, 0.2), colors.warning),
            "info": (hex_to_rgba(colors.info, 0.2), colors.info),
            "primary": (hex_to_rgba(colors.primary, 0.2), colors.primary),
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

    def __init__(
        self, orientation: str = "horizontal", colors: ColorPalette = None, parent=None
    ):
        super().__init__(parent)
        colors = colors or get_colors()

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
        parent=None,
    ):
        super().__init__(parent)
        colors = colors or get_colors()

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
        self, text: str = "", size: int = 40, colors: ColorPalette = None, parent=None
    ):
        super().__init__(text, parent)
        colors = colors or get_colors()

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
        parent=None,
    ):
        super().__init__(parent)
        colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            SPACING.md,
            SPACING.sm,
            SPACING.md if not closable else SPACING.sm,
            SPACING.sm,
        )
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
    File type icon with colored background and icon.

    Displays an icon representing the file type with a colored background.
    Uses qtawesome icons by default, or custom icon_text if provided.
    """

    # Default icons for each file type
    DEFAULT_ICONS = {
        "text": "mdi6.file-document-outline",
        "audio": "mdi6.music-note",
        "video": "mdi6.video-outline",
        "image": "mdi6.image-outline",
        "pdf": "mdi6.file-pdf-box",
    }

    def __init__(
        self,
        file_type: str = "text",
        icon_text: str = "",
        size: int = 36,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        colors = colors or get_colors()
        self._file_type = file_type

        type_colors = {
            "text": (colors.file_text, hex_to_rgba(colors.file_text, 0.15)),
            "audio": (colors.file_audio, hex_to_rgba(colors.file_audio, 0.15)),
            "video": (colors.file_video, hex_to_rgba(colors.file_video, 0.15)),
            "image": (colors.file_image, hex_to_rgba(colors.file_image, 0.15)),
            "pdf": (colors.file_pdf, hex_to_rgba(colors.file_pdf, 0.15)),
        }

        fg, bg = type_colors.get(file_type, type_colors["text"])
        self._fg_color = fg

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

        # Use qtawesome icon by default, or custom text if provided
        if icon_text:
            label = QLabel(icon_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                color: {fg};
                font-size: {size // 2}px;
                background: transparent;
            """)
            layout.addWidget(label)
        else:
            # Use qtawesome icon
            try:
                import qtawesome as qta

                icon_name = self.DEFAULT_ICONS.get(file_type, "mdi6.file-outline")
                icon_size = int(size * 0.55)
                icon_label = QLabel()
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                icon_label.setPixmap(
                    qta.icon(icon_name, color=fg).pixmap(icon_size, icon_size)
                )
                icon_label.setStyleSheet("background: transparent;")
                layout.addWidget(icon_label)
            except ImportError:
                # Fallback to text abbreviation if qtawesome not available
                abbrevs = {
                    "text": "TXT",
                    "audio": "MP3",
                    "video": "VID",
                    "image": "IMG",
                    "pdf": "PDF",
                }
                label = QLabel(abbrevs.get(file_type, "?"))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet(f"""
                    color: {fg};
                    font-size: {size // 3}px;
                    font-weight: bold;
                    background: transparent;
                """)
                layout.addWidget(label)
