"""
Case Manager Page

Composes the Case Manager organisms into a complete page layout.
This page can be used standalone for development or within a screen.

Layout:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR (CaseManagerToolbar)                                         │
│ [Create Case] [Import] [Export]                     [Search...     ] │
├─────────────────────────────────────────────────────────────────────┤
│ STATS ROW (CaseSummaryStats) - clickable to filter                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                     │
│ │ Total Cases │ │With Sources │ │ Attributes  │                     │
│ │     12      │ │      8      │ │     25      │                     │
│ └─────────────┘ └─────────────┘ └─────────────┘                     │
├─────────────────────────────────────────────────────────────────────┤
│ TABLE (CaseTable) - or EmptyState if no cases                        │
│ ┌───┬──────────────────┬─────────┬────────────┬─────────────┐       │
│ │ ☑ │ Case Name        │ Sources │ Attributes │ Actions     │       │
│ ├───┼──────────────────┼─────────┼────────────┼─────────────┤       │
│ │   │ Participant A    │    3    │     5      │ [···]       │       │
│ │   │ Site Alpha       │    0    │     2      │ [···]       │       │
│ └───┴──────────────────┴─────────┴────────────┴─────────────┘       │
├─────────────────────────────────────────────────────────────────────┤
│ BULK ACTIONS BAR (shown when cases selected)                         │
│ ✓ 2 cases selected    [Link Source] [Delete]                    [×] │
└─────────────────────────────────────────────────────────────────────┘

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QStackedWidget, QVBoxLayout, QWidget

from design_system import ColorPalette, get_colors
from design_system.tokens import SPACING

from ..dto import CaseDTO, CaseSummaryDTO
from ..organisms import CaseManagerToolbar, CaseSummaryStats, CaseTable, EmptyState


class CaseManagerPage(QWidget):
    """
    Complete Case Manager page that composes all related organisms.

    This page manages the layout and data flow between organisms.
    It can be used standalone for development or embedded in a screen.

    Signals:
        create_case_clicked: User clicked create case
        import_clicked: User clicked import
        export_clicked: User clicked export
        case_clicked(str): User single-clicked a case
        case_double_clicked(str): User double-clicked a case to view details
        selection_changed(list): Selected case IDs changed
        delete_cases(list): User wants to delete selected cases
        link_source(str): User wants to link source to a case
        edit_case(str): User wants to edit a case
        filter_changed(str | None): Filter changed (None = show all)
        search_changed(str): Search text changed
    """

    # Toolbar actions
    create_case_clicked = Signal()
    import_clicked = Signal()
    export_clicked = Signal()

    # Table interactions
    case_clicked = Signal(str)
    case_double_clicked = Signal(str)
    selection_changed = Signal(list)

    # Case actions
    delete_cases = Signal(list)
    link_source = Signal(str)
    edit_case = Signal(str)

    # Filtering
    filter_changed = Signal(object)  # str | None
    search_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the Case Manager page.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_filter: str | None = None
        self._current_search: str = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the page layout."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Toolbar
        self._toolbar = CaseManagerToolbar(colors=self._colors)
        layout.addWidget(self._toolbar)

        # Stats row
        self._stats_row = CaseSummaryStats(colors=self._colors)
        layout.addWidget(self._stats_row)

        # Content area: either table or empty state
        self._content_stack = QStackedWidget()

        # Empty state (reuses file empty state styling)
        # TODO: Create CaseEmptyState with case-specific messaging
        self._empty_state = EmptyState(colors=self._colors)
        self._content_stack.addWidget(self._empty_state)

        # Table container
        self._table_container = QFrame()
        self._table_container.setStyleSheet("background: transparent;")
        table_layout = QVBoxLayout(self._table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self._case_table = CaseTable(colors=self._colors)
        table_layout.addWidget(self._case_table)

        self._content_stack.addWidget(self._table_container)

        layout.addWidget(self._content_stack, 1)

    def _connect_signals(self):
        """Wire organism signals to page signals."""
        # Toolbar signals
        self._toolbar.create_case_clicked.connect(self.create_case_clicked.emit)
        self._toolbar.import_clicked.connect(self.import_clicked.emit)
        self._toolbar.export_clicked.connect(self.export_clicked.emit)
        self._toolbar.search_changed.connect(self._on_search_changed)

        # Stats row signals
        self._stats_row.filter_changed.connect(self._on_filter_changed)

        # Table signals
        self._case_table.case_clicked.connect(self.case_clicked.emit)
        self._case_table.case_double_clicked.connect(self.case_double_clicked.emit)
        self._case_table.selection_changed.connect(self.selection_changed.emit)
        self._case_table.delete_cases.connect(self.delete_cases.emit)
        self._case_table.link_source.connect(self.link_source.emit)
        self._case_table.edit_case.connect(self.edit_case.emit)

        # Empty state signals
        self._empty_state.import_clicked.connect(self.create_case_clicked.emit)
        self._empty_state.link_clicked.connect(self.import_clicked.emit)

    def _on_filter_changed(self, filter_type: str | None):
        """Handle filter change from stats row."""
        self._current_filter = filter_type
        self.filter_changed.emit(filter_type)

    def _on_search_changed(self, query: str):
        """Handle search text change."""
        self._current_search = query
        self.search_changed.emit(query)

    # =========================================================================
    # Public API - Data setters
    # =========================================================================

    def set_cases(self, cases: list[CaseDTO]):
        """
        Set the cases to display.

        Args:
            cases: List of CaseDTO objects
        """
        if not cases:
            self._content_stack.setCurrentWidget(self._empty_state)
        else:
            self._case_table.set_cases(cases)
            self._content_stack.setCurrentWidget(self._table_container)

    def set_summary(self, summary: CaseSummaryDTO):
        """
        Set the summary statistics.

        Args:
            summary: CaseSummaryDTO with counts
        """
        self._stats_row.set_summary(summary)

    # =========================================================================
    # Public API - State access
    # =========================================================================

    def get_selected_ids(self) -> list[str]:
        """Get currently selected case IDs."""
        return self._case_table.get_selected_ids()

    def get_active_filter(self) -> str | None:
        """Get the currently active filter."""
        return self._current_filter

    def get_search_text(self) -> str:
        """Get the current search text."""
        return self._current_search

    # =========================================================================
    # Public API - State modification
    # =========================================================================

    def clear_selection(self):
        """Clear all case selections."""
        self._case_table.clear_selection()

    def clear_filter(self):
        """Clear the active filter."""
        self._stats_row.clear_filter()
        self._current_filter = None

    def clear_search(self):
        """Clear the search text."""
        self._toolbar.clear_search()
        self._current_search = ""

    # =========================================================================
    # Properties for testing
    # =========================================================================

    @property
    def toolbar(self) -> CaseManagerToolbar:
        """Access the toolbar organism."""
        return self._toolbar

    @property
    def stats_row(self) -> CaseSummaryStats:
        """Access the stats row organism."""
        return self._stats_row

    @property
    def case_table(self) -> CaseTable:
        """Access the case table organism."""
        return self._case_table

    @property
    def empty_state(self) -> EmptyState:
        """Access the empty state organism."""
        return self._empty_state
