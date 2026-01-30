"""
Toast notification components
Material Design styled popup notifications
"""

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class Toast(QWidget):
    """
    Toast notification popup.

    Usage:
        toast = Toast("File saved successfully", variant="success")
        toast.show_toast()

        # Or use the ToastManager for automatic positioning
        ToastManager.show("Error occurred", variant="error")
    """

    closed = Signal()

    def __init__(
        self,
        message: str,
        variant: str = "info",
        duration: int = 4000,
        closable: bool = True,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._duration = duration
        self._variant = variant

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._setup_ui(message, closable)

        # Auto-close timer
        if duration > 0:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self.close_toast)

    def _setup_ui(self, message: str, closable: bool):
        # Variant colors and icons
        variants = {
            "success": (self._colors.success, "✓"),
            "error": (self._colors.error, "✕"),
            "warning": (self._colors.warning, "⚠"),
            "info": (self._colors.info, "ℹ"),
        }

        accent_color, icon = variants.get(self._variant, variants["info"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Container
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.surface};
                border-left: 4px solid {accent_color};
                border-radius: {RADIUS.md}px;
            }}
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 80))
        container.setGraphicsEffect(shadow)

        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        container_layout.setSpacing(SPACING.md)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            color: {accent_color};
            font-size: 18px;
            font-weight: bold;
        """)
        container_layout.addWidget(icon_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        msg_label.setWordWrap(True)
        container_layout.addWidget(msg_label, 1)

        # Close button
        if closable:
            close_btn = QPushButton("×")
            close_btn.setFixedSize(24, 24)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self._colors.text_secondary};
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {self._colors.surface_light};
                }}
            """)
            close_btn.clicked.connect(self.close_toast)
            container_layout.addWidget(close_btn)

        layout.addWidget(container)

        # Set minimum size
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        self.adjustSize()

    def show_toast(self):
        """Show the toast with animation"""
        self.show()
        if self._duration > 0:
            self._timer.start(self._duration)

    def close_toast(self):
        """Close the toast"""
        self.closed.emit()
        self.close()
        self.deleteLater()


class ToastContainer(QWidget):
    """
    Container for managing multiple toasts.
    Handles positioning and stacking of toasts.
    """

    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.sm)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self._toasts = []

    @classmethod
    def instance(cls, parent=None) -> "ToastContainer":
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def add_toast(self, toast: Toast):
        """Add a toast to the container"""
        self._toasts.append(toast)
        self._layout.addWidget(toast)
        toast.closed.connect(lambda: self._remove_toast(toast))
        toast.show()

        self._update_position()
        self.show()

    def _remove_toast(self, toast: Toast):
        """Remove a toast from the container"""
        if toast in self._toasts:
            self._toasts.remove(toast)

        if not self._toasts:
            self.hide()
        else:
            self._update_position()

    def _update_position(self):
        """Update container position at bottom center of screen"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            self.adjustSize()
            x = geometry.center().x() - self.width() // 2
            y = geometry.bottom() - self.height() - 60  # 60px from bottom for status bar
            self.move(x, y)


class ToastManager:
    """
    Static class for easily showing toasts.

    Usage:
        ToastManager.success("File saved!")
        ToastManager.error("Something went wrong")
        ToastManager.warning("Unsaved changes")
        ToastManager.info("Tip: Use Ctrl+S to save")
    """

    @staticmethod
    def _show(message: str, variant: str, duration: int = 4000):
        container = ToastContainer.instance()
        toast = Toast(message, variant=variant, duration=duration)
        container.add_toast(toast)
        toast.show_toast()

    @staticmethod
    def success(message: str, duration: int = 4000):
        ToastManager._show(message, "success", duration)

    @staticmethod
    def error(message: str, duration: int = 6000):
        ToastManager._show(message, "error", duration)

    @staticmethod
    def warning(message: str, duration: int = 5000):
        ToastManager._show(message, "warning", duration)

    @staticmethod
    def info(message: str, duration: int = 4000):
        ToastManager._show(message, "info", duration)
