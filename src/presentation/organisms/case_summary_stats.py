"""
Case Summary Stats Organism

Displays summary statistics for cases with clickable stat cards.

Implements QC-034 presentation layer:
- AC #4: Researcher can view all data for a case
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout

from design_system import ColorPalette, get_colors
from design_system.tokens import RADIUS, SPACING

from ..dto import CaseSummaryDTO
from .source_stats_row import StatCard


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
