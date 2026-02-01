"""
References Panel

A table-based panel for displaying and managing bibliographic references.

Implements QC-041.02:
- AC #1: I can see list of all references
- AC #2: I can edit reference metadata
- AC #3: I can delete references

Structure:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                              │
│ [Add] [Import RIS] [Export]                        [Search...      ] │
├─────────────────────────────────────────────────────────────────────┤
│ TABLE                                                                │
│ ☑ | Title                    | Authors      | Year | Segments | Act │
│ ──────────────────────────────────────────────────────────────────── │
│   | Logic of Scientific...   | Popper, Karl | 1959 |    0     | ··· │
│   | Qualitative Research...  | Smith, John  | 2020 |    2     | ··· │
└─────────────────────────────────────────────────────────────────────┘
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_colors
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY

from ..dto import ReferenceDTO


class ReferencesPanel(QFrame):
    """
    Panel for displaying and managing references.

    Signals:
        add_reference_clicked: User clicked add button
        import_clicked: User clicked import button
        export_clicked: User clicked export button
        search_changed(str): Search text changed
        reference_clicked(str): User single-clicked a reference
        reference_double_clicked(str): User double-clicked a reference
        selection_changed(list): Selected reference IDs changed
        delete_references(list): User wants to delete references
        edit_reference(str): User wants to edit a reference
    """

    # Toolbar signals
    add_reference_clicked = Signal()
    import_clicked = Signal()
    export_clicked = Signal()
    search_changed = Signal(str)

    # Table signals
    reference_clicked = Signal(str)
    reference_double_clicked = Signal(str)
    selection_changed = Signal(list)

    # Action signals
    delete_references = Signal(list)
    edit_reference = Signal(str)

    # Column indices
    COL_CHECKBOX = 0
    COL_TITLE = 1
    COL_AUTHORS = 2
    COL_YEAR = 3
    COL_SEGMENTS = 4
    COL_ACTIONS = 5

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the references panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._references: list[ReferenceDTO] = []
        self._selected_ids: set[str] = set()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the panel UI."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.md)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Table
        self._table = self._create_table()
        layout.addWidget(self._table)

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar widget."""
        toolbar = QWidget()
        toolbar.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)

        # Add button
        self._add_btn = QPushButton("+ Add Reference")
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.text_on_primary};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_hover};
            }}
        """)
        layout.addWidget(self._add_btn)

        # Import button
        self._import_btn = QPushButton("Import RIS")
        self._import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors.surface_elevated};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_hover};
            }}
        """)
        layout.addWidget(self._import_btn)

        # Export button
        self._export_btn = QPushButton("Export")
        self._export_btn.setStyleSheet(self._import_btn.styleSheet())
        layout.addWidget(self._export_btn)

        layout.addStretch()

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search references...")
        self._search_input.setMinimumWidth(200)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors.surface_elevated};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {self._colors.primary};
            }}
        """)
        layout.addWidget(self._search_input)

        return toolbar

    def _create_table(self) -> QTableWidget:
        """Create the references table."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["", "Title", "Authors", "Year", "Segments", "Actions"]
        )

        # Style
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self._colors.surface};
                border: none;
                gridline-color: {self._colors.border};
            }}
            QTableWidget::item {{
                padding: {SPACING.sm}px;
                border-bottom: 1px solid {self._colors.border};
            }}
            QTableWidget::item:selected {{
                background-color: {self._colors.primary}20;
            }}
            QHeaderView::section {{
                background-color: {self._colors.surface_elevated};
                color: {self._colors.text_secondary};
                border: none;
                border-bottom: 1px solid {self._colors.border};
                padding: {SPACING.sm}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                text-transform: uppercase;
            }}
        """)

        # Behavior
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)

        # Column sizing
        header = table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECKBOX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_AUTHORS, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(self.COL_YEAR, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_SEGMENTS, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(self.COL_CHECKBOX, 40)
        table.setColumnWidth(self.COL_AUTHORS, 180)
        table.setColumnWidth(self.COL_YEAR, 60)
        table.setColumnWidth(self.COL_SEGMENTS, 80)
        table.setColumnWidth(self.COL_ACTIONS, 80)

        return table

    def _connect_signals(self):
        """Connect internal signals."""
        self._add_btn.clicked.connect(self.add_reference_clicked.emit)
        self._import_btn.clicked.connect(self.import_clicked.emit)
        self._export_btn.clicked.connect(self.export_clicked.emit)
        self._search_input.textChanged.connect(self.search_changed.emit)

        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _on_cell_clicked(self, row: int, column: int):
        """Handle cell click."""
        if row < 0 or row >= len(self._references):
            return

        ref_id = self._references[row].id

        if column == self.COL_CHECKBOX:
            # Toggle selection
            if ref_id in self._selected_ids:
                self._selected_ids.remove(ref_id)
            else:
                self._selected_ids.add(ref_id)
            self._update_row_checkbox(row)
            self.selection_changed.emit(list(self._selected_ids))
        else:
            self.reference_clicked.emit(ref_id)

    def _on_cell_double_clicked(self, row: int, column: int):
        """Handle cell double-click."""
        if row < 0 or row >= len(self._references):
            return

        if column != self.COL_CHECKBOX:
            ref_id = self._references[row].id
            self.reference_double_clicked.emit(ref_id)

    def _update_row_checkbox(self, row: int):
        """Update checkbox visual state for a row."""
        if row < 0 or row >= len(self._references):
            return

        checkbox_widget = self._table.cellWidget(row, self.COL_CHECKBOX)
        if checkbox_widget:
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                ref_id = self._references[row].id
                checkbox.setChecked(ref_id in self._selected_ids)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_references(self, references: list[ReferenceDTO]):
        """
        Set the references to display.

        Args:
            references: List of ReferenceDTO objects
        """
        self._references = references
        self._selected_ids.clear()
        self._table.setRowCount(0)

        for ref in references:
            self._add_reference_row(ref)

    def _add_reference_row(self, ref: ReferenceDTO):
        """Add a row for a reference."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Checkbox
        checkbox_container = QWidget()
        checkbox_container.setStyleSheet("background: transparent;")
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox = QCheckBox()
        checkbox.setChecked(ref.id in self._selected_ids)
        checkbox_layout.addWidget(checkbox)
        self._table.setCellWidget(row, self.COL_CHECKBOX, checkbox_container)

        # Title
        title_item = QTableWidgetItem(ref.title)
        title_item.setToolTip(ref.title)
        self._table.setItem(row, self.COL_TITLE, title_item)

        # Authors (truncate if too long)
        authors = ref.authors
        if len(authors) > 30:
            authors = authors[:27] + "..."
        authors_item = QTableWidgetItem(authors)
        authors_item.setToolTip(ref.authors)
        self._table.setItem(row, self.COL_AUTHORS, authors_item)

        # Year
        year_text = str(ref.year) if ref.year else "-"
        year_item = QTableWidgetItem(year_text)
        year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, self.COL_YEAR, year_item)

        # Segments count
        segments_item = QTableWidgetItem(str(ref.segment_count))
        segments_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, self.COL_SEGMENTS, segments_item)

        # Actions
        actions_container = QWidget()
        actions_container.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(SPACING.xs, 0, SPACING.xs, 0)
        actions_layout.setSpacing(SPACING.xs)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(24)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.primary};
                border: none;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        edit_btn.clicked.connect(lambda checked, r=ref.id: self.edit_reference.emit(r))
        actions_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Del")
        delete_btn.setFixedHeight(24)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self._colors.error};
                border: none;
                font-size: {TYPOGRAPHY.text_xs}px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        delete_btn.clicked.connect(
            lambda checked, r=ref.id: self.delete_references.emit([r])
        )
        actions_layout.addWidget(delete_btn)

        self._table.setCellWidget(row, self.COL_ACTIONS, actions_container)

        # Row height
        self._table.setRowHeight(row, 44)

    def get_selected_ids(self) -> list[str]:
        """Get currently selected reference IDs."""
        return list(self._selected_ids)

    def clear_selection(self):
        """Clear all selections."""
        self._selected_ids.clear()
        for row in range(self._table.rowCount()):
            self._update_row_checkbox(row)
        self.selection_changed.emit([])
