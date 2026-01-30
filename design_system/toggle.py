"""
Toggle/Switch component
Material Design styled toggle for on/off states
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme


class Toggle(QWidget):
    """
    Toggle/Switch component for boolean on/off states.

    Usage:
        toggle = Toggle()
        toggle.toggled.connect(lambda checked: print(f"Toggled: {checked}"))
        toggle.setChecked(True)
    """

    toggled = Signal(bool)

    def __init__(
        self,
        checked: bool = False,
        label: str = "",
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._checked = checked
        self._handle_position = 22 if checked else 2

        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Animation for smooth toggle
        self._animation = QPropertyAnimation(self, b"handle_position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # If label provided, wrap in layout
        if label:
            self._setup_with_label(label)

    def _setup_with_label(self, label: str):
        """Create a wrapper with label"""
        # This would need a parent widget, so we just store the label
        self._label = label

    def _get_handle_position(self) -> int:
        return self._handle_position

    def _set_handle_position(self, pos: int):
        self._handle_position = pos
        self.update()

    handle_position = Property(int, _get_handle_position, _set_handle_position)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate_toggle()
            self.toggled.emit(checked)

    def toggle(self):
        self.setChecked(not self._checked)

    def _animate_toggle(self):
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(22 if self._checked else 2)
        self._animation.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw track
        track_color = QColor(self._colors.primary if self._checked else self._colors.surface_lighter)
        painter.setBrush(track_color)
        painter.setPen(Qt.PenStyle.NoPen)

        track_path = QPainterPath()
        track_path.addRoundedRect(0, 0, 44, 24, 12, 12)
        painter.drawPath(track_path)

        # Draw handle
        painter.setBrush(QColor("#FFFFFF"))
        handle_path = QPainterPath()
        handle_path.addEllipse(self._handle_position, 2, 20, 20)
        painter.drawPath(handle_path)


class LabeledToggle(QWidget):
    """
    Toggle with an associated label.

    Usage:
        toggle = LabeledToggle("Enable notifications")
        toggle.toggled.connect(lambda checked: print(f"Toggled: {checked}"))
    """

    toggled = Signal(bool)

    def __init__(
        self,
        label: str = "",
        checked: bool = False,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.md)

        # Label
        self._label = QLabel(label)
        self._label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_base}px;
        """)
        layout.addWidget(self._label)

        layout.addStretch()

        # Toggle
        self._toggle = Toggle(checked=checked, colors=self._colors)
        self._toggle.toggled.connect(self.toggled.emit)
        layout.addWidget(self._toggle)

    def isChecked(self) -> bool:
        return self._toggle.isChecked()

    def setChecked(self, checked: bool):
        self._toggle.setChecked(checked)

    def toggle(self):
        self._toggle.toggle()

    def setLabel(self, text: str):
        self._label.setText(text)
