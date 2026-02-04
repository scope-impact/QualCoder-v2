"""
Case Table Organism

Data table for displaying and managing cases in a project.
Supports selection, sorting, and row actions.

Implements QC-034 presentation layer:
- AC #1-4: Researcher can manage cases through UI
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_colors
from design_system.icons import Icon, get_qicon
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY, hex_to_rgba

from ..dto import CaseDTO


class CaseTableRow(QWidget):
    """Custom widget for case name cell with icon."""

    def __init__(
        self,
        name: str,
        description: str | None,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Case icon
        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"""
            background-color: {hex_to_rgba(self._colors.primary, 0.15)};
            border-radius: {RADIUS.md}px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_widget = Icon(
            "mdi6.account-outline",
            size=18,
            color=self._colors.primary,
            colors=self._colors,
        )
        icon_layout.addWidget(icon_widget)
        layout.addWidget(icon_frame)

        # Case info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        info_layout.addWidget(name_label)

        if description:
            desc_label = QLabel(
                description[:50] + "..." if len(description) > 50 else description
            )
            desc_label.setStyleSheet(f"""
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)
            info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)
        layout.addStretch()


class CaseTable(QFrame):
    """
    Data table for displaying cases.

    Signals:
        case_clicked: Emitted when a case row is clicked (case_id)
        case_double_clicked: Emitted when a case row is double-clicked (case_id)
        selection_changed: Emitted when selection changes (list of case_ids)
        delete_cases: Emitted for bulk delete action (list of case_ids)
        link_source: Emitted to link source to case (case_id)
        edit_case: Emitted to edit a case (case_id)
    """

    case_clicked = Signal(str)
    case_double_clicked = Signal(str)
    selection_changed = Signal(list)
    delete_cases = Signal(list)
    link_source = Signal(str)
    edit_case = Signal(str)

    # Column indices
    COL_CHECKBOX = 0
    COL_NAME = 1
    COL_SOURCES = 2
    COL_ATTRIBUTES = 3
    COL_ACTIONS = 4

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._cases: list[CaseDTO] = []
        self._selected_ids: set[str] = set()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the table UI."""
        self.setStyleSheet(f"""
            CaseTable {{
                background-color: {self._colors.surface};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["", "Name", "Sources", "Attributes", "Actions"]
        )

        # Style header
        header = self._table.horizontalHeader()
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                padding: {SPACING.sm}px {SPACING.md}px;
                border: none;
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header.setSectionResizeMode(self.COL_CHECKBOX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_SOURCES, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_ATTRIBUTES, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)

        self._table.setColumnWidth(self.COL_CHECKBOX, 40)
        self._table.setColumnWidth(self.COL_SOURCES, 80)
        self._table.setColumnWidth(self.COL_ATTRIBUTES, 100)
        self._table.setColumnWidth(self.COL_ACTIONS, 100)

        # Hide vertical header
        self._table.verticalHeader().setVisible(False)

        # Selection behavior
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Style table
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {self._colors.border};
            }}
            QTableWidget::item {{
                padding: {SPACING.sm}px;
                border-bottom: 1px solid {self._colors.border};
            }}
            QTableWidget::item:selected {{
                background-color: {hex_to_rgba(self._colors.primary, 0.1)};
            }}
        """)

        layout.addWidget(self._table)

    def _connect_signals(self):
        """Connect internal signals."""
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def set_cases(self, cases: list[CaseDTO]):
        """Set the cases to display."""
        self._cases = cases
        self._populate_table()

    def _populate_table(self):
        """Populate table with case data."""
        self._table.setRowCount(len(self._cases))

        for row, case in enumerate(self._cases):
            self._table.setRowHeight(row, 60)

            # Checkbox
            checkbox = QCheckBox()
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    margin-left: {SPACING.md}px;
                }}
            """)
            checkbox.stateChanged.connect(
                lambda state, cid=case.id: self._on_checkbox_changed(cid, state)
            )
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.addWidget(checkbox)
            self._table.setCellWidget(row, self.COL_CHECKBOX, checkbox_widget)

            # Name with icon
            name_widget = CaseTableRow(
                name=case.name,
                description=case.description,
                colors=self._colors,
            )
            self._table.setCellWidget(row, self.COL_NAME, name_widget)

            # Also set text for sorting/searching
            name_item = QTableWidgetItem(case.name)
            name_item.setData(Qt.ItemDataRole.UserRole, case.id)
            self._table.setItem(row, self.COL_NAME, name_item)

            # Sources count
            sources_item = QTableWidgetItem(str(case.source_count))
            sources_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, self.COL_SOURCES, sources_item)

            # Attributes count
            attrs_item = QTableWidgetItem(str(len(case.attributes)))
            attrs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, self.COL_ATTRIBUTES, attrs_item)

            # Actions
            actions_widget = self._create_actions_widget(case.id)
            self._table.setCellWidget(row, self.COL_ACTIONS, actions_widget)

    def _create_actions_widget(self, case_id: str) -> QWidget:
        """Create action buttons for a row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(SPACING.xs, 0, SPACING.xs, 0)
        layout.setSpacing(SPACING.xs)

        # Link source button
        link_btn = QPushButton()
        link_btn.setIcon(
            get_qicon("mdi6.link-variant", color=self._colors.text_secondary)
        )
        link_btn.setToolTip("Link Source")
        link_btn.setFixedSize(28, 28)
        link_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        link_btn.clicked.connect(lambda: self.link_source.emit(case_id))
        layout.addWidget(link_btn)

        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(
            get_qicon("mdi6.pencil-outline", color=self._colors.text_secondary)
        )
        edit_btn.setToolTip("Edit Case")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)
        edit_btn.clicked.connect(lambda: self.edit_case.emit(case_id))
        layout.addWidget(edit_btn)

        layout.addStretch()
        return widget

    def _on_cell_clicked(self, row: int, _col: int):
        """Handle cell click."""
        if row < len(self._cases):
            self.case_clicked.emit(self._cases[row].id)

    def _on_cell_double_clicked(self, row: int, _col: int):
        """Handle cell double-click."""
        if row < len(self._cases):
            self.case_double_clicked.emit(self._cases[row].id)

    def _on_selection_changed(self):
        """Handle selection change."""
        selected_ids = list(self._selected_ids)
        self.selection_changed.emit(selected_ids)

    def _on_checkbox_changed(self, case_id: str, state: int):
        """Handle checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            self._selected_ids.add(case_id)
        else:
            self._selected_ids.discard(case_id)
        self.selection_changed.emit(list(self._selected_ids))

    def get_selected_ids(self) -> list[str]:
        """Get list of selected case IDs."""
        return list(self._selected_ids)

    def clear_selection(self):
        """Clear all selections."""
        self._selected_ids.clear()
        # Uncheck all checkboxes
        for row in range(self._table.rowCount()):
            widget = self._table.cellWidget(row, self.COL_CHECKBOX)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
