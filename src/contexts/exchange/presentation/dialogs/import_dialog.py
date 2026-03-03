"""
Import Dialog - Format selection and file selection for data import.

Usage:
    dialog = ImportDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        format = dialog.selected_format
        source_path = dialog.source_path
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

IMPORT_FORMATS = {
    "code_list": ("Code List (Text)", "*.txt"),
    "csv": ("Survey Data (CSV)", "*.csv"),
    "refi_qda": ("REFI-QDA Project (.qdpx)", "*.qdpx"),
    "rqda": ("RQDA Project (.rqda)", "*.rqda"),
}


@dataclass(frozen=True)
class ImportFormData:
    """Data from the import dialog."""

    format: str
    source_path: str
    name_column: str | None = None


class ImportDialog(QDialog):
    """Dialog for selecting import format and file."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._form_data: ImportFormData | None = None

        self.setWindowTitle("Import Data")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Format selection
        self._format_combo = QComboBox()
        for key, (label, _) in IMPORT_FORMATS.items():
            self._format_combo.addItem(label, key)
        form.addRow("Format:", self._format_combo)

        # Source path
        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select file to import...")
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self._path_edit)
        path_layout.addWidget(self._browse_btn)
        form.addRow("File:", path_layout)

        # CSV-specific: name column
        self._name_col_edit = QLineEdit()
        self._name_col_edit.setPlaceholderText("First column (default)")
        form.addRow("Case name column:", self._name_col_edit)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_browse(self) -> None:
        fmt_key = self._format_combo.currentData()
        _, ext = IMPORT_FORMATS.get(fmt_key, ("", "*.*"))

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Import File", "", f"Import Files ({ext});;All Files (*)"
        )
        if path:
            self._path_edit.setText(path)

    def _on_accept(self) -> None:
        path = self._path_edit.text().strip()
        if not path:
            return

        name_col = self._name_col_edit.text().strip() or None

        self._form_data = ImportFormData(
            format=self._format_combo.currentData(),
            source_path=path,
            name_column=name_col,
        )
        self.accept()

    @property
    def form_data(self) -> ImportFormData | None:
        return self._form_data
