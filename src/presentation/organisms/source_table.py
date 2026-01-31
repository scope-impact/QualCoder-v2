"""
Source Table Organism

Data table for displaying and managing source files in a project.
Supports selection, sorting, and row actions.

Based on mockup: phase1_file_manager.html
Addresses UX-004, UX-005, UX-006 from UX_TECH_DEBT.md:
- Double-click to open for coding
- Bulk actions bar when selection > 0
- Optimized columns for researcher workflow
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
from design_system.icons import Icon
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY, hex_to_rgba

from ..dto import SourceDTO


class SourceTableRow(QWidget):
    """Custom widget for source name cell with icon."""

    def __init__(
        self,
        name: str,
        source_type: str,
        file_size: int,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Type icon
        type_icons = {
            "text": ("mdi6.file-document-outline", self._colors.file_text),
            "audio": ("mdi6.music-note", self._colors.file_audio),
            "video": ("mdi6.video-outline", self._colors.file_video),
            "image": ("mdi6.image-outline", self._colors.file_image),
            "pdf": ("mdi6.file-pdf-box", self._colors.file_pdf),
        }
        icon_name, icon_color = type_icons.get(
            source_type, ("mdi6.file-outline", self._colors.text_secondary)
        )

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"""
            background-color: {hex_to_rgba(icon_color, 0.15)};
            border-radius: {RADIUS.md}px;
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_widget = Icon(icon_name, size=18, color=icon_color, colors=self._colors)
        icon_layout.addWidget(icon_widget)
        layout.addWidget(icon_frame)

        # File info
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

        size_text = self._format_size(file_size)
        size_label = QLabel(size_text)
        size_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        info_layout.addWidget(size_label)

        layout.addLayout(info_layout)
        layout.addStretch()

    def _format_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class StatusBadge(QFrame):
    """Status badge widget."""

    STATUS_STYLES = {
        "imported": ("info", "Imported"),
        "coded": ("success", "Coded"),
        "in_progress": ("warning", "In Progress"),
        "transcribing": ("warning", "Transcribing"),
        "error": ("error", "Error"),
    }

    def __init__(self, status: str, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()

        style_type, label = self.STATUS_STYLES.get(status, ("info", status.title()))

        color_map = {
            "success": self._colors.success,
            "warning": self._colors.warning,
            "error": self._colors.error,
            "info": self._colors.info,
        }
        color = color_map.get(style_type, self._colors.info)

        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {hex_to_rgba(color, 0.2)};
                border-radius: {RADIUS.full}px;
                padding: {SPACING.xs}px {SPACING.sm}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {color};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(label_widget)


class BulkActionsBar(QFrame):
    """
    Contextual action bar shown when files are selected.

    Addresses UX-005: Bulk Actions Hidden
    """

    code_clicked = Signal()
    delete_clicked = Signal()
    export_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._count = 0

        self.setStyleSheet(f"""
            BulkActionsBar {{
                background-color: {self._colors.surface_light};
                border-radius: {RADIUS.md}px;
                border: 1px solid {self._colors.border};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        # Selection count
        self._count_label = QLabel("0 files selected")
        self._count_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        layout.addWidget(self._count_label)

        layout.addStretch()

        # Action buttons
        self._code_btn = self._create_action_btn("Code", "mdi6.code-tags")
        self._code_btn.clicked.connect(self.code_clicked.emit)
        layout.addWidget(self._code_btn)

        self._delete_btn = self._create_action_btn(
            "Delete", "mdi6.delete-outline", danger=True
        )
        self._delete_btn.clicked.connect(self.delete_clicked.emit)
        layout.addWidget(self._delete_btn)

        self._export_btn = self._create_action_btn("Export", "mdi6.export")
        self._export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self._export_btn)

        # Clear selection
        clear_btn = QPushButton()
        try:
            import qtawesome as qta

            clear_btn.setIcon(qta.icon("mdi6.close", color=self._colors.text_secondary))
        except ImportError:
            clear_btn.setText("×")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
            }}
        """)
        clear_btn.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(clear_btn)

        self.hide()

    def _create_action_btn(
        self, text: str, icon_name: str, danger: bool = False
    ) -> QPushButton:
        """Create an action button."""
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if danger:
            color = self._colors.error
            hover_bg = hex_to_rgba(self._colors.error, 0.1)
        else:
            color = self._colors.text_primary
            hover_bg = self._colors.surface_lighter

        # Add icon if available
        try:
            import qtawesome as qta

            btn.setIcon(qta.icon(icon_name, color=color))
        except ImportError:
            pass

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
        """)
        return btn

    def set_count(self, count: int):
        """Update the selection count."""
        self._count = count
        self._count_label.setText(f"{count} file{'s' if count != 1 else ''} selected")
        self.setVisible(count > 0)


class SourceTable(QFrame):
    """
    Data table for source files.

    Displays sources with columns for name, type, date, cases, status.
    Supports selection, double-click to open, and sorting.

    Signals:
        source_clicked(str): Source row clicked (source_id)
        source_double_clicked(str): Source row double-clicked (source_id)
        selection_changed(list[str]): Selection changed (list of source_ids)
        open_for_coding(str): Request to open source for coding
        delete_sources(list[str]): Request to delete sources
        export_sources(list[str]): Request to export sources
    """

    source_clicked = Signal(str)
    source_double_clicked = Signal(str)
    selection_changed = Signal(list)
    open_for_coding = Signal(str)
    delete_sources = Signal(list)
    export_sources = Signal(list)

    COLUMNS = ["", "File Name", "Codes", "Cases", "Status", "Actions"]
    COL_CHECKBOX = 0
    COL_NAME = 1
    COL_CODES = 2
    COL_CASES = 3
    COL_STATUS = 4
    COL_ACTIONS = 5

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._sources: list[SourceDTO] = []
        self._source_map: dict[int, SourceDTO] = {}  # row -> SourceDTO

        self._setup_ui()

    def _setup_ui(self):
        """Build the table UI."""
        self.setStyleSheet(f"""
            SourceTable {{
                background-color: {self._colors.surface};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            background-color: {self._colors.surface};
            border-top-left-radius: {RADIUS.lg}px;
            border-top-right-radius: {RADIUS.lg}px;
            border-bottom: 1px solid {self._colors.border};
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(SPACING.sm)
        title_icon = Icon(
            "mdi6.folder-open-outline", size=20, color=self._colors.primary
        )
        title_layout.addWidget(title_icon)
        title_label = QLabel("Project Files")
        title_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_base}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        """)
        title_layout.addWidget(title_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()
        layout.addWidget(header_frame)

        # Bulk actions bar
        self._bulk_actions = BulkActionsBar(colors=self._colors)
        self._bulk_actions.code_clicked.connect(self._on_bulk_code)
        self._bulk_actions.delete_clicked.connect(self._on_bulk_delete)
        self._bulk_actions.export_clicked.connect(self._on_bulk_export)
        self._bulk_actions.clear_clicked.connect(self._clear_selection)
        layout.addWidget(self._bulk_actions)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)

        # Header styling
        self._table.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_medium};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: {SPACING.md}px {SPACING.lg}px;
                border: none;
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECKBOX, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_CODES, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_CASES, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_CHECKBOX, 40)
        self._table.setColumnWidth(self.COL_CODES, 80)
        self._table.setColumnWidth(self.COL_CASES, 100)
        self._table.setColumnWidth(self.COL_STATUS, 120)
        self._table.setColumnWidth(self.COL_ACTIONS, 100)

        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self._colors.surface};
                border: none;
            }}
            QTableWidget::item {{
                padding: {SPACING.md}px {SPACING.lg}px;
                border-bottom: 1px solid {self._colors.border};
                color: {self._colors.text_primary};
            }}
            QTableWidget::item:selected {{
                background-color: {hex_to_rgba(self._colors.primary, 0.10)};
            }}
            QTableWidget::item:hover {{
                background-color: {self._colors.surface_light};
            }}
        """)

        self._table.cellClicked.connect(self._on_cell_click)
        self._table.cellDoubleClicked.connect(self._on_cell_double_click)

        layout.addWidget(self._table)

    def set_sources(self, sources: list[SourceDTO]):
        """Set the list of sources to display."""
        self._sources = sources
        self._source_map.clear()
        self._table.setRowCount(len(sources))

        for row, source in enumerate(sources):
            self._source_map[row] = source
            self._populate_row(row, source)

        self._update_selection_count()

    def _populate_row(self, row: int, source: SourceDTO):
        """Populate a table row with source data."""
        # Checkbox
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda: self._update_selection_count())
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        checkbox_layout.addWidget(checkbox)
        self._table.setCellWidget(row, self.COL_CHECKBOX, checkbox_widget)

        # File name with icon
        name_widget = SourceTableRow(
            name=source.name,
            source_type=source.source_type,
            file_size=source.file_size,
            colors=self._colors,
        )
        self._table.setCellWidget(row, self.COL_NAME, name_widget)

        # Codes count
        codes_item = QTableWidgetItem(str(source.code_count))
        codes_item.setFlags(codes_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        codes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, self.COL_CODES, codes_item)

        # Cases
        cases_text = ", ".join(source.cases) if source.cases else "-"
        cases_item = QTableWidgetItem(cases_text)
        cases_item.setFlags(cases_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, self.COL_CASES, cases_item)

        # Status badge
        status_widget = StatusBadge(source.status, colors=self._colors)
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(SPACING.sm, 0, SPACING.sm, 0)
        status_layout.addWidget(status_widget)
        status_layout.addStretch()
        self._table.setCellWidget(row, self.COL_STATUS, status_container)

        # Actions
        actions_widget = self._create_row_actions(source.id)
        self._table.setCellWidget(row, self.COL_ACTIONS, actions_widget)

        # Set row height
        self._table.setRowHeight(row, 60)

    def _create_row_actions(self, source_id: str) -> QWidget:
        """Create action buttons for a row."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)

        # View button
        view_btn = QPushButton()
        try:
            import qtawesome as qta

            view_btn.setIcon(
                qta.icon("mdi6.eye-outline", color=self._colors.text_secondary)
            )
        except ImportError:
            view_btn.setText("👁")
        view_btn.setFixedSize(28, 28)
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.setToolTip("View")
        view_btn.setStyleSheet(self._action_btn_style())
        view_btn.clicked.connect(lambda: self.source_clicked.emit(source_id))
        layout.addWidget(view_btn)

        # Code button
        code_btn = QPushButton()
        try:
            import qtawesome as qta

            code_btn.setIcon(
                qta.icon("mdi6.code-tags", color=self._colors.text_secondary)
            )
        except ImportError:
            code_btn.setText("</>")
        code_btn.setFixedSize(28, 28)
        code_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        code_btn.setToolTip("Code")
        code_btn.setStyleSheet(self._action_btn_style())
        code_btn.clicked.connect(lambda: self.open_for_coding.emit(source_id))
        layout.addWidget(code_btn)

        # More button (placeholder)
        more_btn = QPushButton()
        try:
            import qtawesome as qta

            more_btn.setIcon(
                qta.icon("mdi6.dots-vertical", color=self._colors.text_secondary)
            )
        except ImportError:
            more_btn.setText("⋮")
        more_btn.setFixedSize(28, 28)
        more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        more_btn.setToolTip("More actions")
        more_btn.setStyleSheet(self._action_btn_style())
        layout.addWidget(more_btn)

        layout.addStretch()
        return widget

    def _action_btn_style(self) -> str:
        """Get stylesheet for action buttons."""
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_lighter};
            }}
        """

    def _on_cell_click(self, row: int, col: int):
        """Handle cell click."""
        if row in self._source_map and col != self.COL_CHECKBOX:
            self.source_clicked.emit(self._source_map[row].id)

    def _on_cell_double_click(self, row: int, col: int):
        """Handle cell double-click - open for coding."""
        if row in self._source_map and col != self.COL_CHECKBOX:
            source_id = self._source_map[row].id
            self.source_double_clicked.emit(source_id)
            self.open_for_coding.emit(source_id)

    def _update_selection_count(self):
        """Update bulk actions bar with selection count."""
        selected = self.get_selected_ids()
        self._bulk_actions.set_count(len(selected))
        self.selection_changed.emit(selected)

    def _clear_selection(self):
        """Clear all checkboxes."""
        for row in range(self._table.rowCount()):
            checkbox_widget = self._table.cellWidget(row, self.COL_CHECKBOX)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        self._update_selection_count()

    def get_selected_ids(self) -> list[str]:
        """Get IDs of selected sources."""
        selected = []
        for row in range(self._table.rowCount()):
            checkbox_widget = self._table.cellWidget(row, self.COL_CHECKBOX)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked() and row in self._source_map:
                    selected.append(self._source_map[row].id)
        return selected

    def clear_selection(self):
        """Clear all checkbox selections (public API)."""
        self._selected_ids.clear()
        self._clear_selection()

    def _on_bulk_code(self):
        """Handle bulk code action."""
        selected = self.get_selected_ids()
        if selected:
            # Open first selected for coding
            self.open_for_coding.emit(selected[0])

    def _on_bulk_delete(self):
        """Handle bulk delete action."""
        selected = self.get_selected_ids()
        if selected:
            self.delete_sources.emit(selected)

    def _on_bulk_export(self):
        """Handle bulk export action."""
        selected = self.get_selected_ids()
        if selected:
            self.export_sources.emit(selected)

    def select_source(self, source_id: str):
        """Select a source by ID."""
        for row, source in self._source_map.items():
            if source.id == source_id:
                self._table.selectRow(row)
                break

    def get_source_count(self) -> int:
        """Get total number of sources."""
        return len(self._sources)
