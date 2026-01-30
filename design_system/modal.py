"""
Modal/Dialog components
Material Design styled modal dialogs
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .tokens import RADIUS, SPACING, TYPOGRAPHY, ColorPalette, get_colors


class Modal(QDialog):
    """
    Modal dialog with header, body, and footer sections.

    Usage:
        modal = Modal(title="Confirm Action", parent=self)
        modal.body.addWidget(QLabel("Are you sure?"))
        modal.add_button("Cancel", "secondary")
        modal.add_button("Delete", "destructive", on_click=self.delete_item)
        modal.exec()
    """

    def __init__(
        self,
        title: str = "",
        size: str = "default",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        # Dialog settings
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # Size presets
        sizes = {
            "sm": 400,
            "default": 500,
            "lg": 700,
            "xl": 900,
        }
        self._width = sizes.get(size, sizes["default"])

        self._setup_ui(title)

    def _setup_ui(self, title: str):
        # Main layout with overlay effect
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Modal container
        self._container = QFrame()
        self._container.setFixedWidth(self._width)
        self._container.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(0, 0, 0, 100))
        self._container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        if title:
            self._header = ModalHeader(title, colors=self._colors)
            self._header.close_clicked.connect(self.reject)
            container_layout.addWidget(self._header)

        # Body
        self._body = ModalBody(colors=self._colors)
        container_layout.addWidget(self._body)

        # Footer
        self._footer = ModalFooter(colors=self._colors)
        container_layout.addWidget(self._footer)

        main_layout.addWidget(self._container, alignment=Qt.AlignmentFlag.AlignCenter)

    @property
    def body(self) -> QVBoxLayout:
        """Access the body layout to add content"""
        return self._body.layout()

    def add_button(
        self, text: str, variant: str = "primary", on_click=None
    ) -> QPushButton:
        """Add a button to the footer"""
        return self._footer.add_button(text, variant, on_click)

    def set_body_content(self, widget: QWidget):
        """Set the body content widget"""
        self._body.set_content(widget)


class ModalHeader(QFrame):
    """Modal header with title and close button"""

    close_clicked = Signal()

    def __init__(self, title: str = "", colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-bottom: 1px solid {self._colors.border};
                padding: {SPACING.lg}px {SPACING.xl}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg)

        # Title - using display font for prominence
        self._title = QLabel(title)
        self._title.setStyleSheet(f"""
            font-family: {TYPOGRAPHY.font_family_display};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
            color: {self._colors.text_primary};
        """)
        layout.addWidget(self._title)

        layout.addStretch()

        # Close button
        self._close_btn = QPushButton("×")
        self._close_btn.setFixedSize(32, 32)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.text_secondary};
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)
        self._close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self._close_btn)

    def setTitle(self, title: str):
        self._title.setText(title)


class ModalBody(QFrame):
    """Modal body container"""

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        self._layout.setSpacing(SPACING.md)

    def layout(self) -> QVBoxLayout:
        return self._layout

    def set_content(self, widget: QWidget):
        # Clear existing content
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._layout.addWidget(widget)


class ModalFooter(QFrame):
    """Modal footer with action buttons"""

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-top: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.xl, SPACING.md, SPACING.xl, SPACING.md)
        self._layout.setSpacing(SPACING.sm)
        self._layout.addStretch()

    def add_button(
        self, text: str, variant: str = "primary", on_click=None
    ) -> QPushButton:
        """Add a button to the footer"""
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("variant", variant if variant != "primary" else "")

        # Apply variant styles
        styles = {
            "primary": f"""
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
            """,
            "secondary": f"""
                background-color: {self._colors.surface_light};
                color: {self._colors.text_primary};
            """,
            "destructive": f"""
                background-color: {self._colors.error};
                color: {self._colors.error_foreground};
            """,
            "outline": f"""
                background-color: transparent;
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
            """,
        }

        style = styles.get(variant, styles["primary"])
        btn.setStyleSheet(f"""
            QPushButton {{
                {style}
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.xl}px;
                font-size: {TYPOGRAPHY.text_base}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                min-height: 36px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)

        if on_click:
            btn.clicked.connect(on_click)

        self._layout.addWidget(btn)
        return btn
