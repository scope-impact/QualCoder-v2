"""
Statistics Card component
Material Design styled statistics display
"""

from .qt_compat import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect,
    Qt, QColor,
)

from .tokens import SPACING, RADIUS, TYPOGRAPHY, ColorPalette, get_theme
from .icons import Icon


class StatCard(QFrame):
    """
    Statistics display card with value, label, and optional trend indicator.

    Usage:
        card = StatCard(
            value="341",
            label="Coded Segments",
            trend="+12%",
            trend_direction="up"
        )
    """

    def __init__(
        self,
        value: str,
        label: str,
        trend: str = None,
        trend_direction: str = None,  # "up", "down", or None
        icon: str = None,
        color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._accent_color = color or self._colors.primary

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.xs)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon (optional)
        if icon:
            # Check if it's an MDI icon (mdi6.xxx) or emoji/text
            if icon.startswith("mdi6."):
                icon_widget = Icon(icon, size=28, color=self._accent_color, colors=self._colors)
                layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                # Emoji or text icon
                icon_label = QLabel(icon)
                icon_label.setStyleSheet(f"""
                    color: {self._accent_color};
                    font-size: 24px;
                """)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(icon_label)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {self._accent_color};
            font-size: 36px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)

        # Trend (optional)
        if trend:
            trend_layout = QHBoxLayout()
            trend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            trend_layout.setSpacing(SPACING.xs)

            # Trend arrow
            if trend_direction == "up":
                arrow = "↑"
                trend_color = self._colors.success
            elif trend_direction == "down":
                arrow = "↓"
                trend_color = self._colors.error
            else:
                arrow = ""
                trend_color = self._colors.text_secondary

            if arrow:
                arrow_label = QLabel(arrow)
                arrow_label.setStyleSheet(f"""
                    color: {trend_color};
                    font-size: {TYPOGRAPHY.text_sm}px;
                """)
                trend_layout.addWidget(arrow_label)

            trend_label = QLabel(trend)
            trend_label.setStyleSheet(f"""
                color: {trend_color};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            trend_layout.addWidget(trend_label)

            layout.addLayout(trend_layout)


class StatCardRow(QFrame):
    """
    Horizontal row of stat cards.

    Usage:
        row = StatCardRow()
        row.add_stat("341", "Segments")
        row.add_stat("24", "Codes")
        row.add_stat("12", "Files")
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(SPACING.lg)

    def add_stat(
        self,
        value: str,
        label: str,
        trend: str = None,
        trend_direction: str = None,
        icon: str = None,
        color: str = None
    ) -> StatCard:
        """Add a stat card to the row"""
        card = StatCard(
            value=value,
            label=label,
            trend=trend,
            trend_direction=trend_direction,
            icon=icon,
            color=color,
            colors=self._colors
        )
        self._layout.addWidget(card)
        return card


class MiniStatCard(QFrame):
    """
    Compact stat card for inline display.

    Usage:
        stat = MiniStatCard("24", "codes", color="#009688")
    """

    def __init__(
        self,
        value: str,
        label: str,
        color: str = None,
        colors: ColorPalette = None,
        parent=None
    ):
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        accent = color or self._colors.primary

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {accent};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(value_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        layout.addWidget(label_widget)
