"""
Case Summary Stats Organism

Displays summary statistics for cases with clickable stat cards.

Implements QC-034 presentation layer:
- AC #4: Researcher can view all data for a case
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from design_system import ColorPalette, get_colors
from design_system.icons import Icon
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY

from ..dto import CaseSummaryDTO


class StatCard(QFrame):
    """
    Clickable stat card for case summary.

    Displays count and label with icon. Clicking emits a signal for filtering.

    Signals:
        clicked(str): Emitted when card is clicked, with filter_type
    """

    clicked = Signal(str)

    def __init__(
        self,
        label: str,
        count: int = 0,
        icon: str = "mdi6.chart-box-outline",
        color: str = None,
        filter_type: str = "",
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._accent_color = color or self._colors.primary
        self._filter_type = filter_type
        self._count = count
        self._active = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(label, icon)
        self._update_style()

    def _setup_ui(self, label: str, icon_name: str):
        """Build the card UI."""
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Icon container with colored background
        icon_frame = QFrame()
        icon_frame.setFixedSize(48, 48)
        icon_frame.setStyleSheet(f"""
            background-color: {self._hex_with_alpha(self._accent_color, 0.2)};
            border-radius: {RADIUS.md}px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_widget = Icon(
            icon_name, size=24, color=self._accent_color, colors=self._colors
        )
        icon_layout.addWidget(icon_widget)
        layout.addWidget(icon_frame)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self._count_label = QLabel(str(self._count))
        self._count_label.setStyleSheet(f"""
            font-family: {TYPOGRAPHY.font_family_display};
            color: {self._colors.text_primary};
            font-size: 24px;
            font-weight: {TYPOGRAPHY.weight_bold};
        """)
        info_layout.addWidget(self._count_label)

        type_label = QLabel(label)
        type_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        info_layout.addWidget(type_label)

        layout.addLayout(info_layout)
        layout.addStretch()

    def _hex_with_alpha(self, hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba string."""
        color = QColor(hex_color)
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})"

    def _update_style(self):
        """Update card styling based on active state."""
        if self._active:
            border = f"2px solid {self._accent_color}"
            bg = self._hex_with_alpha(self._accent_color, 0.05)
        else:
            border = f"1px solid {self._colors.border}"
            bg = self._colors.surface

        self.setStyleSheet(f"""
            StatCard {{
                background-color: {bg};
                border-radius: {RADIUS.lg}px;
                border: {border};
            }}
            StatCard:hover {{
                background-color: {self._hex_with_alpha(self._accent_color, 0.08)};
            }}
        """)

    def set_count(self, count: int):
        """Update the count display."""
        self._count = count
        self._count_label.setText(str(count))

    def set_active(self, active: bool):
        """Set the active/filter state."""
        self._active = active
        self._update_style()

    def mousePressEvent(self, event):
        """Handle click to emit filter signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._filter_type)


class CaseSummaryStats(QFrame):
    """
    Summary statistics for cases.

    Displays clickable stat cards showing:
    - Total cases
    - Cases with sources linked
    - Total attributes

    Signals:
        filter_changed: Emitted when a filter is selected (filter_type or None)
    """

    filter_changed = Signal(object)  # str | None

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._active_filter: str | None = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the stats UI."""
        self.setStyleSheet(f"""
            CaseSummaryStats {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.md)

        # Total cases card
        self._total_cases_card = StatCard(
            label="Total Cases",
            count=0,
            icon="mdi6.account-group-outline",
            color=self._colors.primary,
            filter_type="all",
            colors=self._colors,
        )
        layout.addWidget(self._total_cases_card)

        # Cases with sources card
        self._with_sources_card = StatCard(
            label="With Sources",
            count=0,
            icon="mdi6.link-variant",
            color=self._colors.success,
            filter_type="with_sources",
            colors=self._colors,
        )
        layout.addWidget(self._with_sources_card)

        # Attributes card
        self._attributes_card = StatCard(
            label="Attributes",
            count=0,
            icon="mdi6.tag-multiple-outline",
            color=self._colors.info,
            filter_type="has_attributes",
            colors=self._colors,
        )
        layout.addWidget(self._attributes_card)

        layout.addStretch()

        self._cards = {
            "all": self._total_cases_card,
            "with_sources": self._with_sources_card,
            "has_attributes": self._attributes_card,
        }

    def _connect_signals(self):
        """Connect card click signals."""
        for _filter_type, card in self._cards.items():
            card.clicked.connect(self._on_card_clicked)

    def _on_card_clicked(self, filter_type: str):
        """Handle card click - toggle filter."""
        if self._active_filter == filter_type:
            # Deactivate
            self._active_filter = None
            self._cards[filter_type].set_active(False)
            self.filter_changed.emit(None)
        else:
            # Activate new filter
            if self._active_filter:
                self._cards[self._active_filter].set_active(False)
            self._active_filter = filter_type
            self._cards[filter_type].set_active(True)
            self.filter_changed.emit(filter_type)

    def set_summary(self, summary: CaseSummaryDTO):
        """Update the summary statistics."""
        self._total_cases_card.set_count(summary.total_cases)
        self._with_sources_card.set_count(summary.cases_with_sources)
        self._attributes_card.set_count(summary.total_attributes)

    def get_active_filter(self) -> str | None:
        """Get the currently active filter."""
        return self._active_filter

    def clear_filter(self):
        """Clear the active filter."""
        if self._active_filter:
            self._cards[self._active_filter].set_active(False)
        self._active_filter = None
        self.filter_changed.emit(None)
