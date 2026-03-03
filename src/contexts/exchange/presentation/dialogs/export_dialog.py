"""
Export Dialog - Format selection and options for data export.

Usage:
    dialog = ExportDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        format = dialog.selected_format
        output_path = dialog.output_path
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
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

EXPORT_FORMATS = {
    "codebook": ("Codebook (Text)", "*.txt"),
    "html": ("Coded Text (HTML)", "*.html"),
    "refi_qda": ("REFI-QDA Project (.qdpx)", "*.qdpx"),
}


@dataclass(frozen=True)
class ExportFormData:
    """Data from the export dialog."""

    format: str
    output_path: str
    include_memos: bool = True
    project_name: str = "QualCoder Project"


class ExportDialog(QDialog):
    """Dialog for selecting export format and options."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._form_data: ExportFormData | None = None

        self.setWindowTitle("Export Data")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Format selection
        self._format_combo = QComboBox()
        for key, (label, _) in EXPORT_FORMATS.items():
            self._format_combo.addItem(label, key)
        form.addRow("Format:", self._format_combo)

        # Output path
        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select output file...")
        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self._path_edit)
        path_layout.addWidget(self._browse_btn)
        form.addRow("Save to:", path_layout)

        # Options
        self._memos_check = QCheckBox("Include memos")
        self._memos_check.setChecked(True)
        form.addRow("", self._memos_check)

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
        _, ext = EXPORT_FORMATS.get(fmt_key, ("", "*.*"))

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Export", "", f"Export Files ({ext})"
        )
        if path:
            self._path_edit.setText(path)

    def _on_accept(self) -> None:
        path = self._path_edit.text().strip()
        if not path:
            return

        self._form_data = ExportFormData(
            format=self._format_combo.currentData(),
            output_path=path,
            include_memos=self._memos_check.isChecked(),
        )
        self.accept()

    @property
    def form_data(self) -> ExportFormData | None:
        return self._form_data
