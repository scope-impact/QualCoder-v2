"""
Case Manager Screen

The main case management interface for QualCoder.
This screen wraps the CaseManagerPage and implements the ScreenProtocol
for integration with AppShell.

Implements QC-034 Manage Cases:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Architecture (Functional Core / Imperative Shell):
    User Action → Screen → ViewModel → Repository → Domain → Events
                                                              ↓
    UI Update ← Screen ← ViewModel ← ──────────────────────────┘

Structure:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                              │
│ [Create Case] [Import] [Export]                     [Search...     ] │
├─────────────────────────────────────────────────────────────────────┤
│ STATS ROW (clickable for filtering)                                  │
│ [12 Total Cases] [8 With Sources] [25 Attributes]                   │
├─────────────────────────────────────────────────────────────────────┤
│ CASE TABLE (or Empty State)                                          │
│ ☑ | Case Name        | Sources | Attributes | Actions               │
│ ─────────────────────────────────────────────────────────────────── │
│   | Participant A    |    3    |     5      | [···]                 │
│   | Site Alpha       |    0    |     2      | [···]                 │
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_colors
from src.shared.presentation.dto import CaseDTO, CaseSummaryDTO

from ..pages import CaseManagerPage

if TYPE_CHECKING:
    from ..viewmodels import CaseManagerViewModel


class CreateCaseDialog(QDialog):
    """Dialog for creating a new case."""

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self.setWindowTitle("Create New Case")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Enter case name...")
        form.addRow("Name:", self._name_input)

        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText("Optional description...")
        self._description_input.setMaximumHeight(100)
        form.addRow("Description:", self._description_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_name(self) -> str:
        """Get the entered name."""
        return self._name_input.text().strip()

    def get_description(self) -> str | None:
        """Get the entered description."""
        text = self._description_input.toPlainText().strip()
        return text if text else None


class CaseManagerScreen(QWidget):
    """
    Complete case management screen.

    Implements ScreenProtocol for use with AppShell.
    This screen wraps CaseManagerPage and provides:
    - Connection to CaseManagerViewModel
    - Create case dialog
    - Confirmation dialogs for destructive actions
    - Navigation to case details

    Signals:
        case_opened(str): User wants to view case details
        case_created(str): A new case was created
        cases_deleted(list): Cases were deleted
        navigate_to_case(str): Navigate to case details with case ID
    """

    case_opened = Signal(str)
    case_created = Signal(str)
    cases_deleted = Signal(list)
    navigate_to_case = Signal(str)

    def __init__(
        self,
        viewmodel: CaseManagerViewModel | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the case manager screen.

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

        # Load initial data if viewmodel provided
        if self._viewmodel:
            self._load_data()

    def _setup_ui(self):
        """Build the screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the page
        self._page = CaseManagerPage(colors=self._colors)
        layout.addWidget(self._page)

    def _connect_signals(self):
        """Connect page signals to screen handlers."""
        # Toolbar actions
        self._page.create_case_clicked.connect(self._on_create_case_clicked)
        self._page.import_clicked.connect(self._on_import_clicked)
        self._page.export_clicked.connect(self._on_export_clicked)

        # Table interactions
        self._page.case_clicked.connect(self._on_case_clicked)
        self._page.case_double_clicked.connect(self._on_case_double_clicked)
        self._page.selection_changed.connect(self._on_selection_changed)

        # Case actions
        self._page.delete_cases.connect(self._on_delete_cases)
        self._page.link_source.connect(self._on_link_source)
        self._page.edit_case.connect(self._on_edit_case)

        # Filtering
        self._page.filter_changed.connect(self._on_filter_changed)
        self._page.search_changed.connect(self._on_search_changed)

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_data(self):
        """Load data from viewmodel."""
        if not self._viewmodel:
            return

        # Load summary stats
        summary = self._viewmodel.get_summary()
        self._page.set_summary(summary)

        # Load cases
        cases = self._viewmodel.load_cases()
        self._page.set_cases(cases)

    def refresh(self):
        """Refresh data from viewmodel."""
        self._load_data()

    def set_viewmodel(self, viewmodel: CaseManagerViewModel):
        """
        Set or replace the viewmodel.

        Args:
            viewmodel: The new viewmodel to use
        """
        # Disconnect previous viewmodel signals if any
        if self._viewmodel is not None:
            self._disconnect_viewmodel_signals()

        self._viewmodel = viewmodel
        self._connect_viewmodel_signals()
        self._load_data()

    def _connect_viewmodel_signals(self) -> None:
        """Connect to viewmodel signals for reactive UI updates (e.g. MCP-triggered changes)."""
        if self._viewmodel is None:
            return

        self._viewmodel.cases_changed.connect(self._load_data)
        self._viewmodel.summary_changed.connect(self._refresh_summary)

    def _disconnect_viewmodel_signals(self) -> None:
        """Disconnect from previous viewmodel signals."""
        if self._viewmodel is None:
            return

        self._viewmodel.cases_changed.disconnect(self._load_data)
        self._viewmodel.summary_changed.disconnect(self._refresh_summary)

    def _refresh_summary(self) -> None:
        """Refresh only the summary stats from viewmodel."""
        if self._viewmodel:
            summary = self._viewmodel.get_summary()
            self._page.set_summary(summary)

    # =========================================================================
    # Toolbar Action Handlers
    # =========================================================================

    def _on_create_case_clicked(self):
        """Handle create case button click."""
        dialog = CreateCaseDialog(colors=self._colors, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            description = dialog.get_description()

            if not name:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Case name cannot be empty.",
                )
                return

            # Create via viewmodel
            if self._viewmodel:
                if self._viewmodel.create_case(name, description):
                    # Find the new case ID
                    cases = self._viewmodel.load_cases()
                    for case in cases:
                        if case.name == name:
                            self.case_created.emit(case.id)
                            break
                    self._load_data()  # Refresh display
                else:
                    QMessageBox.warning(
                        self,
                        "Create Failed",
                        f"A case with name '{name}' already exists.",
                    )
            else:
                # Demo mode - just emit signal
                self.case_created.emit("new")

    def _on_import_clicked(self):
        """Handle import cases button click."""
        # TODO: Show import dialog
        print("CaseManagerScreen: Import cases")

    def _on_export_clicked(self):
        """Handle export button click."""
        selected_ids = self._page.get_selected_ids()
        if selected_ids:
            # TODO: Export selected cases
            print(f"CaseManagerScreen: Export {len(selected_ids)} cases")
        else:
            QMessageBox.information(
                self,
                "Export",
                "Select cases to export first.",
            )

    # =========================================================================
    # Table Interaction Handlers
    # =========================================================================

    def _on_case_clicked(self, case_id: str):
        """Handle single click on a case."""
        if self._viewmodel:
            self._viewmodel.select_case(int(case_id))

    def _on_case_double_clicked(self, case_id: str):
        """Handle double-click on a case - open for details."""
        self.case_opened.emit(case_id)
        self.navigate_to_case.emit(case_id)

    def _on_selection_changed(self, selected_ids: list[str]):
        """Handle selection change in table."""
        # Selection is managed by the table itself
        pass

    # =========================================================================
    # Case Action Handlers
    # =========================================================================

    def _on_delete_cases(self, case_ids: list[str]):
        """Handle delete cases request."""
        if not case_ids:
            return

        # Confirm deletion
        count = len(case_ids)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {count} case(s)?\n\n"
            "This will unlink all associated sources but not delete them.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete via viewmodel
        if self._viewmodel:
            deleted = []
            for case_id in case_ids:
                if self._viewmodel.delete_case(int(case_id)):
                    deleted.append(case_id)

            if deleted:
                self.cases_deleted.emit(deleted)
                self._load_data()  # Refresh display

            if len(deleted) < len(case_ids):
                QMessageBox.warning(
                    self,
                    "Delete Warning",
                    "Some cases could not be deleted.",
                )

    def _on_link_source(self, case_id: str):
        """Handle link source to case request."""
        # TODO: Show source selection dialog
        print(f"CaseManagerScreen: Link source to case {case_id}")

    def _on_edit_case(self, case_id: str):
        """Handle edit case request."""
        # TODO: Show edit case dialog
        print(f"CaseManagerScreen: Edit case {case_id}")

    # =========================================================================
    # Filter Handlers
    # =========================================================================

    def _on_filter_changed(self, filter_type: str | None):
        """Handle filter change from stats row."""
        if not self._viewmodel:
            return

        # Reload all cases - filtering would be applied here
        cases = self._viewmodel.load_cases()

        # Apply filter (if any)
        if filter_type == "with_sources":
            cases = [c for c in cases if c.source_count > 0]
        elif filter_type == "has_attributes":
            cases = [c for c in cases if c.attributes]

        self._page.set_cases(cases)

    def _on_search_changed(self, query: str):
        """Handle search text change."""
        if not self._viewmodel:
            return

        if query:
            cases = self._viewmodel.search_cases(query)
        else:
            # No search - apply current filter if any
            current_filter = self._page.get_active_filter()
            cases = self._viewmodel.load_cases()

            if current_filter == "with_sources":
                cases = [c for c in cases if c.source_count > 0]
            elif current_filter == "has_attributes":
                cases = [c for c in cases if c.attributes]

        self._page.set_cases(cases)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_cases(self, cases: list[CaseDTO]):
        """
        Set cases directly (for use without viewmodel).

        Args:
            cases: List of case DTOs
        """
        self._page.set_cases(cases)

    def set_summary(self, summary: CaseSummaryDTO):
        """
        Set summary directly (for use without viewmodel).

        Args:
            summary: Case summary DTO
        """
        self._page.set_summary(summary)

    def get_selected_ids(self) -> list[str]:
        """Get currently selected case IDs."""
        return self._page.get_selected_ids()

    def clear_selection(self):
        """Clear all selections."""
        self._page.clear_selection()
        if self._viewmodel:
            self._viewmodel.clear_selection()

    @property
    def page(self) -> CaseManagerPage:
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
            summary = self._viewmodel.get_summary()
            return f"{summary.total_cases} cases | {summary.cases_with_sources} with sources | {summary.total_attributes} attributes"
        return "Ready"


