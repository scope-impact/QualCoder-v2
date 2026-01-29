"""
Progress Bar components
Material Design styled progress indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPainterPath

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class ProgressBar(QWidget):
    """
    Linear progress bar with optional label.

    Usage:
        progress = ProgressBar(value=67, label="Progress")
        progress.setValue(80)  # Update value
    """

    def __init__(
        self,
        value: int = 0,
        max_value: int = 100,
        label: str = None,
        show_percentage: bool = True,
        variant: str = "primary",
        height: int = 8,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._value = value
        self._max_value = max_value
        self._variant = variant
        self._bar_height = height

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # Header with label and percentage
        if label or show_percentage:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)

            if label:
                self._label = QLabel(label)
                self._label.setStyleSheet(f"""
                    color: {self._colors.text_primary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                """)
                header.addWidget(self._label)

            header.addStretch()

            if show_percentage:
                self._percentage = QLabel(f"{value}%")
                self._percentage.setStyleSheet(f"""
                    color: {self._colors.text_secondary};
                    font-size: {TYPOGRAPHY.text_sm}px;
                """)
                header.addWidget(self._percentage)

            layout.addLayout(header)
        else:
            self._percentage = None

        # Progress bar
        self._bar = ProgressBarWidget(
            value=value,
            max_value=max_value,
            variant=variant,
            height=height,
            colors=self._colors
        )
        layout.addWidget(self._bar)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        """Set the progress value"""
        self._value = max(0, min(value, self._max_value))
        self._bar.setValue(self._value)
        if self._percentage:
            percent = int((self._value / self._max_value) * 100)
            self._percentage.setText(f"{percent}%")

    def setMaxValue(self, max_value: int):
        """Set the maximum value"""
        self._max_value = max_value
        self._bar.setMaxValue(max_value)
        self.setValue(self._value)  # Recalculate percentage


class ProgressBarWidget(QWidget):
    """The actual progress bar drawing widget"""

    def __init__(
        self,
        value: int = 0,
        max_value: int = 100,
        variant: str = "primary",
        height: int = 8,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._value = value
        self._max_value = max_value
        self._variant = variant

        self.setFixedHeight(height)
        self.setMinimumWidth(100)

        # Get fill color based on variant
        variants = {
            "primary": self._colors.primary,
            "success": self._colors.success,
            "warning": self._colors.warning,
            "error": self._colors.error,
            "info": self._colors.info,
        }
        self._fill_color = variants.get(variant, self._colors.primary)

    def setValue(self, value: int):
        self._value = value
        self.update()

    def setMaxValue(self, max_value: int):
        self._max_value = max_value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        height = self.height()
        width = self.width()
        radius = height / 2

        # Draw background track
        painter.setBrush(QColor(self._colors.surface_lighter))
        painter.setPen(Qt.PenStyle.NoPen)

        track_path = QPainterPath()
        track_path.addRoundedRect(0, 0, width, height, radius, radius)
        painter.drawPath(track_path)

        # Draw fill
        if self._value > 0:
            fill_width = (self._value / self._max_value) * width
            fill_width = max(height, fill_width)  # Minimum width for rounded corners

            painter.setBrush(QColor(self._fill_color))
            fill_path = QPainterPath()
            fill_path.addRoundedRect(0, 0, fill_width, height, radius, radius)
            painter.drawPath(fill_path)


class ProgressBarLabeled(QWidget):
    """
    Progress bar with fraction label (e.g., "8/12 files").

    Usage:
        progress = ProgressBarLabeled(
            value=8,
            max_value=12,
            label="Files Coded"
        )
    """

    def __init__(
        self,
        value: int = 0,
        max_value: int = 100,
        label: str = "",
        variant: str = "primary",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._value = value
        self._max_value = max_value

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(self._label)

        header.addStretch()

        self._fraction = QLabel(f"{value}/{max_value}")
        self._fraction.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(self._fraction)

        layout.addLayout(header)

        # Progress bar
        self._bar = ProgressBarWidget(
            value=value,
            max_value=max_value,
            variant=variant,
            colors=self._colors
        )
        layout.addWidget(self._bar)

    def setValue(self, value: int):
        self._value = value
        self._bar.setValue(value)
        self._fraction.setText(f"{value}/{self._max_value}")

    def setMaxValue(self, max_value: int):
        self._max_value = max_value
        self._bar.setMaxValue(max_value)
        self._fraction.setText(f"{self._value}/{max_value}")
