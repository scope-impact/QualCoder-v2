"""
References Screen

The main reference management interface for QualCoder.
This screen wraps the ReferencesPage and implements the ScreenProtocol
for integration with AppShell.

Implements QC-041.02 View and Edit References:
- AC #1: I can see list of all references
- AC #2: I can edit reference metadata
- AC #3: I can delete references

Structure:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                              │
│ [Add Reference] [Import RIS] [Export]              [Search...      ] │
├─────────────────────────────────────────────────────────────────────┤
│ REFERENCES TABLE (or Empty State)                                    │
│ ☑ | Title                    | Authors    | Year | Actions          │
│ ─────────────────────────────────────────────────────────────────── │
│   | Logic of Scientific...   | Popper, K  | 1959 | [···]            │
│   | Qualitative Research...  | Smith, J   | 2020 | [···]            │
└─────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_colors

from ..dto import ReferenceDTO
from ..pages.references_page import ReferencesPage

if TYPE_CHECKING:
    from ..viewmodels.references_viewmodel import ReferencesViewModel


class ReferenceDialog(QDialog):
    """Dialog for creating or editing a reference."""

    def __init__(
        self,
        reference: ReferenceDTO | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._reference = reference

        self.setWindowTitle("Edit Reference" if reference else "Add Reference")
        self.setMinimumWidth(500)

        self._setup_ui()

        if reference:
            self._populate_fields()

    def _setup_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Reference title...")
        form.addRow("Title:", self._title_input)

        self._authors_input = QLineEdit()
        self._authors_input.setPlaceholderText("Author names (semicolon separated)...")
        form.addRow("Authors:", self._authors_input)

        self._year_input = QSpinBox()
        self._year_input.setRange(1000, 2100)
        self._year_input.setValue(2024)
        self._year_input.setSpecialValueText("Not set")
        form.addRow("Year:", self._year_input)

        self._source_input = QLineEdit()
        self._source_input.setPlaceholderText("Journal or publisher...")
        form.addRow("Source:", self._source_input)

        self._doi_input = QLineEdit()
        self._doi_input.setPlaceholderText("10.xxxx/xxxxx")
        form.addRow("DOI:", self._doi_input)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://...")
        form.addRow("URL:", self._url_input)

        self._memo_input = QTextEdit()
        self._memo_input.setPlaceholderText("Notes or abstract...")
        self._memo_input.setMaximumHeight(100)
        form.addRow("Notes:", self._memo_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_fields(self):
        """Populate fields with existing reference data."""
        if not self._reference:
            return

        self._title_input.setText(self._reference.title)
        self._authors_input.setText(self._reference.authors)
        if self._reference.year:
            self._year_input.setValue(self._reference.year)
        if self._reference.source:
            self._source_input.setText(self._reference.source)
        if self._reference.doi:
            self._doi_input.setText(self._reference.doi)
        if self._reference.url:
            self._url_input.setText(self._reference.url)
        if self._reference.memo:
            self._memo_input.setPlainText(self._reference.memo)

    def get_title(self) -> str:
        return self._title_input.text().strip()

    def get_authors(self) -> str:
        return self._authors_input.text().strip()

    def get_year(self) -> int | None:
        val = self._year_input.value()
        return val if val >= 1000 else None

    def get_source(self) -> str | None:
        text = self._source_input.text().strip()
        return text if text else None

    def get_doi(self) -> str | None:
        text = self._doi_input.text().strip()
        return text if text else None

    def get_url(self) -> str | None:
        text = self._url_input.text().strip()
        return text if text else None

    def get_memo(self) -> str | None:
        text = self._memo_input.toPlainText().strip()
        return text if text else None


class ReferencesScreen(QWidget):
    """
    Complete references management screen.

    Implements ScreenProtocol for use with AppShell.

    Signals:
        reference_selected(str): User selected a reference
        edit_reference(str): User wants to edit a reference
        delete_references(list): References were deleted
    """

    reference_selected = Signal(str)
    edit_reference = Signal(str)
    delete_references = Signal(list)

    def __init__(
        self,
        viewmodel: ReferencesViewModel | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the references screen.

        Args:
            viewmodel: Optional viewmodel for data and commands
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._viewmodel = viewmodel

        self._setup_ui()
        self._connect_signals()

        if self._viewmodel:
            self._load_data()

    def _setup_ui(self):
        """Build the screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._page = ReferencesPage(colors=self._colors)
        layout.addWidget(self._page)

    def _connect_signals(self):
        """Connect page signals to screen handlers."""
        self._page.add_reference_clicked.connect(self._on_add_reference_clicked)
        self._page.import_clicked.connect(self._on_import_clicked)
        self._page.export_clicked.connect(self._on_export_clicked)

        self._page.reference_clicked.connect(self._on_reference_clicked)
        self._page.reference_double_clicked.connect(self._on_reference_double_clicked)

        self._page.delete_references.connect(self._on_delete_references)
        self._page.edit_reference.connect(self._on_edit_reference)

        self._page.search_changed.connect(self._on_search_changed)

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_data(self):
        """Load data from viewmodel."""
        if not self._viewmodel:
            return

        refs = self._viewmodel.load_references()
        self._page.set_references(refs)

    def refresh(self):
        """Refresh data from viewmodel."""
        self._load_data()

    def set_viewmodel(self, viewmodel: ReferencesViewModel):
        """Set or replace the viewmodel."""
        self._viewmodel = viewmodel
        self._load_data()

    # =========================================================================
    # Toolbar Action Handlers
    # =========================================================================

    def _on_add_reference_clicked(self):
        """Handle add reference button click."""
        dialog = ReferenceDialog(colors=self._colors, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = dialog.get_title()
            authors = dialog.get_authors()

            if not title or not authors:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Title and authors are required.",
                )
                return

            if self._viewmodel:
                if self._viewmodel.add_reference(
                    title=title,
                    authors=authors,
                    year=dialog.get_year(),
                    source=dialog.get_source(),
                    doi=dialog.get_doi(),
                    url=dialog.get_url(),
                    memo=dialog.get_memo(),
                ):
                    self._load_data()
                else:
                    QMessageBox.warning(
                        self,
                        "Add Failed",
                        "Failed to add reference.",
                    )

    def _on_import_clicked(self):
        """Handle import RIS button click."""
        print("ReferencesScreen: Import RIS")

    def _on_export_clicked(self):
        """Handle export button click."""
        print("ReferencesScreen: Export references")

    # =========================================================================
    # Table Interaction Handlers
    # =========================================================================

    def _on_reference_clicked(self, reference_id: str):
        """Handle single click on a reference."""
        if self._viewmodel:
            self._viewmodel.select_reference(int(reference_id))
        self.reference_selected.emit(reference_id)

    def _on_reference_double_clicked(self, reference_id: str):
        """Handle double-click on a reference - open for editing."""
        self._on_edit_reference(reference_id)

    # =========================================================================
    # Reference Action Handlers
    # =========================================================================

    def _on_delete_references(self, reference_ids: list[str]):
        """Handle delete references request."""
        if not reference_ids:
            return

        count = len(reference_ids)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {count} reference(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._viewmodel:
            deleted = []
            for ref_id in reference_ids:
                if self._viewmodel.delete_reference(int(ref_id)):
                    deleted.append(ref_id)

            if deleted:
                self.delete_references.emit(deleted)
                self._load_data()

    def _on_edit_reference(self, reference_id: str):
        """Handle edit reference request."""
        self.edit_reference.emit(reference_id)

        if not self._viewmodel:
            return

        ref = self._viewmodel.get_reference(int(reference_id))
        if not ref:
            return

        dialog = ReferenceDialog(reference=ref, colors=self._colors, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if self._viewmodel.update_reference(
                reference_id=int(reference_id),
                title=dialog.get_title(),
                authors=dialog.get_authors(),
                year=dialog.get_year(),
                source=dialog.get_source(),
                doi=dialog.get_doi(),
                url=dialog.get_url(),
                memo=dialog.get_memo(),
            ):
                self._load_data()

    # =========================================================================
    # Search Handler
    # =========================================================================

    def _on_search_changed(self, query: str):
        """Handle search text change."""
        if not self._viewmodel:
            return

        if query:
            refs = self._viewmodel.search_references(query)
        else:
            refs = self._viewmodel.load_references()

        self._page.set_references(refs)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_references(self, references: list[ReferenceDTO]):
        """Set references directly (for use without viewmodel)."""
        self._page.set_references(references)

    def get_selected_ids(self) -> list[str]:
        """Get currently selected reference IDs."""
        return self._page.get_selected_ids()

    def clear_selection(self):
        """Clear all selections."""
        self._page.clear_selection()
        if self._viewmodel:
            self._viewmodel.clear_selection()

    @property
    def page(self) -> ReferencesPage:
        """Get the underlying page."""
        return self._page

    # =========================================================================
    # ScreenProtocol Implementation
    # =========================================================================

    def get_toolbar_content(self) -> QWidget | None:
        """Return None - toolbar is embedded in page."""
        return None

    def get_content(self) -> QWidget:
        """Return self as the content."""
        return self

    def get_status_message(self) -> str:
        """Return status bar message."""
        if self._viewmodel:
            refs = self._viewmodel.load_references()
            return f"{len(refs)} references"
        return "Ready"
