"""
Import from S3 Dialog

Modal dialog triggered by [Import from S3] button in FileManager toolbar.
Lists files in the configured S3 data store, marks already-imported files,
and lets the user select which remote files to pull and auto-import.

Flow:
1. Dialog opens -> scans S3 for files
2. Cross-references with source_repo to mark already-imported files
3. User checks files to pull
4. Click "Pull Selected" -> download + auto-import each file
5. Dialog closes -> FileManager reloads via sources_changed signal
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
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
from design_system.tokens import RADIUS, SPACING, TYPOGRAPHY

if TYPE_CHECKING:
    from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
        DataStoreViewModel,
    )

logger = logging.getLogger("qualcoder.storage.presentation")


class ImportFromS3Dialog(QDialog):
    """
    Modal dialog for importing files from S3 data store.

    Shows remote files with status indicators:
    - "remote" = available to pull (checkable)
    - "imported" = already in Sources (greyed out)
    """

    def __init__(
        self,
        viewmodel: DataStoreViewModel,
        local_dir: str,
        colors: ColorPalette | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._local_dir = local_dir
        self._colors = colors or get_colors()
        self._remote_files: list = []
        self._imported_names: set[str] = set()

        self.setWindowTitle("Import from Data Store")
        self.setModal(True)
        self.setMinimumSize(600, 450)

        self._setup_ui()
        self._load_files()

    def _setup_ui(self) -> None:
        """Build the dialog UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self._colors.surface};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._setup_header(layout)

        # File table
        self._setup_table(layout)

        # Footer with buttons
        self._setup_footer(layout)

    def _setup_header(self, layout: QVBoxLayout) -> None:
        """Setup header with S3 prefix info and refresh button."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)

        config = self._viewmodel.get_config()
        prefix_text = ""
        if config:
            bucket = config["bucket_name"]
            prefix = config.get("prefix", "")
            prefix_text = f"S3: {bucket}/{prefix}" if prefix else f"S3: {bucket}/"

        self._prefix_label = QLabel(prefix_text)
        self._prefix_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
        """)
        header_layout.addWidget(self._prefix_label)

        header_layout.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.setStyleSheet(self._get_button_style())
        self._refresh_btn.clicked.connect(self._load_files)
        header_layout.addWidget(self._refresh_btn)

        layout.addWidget(header)

    def _setup_table(self, layout: QVBoxLayout) -> None:
        """Setup the file table with checkboxes."""
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Name", "Size", "Status"])
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self._colors.surface};
                border: none;
                gridline-color: {self._colors.border};
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QTableWidget::item {{
                padding: {SPACING.sm}px {SPACING.md}px;
            }}
            QHeaderView::section {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_secondary};
                border: none;
                border-bottom: 1px solid {self._colors.border};
                padding: {SPACING.sm}px {SPACING.md}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: {TYPOGRAPHY.weight_semibold};
            }}
        """)

        self._table.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self._table, 1)

    def _setup_footer(self, layout: QVBoxLayout) -> None:
        """Setup footer with cancel and pull buttons."""
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-top: 1px solid {self._colors.border};
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        footer_layout.addStretch()

        # Cancel
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._get_button_style())
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        # Pull Selected
        self._pull_btn = QPushButton("Pull Selected")
        self._pull_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pull_btn.setStyleSheet(self._get_primary_button_style())
        self._pull_btn.setEnabled(False)
        self._pull_btn.clicked.connect(self._on_pull_selected)
        footer_layout.addWidget(self._pull_btn)

        layout.addWidget(footer)

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_files(self) -> None:
        """Scan S3 and populate the table."""
        self._remote_files = self._viewmodel.scan()
        self._imported_names = self._viewmodel.get_imported_filenames()
        self._populate_table()

    def _populate_table(self) -> None:
        """Fill the table with remote files and status."""
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        self._table.setRowCount(len(self._remote_files))

        for row, rf in enumerate(self._remote_files):
            is_imported = rf.filename in self._imported_names

            # Name with checkbox
            name_item = QTableWidgetItem(rf.filename)
            if is_imported:
                name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # No checkbox
                name_item.setForeground(
                    Qt.GlobalColor.gray
                )
            else:
                name_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                name_item.setCheckState(Qt.CheckState.Unchecked)
            self._table.setItem(row, 0, name_item)

            # Size
            size_text = self._format_size(rf.size_bytes)
            size_item = QTableWidgetItem(size_text)
            size_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if is_imported:
                size_item.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(row, 1, size_item)

            # Status
            status_text = "imported" if is_imported else "remote"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            if is_imported:
                status_item.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(row, 2, status_item)

        self._table.blockSignals(False)
        self._update_pull_button()

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle checkbox state change."""
        if item.column() == 0:
            self._update_pull_button()

    def _update_pull_button(self) -> None:
        """Update pull button text and enabled state based on selection."""
        count = self._get_checked_count()
        if count > 0:
            self._pull_btn.setText(f"Pull {count} Selected")
            self._pull_btn.setEnabled(True)
        else:
            self._pull_btn.setText("Pull Selected")
            self._pull_btn.setEnabled(False)

    def _get_checked_count(self) -> int:
        """Count checked items."""
        count = 0
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        return count

    def _on_pull_selected(self) -> None:
        """Pull all checked files from S3 and auto-import."""
        keys_to_pull = []
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                keys_to_pull.append(self._remote_files[row].key)

        if not keys_to_pull:
            return

        self._pull_btn.setEnabled(False)
        self._pull_btn.setText("Pulling...")

        succeeded = 0
        failed = 0

        for key in keys_to_pull:
            result = self._viewmodel.pull_and_import(key, self._local_dir)
            if result.is_success:
                succeeded += 1
            else:
                failed += 1
                logger.warning("Failed to pull %s: %s", key, result.error)

        logger.info("Pull complete: %d succeeded, %d failed", succeeded, failed)

        # Refresh table to update status indicators
        self._load_files()

        if failed == 0:
            self.accept()

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _get_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
        """

    def _get_primary_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px {SPACING.lg}px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {self._colors.primary_light};
            }}
            QPushButton:disabled {{
                background-color: {self._colors.surface_light};
                color: {self._colors.text_disabled};
            }}
        """
