"""
Progress Bar components
Material Design styled progress indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
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


class RelevanceScoreBar(QWidget):
    """
    Horizontal progress bar for displaying relevance/confidence scores.

    Used in AI search results and code suggestions to show
    how relevant or confident a result is.

    Usage:
        score = RelevanceScoreBar(score=0.85, label="Match Score")
        score.set_score(0.92)

    Variants:
        - "default": Primary color gradient
        - "confidence": Green/yellow/red based on score
        - "match": Blue gradient for search relevance
    """

    clicked = pyqtSignal(float)

    def __init__(
        self,
        score: float = 0,
        label: str = "",
        show_percentage: bool = True,
        variant: str = "default",
        width: int = 120,
        height: int = 6,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._score = max(0, min(1, score))
        self._label = label
        self._show_percentage = show_percentage
        self._variant = variant
        self._bar_width = width
        self._bar_height = height

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Label (optional)
        if label:
            self._label_widget = QLabel(label)
            self._label_widget.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            layout.addWidget(self._label_widget)

        # Score bar
        self._bar = RelevanceBarWidget(
            score=score,
            variant=variant,
            width=width,
            height=height,
            colors=self._colors
        )
        layout.addWidget(self._bar)

        # Percentage (optional)
        if show_percentage:
            self._percentage = QLabel(f"{int(score * 100)}%")
            self._percentage.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                min-width: 32px;
            """)
            layout.addWidget(self._percentage)

        layout.addStretch()

    def set_score(self, score: float):
        """Update the score (0-1)"""
        self._score = max(0, min(1, score))
        self._bar.set_score(self._score)
        if hasattr(self, '_percentage'):
            self._percentage.setText(f"{int(self._score * 100)}%")

    def score(self) -> float:
        """Get current score"""
        return self._score

    def set_variant(self, variant: str):
        """Change display variant"""
        self._variant = variant
        self._bar.set_variant(variant)


class RelevanceBarWidget(QWidget):
    """The actual relevance bar drawing widget"""

    def __init__(
        self,
        score: float = 0,
        variant: str = "default",
        width: int = 120,
        height: int = 6,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._score = max(0, min(1, score))
        self._variant = variant

        self.setFixedSize(width, height)

    def set_score(self, score: float):
        """Update score and redraw"""
        self._score = max(0, min(1, score))
        self.update()

    def set_variant(self, variant: str):
        """Change variant and redraw"""
        self._variant = variant
        self.update()

    def _get_fill_color(self) -> str:
        """Get fill color based on variant and score"""
        if self._variant == "confidence":
            # Color based on score threshold
            if self._score >= 0.8:
                return self._colors.success
            elif self._score >= 0.5:
                return self._colors.warning
            else:
                return self._colors.error

        elif self._variant == "match":
            return self._colors.info

        elif self._variant == "gradient":
            # Interpolate from warning to success
            if self._score < 0.5:
                return self._colors.warning
            else:
                return self._colors.success

        # Default: primary
        return self._colors.primary

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
        if self._score > 0:
            fill_width = self._score * width
            fill_width = max(height, fill_width)  # Minimum for rounded corners

            painter.setBrush(QColor(self._get_fill_color()))
            fill_path = QPainterPath()
            fill_path.addRoundedRect(0, 0, fill_width, height, radius, radius)
            painter.drawPath(fill_path)


class ScoreIndicator(QFrame):
    """
    Compact score indicator with label and bar.

    For use in list items and search results.

    Usage:
        indicator = ScoreIndicator(
            label="Relevance",
            score=0.87,
            variant="confidence"
        )
    """

    def __init__(
        self,
        label: str = "Score",
        score: float = 0,
        variant: str = "default",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # Header with label and percentage
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        header.addWidget(label_widget)

        header.addStretch()

        self._percentage = QLabel(f"{int(score * 100)}%")
        self._percentage.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        header.addWidget(self._percentage)

        layout.addLayout(header)

        # Bar
        self._bar = RelevanceBarWidget(
            score=score,
            variant=variant,
            width=100,
            height=4,
            colors=self._colors
        )
        layout.addWidget(self._bar)

    def set_score(self, score: float):
        """Update the score"""
        score = max(0, min(1, score))
        self._bar.set_score(score)
        self._percentage.setText(f"{int(score * 100)}%")