# =============================================================================
# DEMO
# =============================================================================


def main():
    """Run the case manager screen demo."""
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_colors()

    window = QMainWindow()
    window.setWindowTitle("Case Manager Screen Demo")
    window.setMinimumSize(1200, 800)
    window.setStyleSheet(f"background-color: {colors.background};")

    # Create screen without viewmodel (uses page's demo mode)
    screen = CaseManagerScreen(colors=colors)

    # Connect signals for demo
    screen.case_opened.connect(lambda id: print(f"Case opened: {id}"))
    screen.navigate_to_case.connect(lambda id: print(f"Navigate to case: {id}"))
    screen.case_created.connect(lambda id: print(f"Case created: {id}"))
    screen.cases_deleted.connect(lambda ids: print(f"Deleted: {ids}"))

    # Set demo data
    screen.set_summary(
        CaseSummaryDTO(
            total_cases=3,
            cases_with_sources=2,
            total_attributes=5,
            unique_attribute_names=["age", "gender", "location"],
        )
    )

    screen.set_cases(
        [
            CaseDTO(
                id="1",
                name="Participant A",
                description="First participant in the study",
                source_count=3,
                attributes=[
                    {"name": "age", "attr_type": "number", "value": 25},
                    {"name": "gender", "attr_type": "text", "value": "female"},
                ],
            ),
            CaseDTO(
                id="2",
                name="Participant B",
                description="Second participant",
                source_count=5,
                attributes=[
                    {"name": "age", "attr_type": "number", "value": 30},
                ],
            ),
            CaseDTO(
                id="3",
                name="Site Alpha",
                description="Research site location",
                source_count=0,
                attributes=[],
            ),
        ]
    )

    window.setCentralWidget(screen)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
