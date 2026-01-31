"""
Folder Dialog - Create and Rename Folders.

Implements QC-027.05 AC #1 (create folders) and AC #3 (rename folders).

Usage:
    dialog = FolderDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        folder_name = dialog.folder_name
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


# ============================================================
# Data Types
# ============================================================


@dataclass(frozen=True)
class FolderFormData:
    """Data from the folder dialog form."""

    name: str


# ============================================================
# Folder Dialog
# ============================================================


class FolderDialog(QDialog):
    """
    Dialog for creating or renaming a folder.

    Args:
        parent: Parent widget
        existing_name: Pre-fill name for rename operations
        title: Dialog title (default: "Create Folder")
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        existing_name: str = "",
        title: str = "Create Folder",
    ) -> None:
        super().__init__(parent)
        self._folder_name = ""

        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.setModal(True)

        self._setup_ui(existing_name)

    def _setup_ui(self, existing_name: str) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter folder name")
        self._name_input.setText(existing_name)
        self._name_input.textChanged.connect(self._validate_input)
        form_layout.addRow("Name:", self._name_input)

        layout.addLayout(form_layout)

        # Error label
        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: #dc3545;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

        # Initial validation
        self._validate_input()

    def _validate_input(self) -> None:
        """Validate the folder name input."""
        name = self._name_input.text().strip()
        ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)

        if not name:
            ok_button.setEnabled(False)
            self._error_label.setVisible(False)
        elif "/" in name or "\\" in name:
            ok_button.setEnabled(False)
            self._error_label.setText("Folder name cannot contain / or \\")
            self._error_label.setVisible(True)
        else:
            ok_button.setEnabled(True)
            self._error_label.setVisible(False)

    def _on_accept(self) -> None:
        """Handle accept action."""
        self._folder_name = self._name_input.text().strip()
        self.accept()

    @property
    def folder_name(self) -> str:
        """Get the entered folder name."""
        return self._folder_name

    @property
    def form_data(self) -> FolderFormData:
        """Get the form data as a frozen dataclass."""
        return FolderFormData(name=self._folder_name)


class RenameFolderDialog(FolderDialog):
    """
    Convenience subclass for renaming a folder.

    Pre-configures the dialog for rename operations.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        existing_name: str = "",
    ) -> None:
        super().__init__(
            parent=parent,
            existing_name=existing_name,
            title="Rename Folder",
        )
