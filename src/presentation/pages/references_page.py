"""
References Page

Composes the References organisms into a complete page layout.

Layout:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                              │
│ [Add Reference] [Import RIS] [Export]              [Search...      ] │
├─────────────────────────────────────────────────────────────────────┤
│ TABLE (ReferencesPanel) - or EmptyState if no references            │
│ ┌───┬────────────────────────┬────────────┬──────┬─────────────┐   │
│ │ ☑ │ Title                  │ Authors    │ Year │ Actions     │   │
│ ├───┼────────────────────────┼────────────┼──────┼─────────────┤   │
│ │   │ Logic of Scientific... │ Popper, K  │ 1959 │ [···]       │   │
│ │   │ Qualitative Research   │ Smith, J   │ 2020 │ [···]       │   │
│ └───┴────────────────────────┴────────────┴──────┴─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

Implements QC-041.02 presentation layer:
- AC #1: I can see list of all references
- AC #2: I can edit reference metadata
- AC #3: I can delete references
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QStackedWidget, QVBoxLayout, QWidget

from design_system import ColorPalette, get_colors
from design_system.tokens import SPACING

from ..dto import ReferenceDTO
from ..organisms import EmptyState
from ..organisms.references_panel import ReferencesPanel


class ReferencesPage(QWidget):
    """
    Complete References page that composes all related organisms.

    Signals:
        add_reference_clicked: User clicked add reference
        import_clicked: User clicked import
        export_clicked: User clicked export
        reference_clicked(str): User single-clicked a reference
        reference_double_clicked(str): User double-clicked a reference
        selection_changed(list): Selected reference IDs changed
        delete_references(list): User wants to delete selected references
        edit_reference(str): User wants to edit a reference
        search_changed(str): Search text changed
    """

    # Toolbar actions
    add_reference_clicked = Signal()
    import_clicked = Signal()
    export_clicked = Signal()

    # Table interactions
    reference_clicked = Signal(str)
    reference_double_clicked = Signal(str)
    selection_changed = Signal(list)

    # Reference actions
    delete_references = Signal(list)
    edit_reference = Signal(str)

    # Search
    search_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the References page.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()

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

        # References panel (includes toolbar)
        self._references_panel = ReferencesPanel(colors=self._colors)
        layout.addWidget(self._references_panel, 0)

        # Content area: either table or empty state
        self._content_stack = QStackedWidget()

        # Empty state
        self._empty_state = EmptyState(colors=self._colors)
        self._empty_state.set_title("No References")
        self._empty_state.set_description(
            "Add references to cite in your research. "
            "You can import from RIS files or add manually."
        )
        self._content_stack.addWidget(self._empty_state)

        # Table container (references panel has the table)
        self._table_container = QFrame()
        self._table_container.setStyleSheet("background: transparent;")
        table_layout = QVBoxLayout(self._table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # The panel already contains the table, so we just show it
        self._content_stack.addWidget(self._table_container)

        layout.addWidget(self._content_stack, 1)

    def _connect_signals(self):
        """Wire organism signals to page signals."""
        # Panel toolbar signals
        self._references_panel.add_reference_clicked.connect(
            self.add_reference_clicked.emit
        )
        self._references_panel.import_clicked.connect(self.import_clicked.emit)
        self._references_panel.export_clicked.connect(self.export_clicked.emit)
        self._references_panel.search_changed.connect(self.search_changed.emit)

        # Table signals
        self._references_panel.reference_clicked.connect(self.reference_clicked.emit)
        self._references_panel.reference_double_clicked.connect(
            self.reference_double_clicked.emit
        )
        self._references_panel.selection_changed.connect(self.selection_changed.emit)
        self._references_panel.delete_references.connect(self.delete_references.emit)
        self._references_panel.edit_reference.connect(self.edit_reference.emit)

        # Empty state
        self._empty_state.import_clicked.connect(self.add_reference_clicked.emit)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_references(self, references: list[ReferenceDTO]):
        """
        Set the references to display.

        Args:
            references: List of ReferenceDTO objects
        """
        if not references:
            self._content_stack.setCurrentWidget(self._empty_state)
        else:
            self._references_panel.set_references(references)
            self._content_stack.setCurrentWidget(self._references_panel)

    def get_selected_ids(self) -> list[str]:
        """Get currently selected reference IDs."""
        return self._references_panel.get_selected_ids()

    def clear_selection(self):
        """Clear all selections."""
        self._references_panel.clear_selection()

    def get_active_filter(self) -> str | None:
        """Get the currently active filter (not used for references)."""
        return None
