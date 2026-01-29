"""
Spinner/Loading components
Material Design styled loading indicators
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QConicalGradient

from .tokens import SPACING, TYPOGRAPHY, ColorPalette, get_theme


class Spinner(QWidget):
    """
    Circular loading spinner.

    Usage:
        spinner = Spinner(size=24)
        spinner.start()
        # Later...
        spinner.stop()
    """

    def __init__(
        self,
        size: int = 24,
        color: str = None,
        stroke_width: int = 3,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._size = size
        self._color = color or self._colors.primary
        self._stroke_width = stroke_width
        self._angle = 0
        self._running = False

        self.setFixedSize(size, size)

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        """Start the spinner animation"""
        self._running = True
        self._timer.start(16)  # ~60fps
        self.show()

    def stop(self):
        """Stop the spinner animation"""
        self._running = False
        self._timer.stop()

    def isRunning(self) -> bool:
        return self._running

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center and size
        size = self._size - self._stroke_width
        x = self._stroke_width / 2
        y = self._stroke_width / 2

        # Draw background circle (track)
        painter.setPen(QPen(
            QColor(self._colors.surface_light),
            self._stroke_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap
        ))
        painter.drawEllipse(int(x), int(y), size, size)

        # Draw spinning arc
        painter.setPen(QPen(
            QColor(self._color),
            self._stroke_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap
        ))

        # Draw arc (90 degrees)
        painter.drawArc(
            int(x), int(y), size, size,
            self._angle * 16,  # Start angle (in 1/16th degrees)
            90 * 16  # Span angle
        )


class LoadingIndicator(QWidget):
    """
    Loading indicator with spinner and optional text.

    Usage:
        loading = LoadingIndicator("Loading...")
        loading.start()
    """

    def __init__(
        self,
        text: str = "Loading...",
        spinner_size: int = 24,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner
        self._spinner = Spinner(size=spinner_size, colors=self._colors)
        layout.addWidget(self._spinner)

        # Text
        if text:
            self._label = QLabel(text)
            self._label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_sm}px;
            """)
            layout.addWidget(self._label)

    def start(self):
        """Start the loading animation"""
        self._spinner.start()
        self.show()

    def stop(self):
        """Stop the loading animation"""
        self._spinner.stop()

    def setText(self, text: str):
        """Update the loading text"""
        if hasattr(self, '_label'):
            self._label.setText(text)


class LoadingOverlay(QWidget):
    """
    Full-screen loading overlay.

    Usage:
        overlay = LoadingOverlay(parent_widget)
        overlay.show_loading("Processing...")
        # Later...
        overlay.hide_loading()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._colors = get_theme("dark")

        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(0, 0, 0, 0.5);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.surface};
                border-radius: 12px;
                padding: 24px;
            }}
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(SPACING.lg)

        # Spinner
        self._spinner = Spinner(size=40, colors=self._colors)
        container_layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Text
        self._label = QLabel("Loading...")
        self._label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_base}px;
        """)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._label)

        layout.addWidget(container)

        self.hide()

    def show_loading(self, text: str = "Loading..."):
        """Show the loading overlay"""
        self._label.setText(text)
        self._spinner.start()

        # Resize to parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        self.show()
        self.raise_()

    def hide_loading(self):
        """Hide the loading overlay"""
        self._spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        """Resize with parent"""
        if self.parent():
            self.setGeometry(self.parent().rect())


class SkeletonLoader(QWidget):
    """
    Skeleton loading placeholder.

    Usage:
        skeleton = SkeletonLoader(width=200, height=20)
    """

    def __init__(
        self,
        width: int = 100,
        height: int = 20,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setFixedSize(width, height)

        # Animation
        self._offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _animate(self):
        self._offset = (self._offset + 5) % (self.width() * 2)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create gradient
        gradient = QConicalGradient(self.width() / 2, self.height() / 2, 0)

        base_color = QColor(self._colors.surface_light)
        highlight_color = QColor(self._colors.surface_lighter)

        # Simplified shimmer effect
        painter.setBrush(base_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        # Shimmer highlight
        highlight_width = self.width() // 3
        highlight_x = (self._offset - highlight_width) % (self.width() + highlight_width)

        painter.setBrush(highlight_color)
        painter.setOpacity(0.5)
        painter.drawRoundedRect(
            int(highlight_x), 0,
            highlight_width, self.height(),
            4, 4
        )
