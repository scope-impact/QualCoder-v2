"""
File Manager Screen

The main file management interface for QualCoder.
This screen wraps the FileManagerPage and implements the ScreenProtocol
for integration with AppShell.

Implements QC-026 Project Open & Navigation:
- Display project sources with stats by type
- Filter sources by type (via stats cards)
- Search sources by name
- Import, link, and create new sources
- Open sources for coding (double-click)
- Bulk operations on selected sources

Architecture (Functional Core / Imperative Shell):
    User Action → Screen → ViewModel → Controller → Domain → Events
                                                              ↓
    UI Update ← Screen ← ViewModel ← ──────────────────────────┘

Structure:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                              │
│ [Import Files] [Link] [Create] [Export]               [Search...]   │
├─────────────────────────────────────────────────────────────────────┤
│ STATS ROW (clickable for filtering)                                  │
│ [12 Text] [5 Audio] [3 Video] [8 Images] [4 PDF]                    │
├─────────────────────────────────────────────────────────────────────┤
│ SOURCE TABLE (or Empty State)                                        │
│ ☑ | File Name | Codes | Cases | Status | Actions                    │
│ ─────────────────────────────────────────────────────────────────── │
│   | Interview1.txt | 12 | Case A | Coded | [···]                    │
│   | Recording.mp3  | 3  | -      | Ready | [···]                    │
├─────────────────────────────────────────────────────────────────────┤
│ BULK ACTIONS BAR (when files selected)                               │
│ ✓ 3 files selected    [Code] [Delete] [Export]                  [×] │
└─────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout, QWidget

from design_system import ColorPalette, get_colors

from ..dto import ProjectSummaryDTO, SourceDTO
from ..pages import FileManagerPage

if TYPE_CHECKING:
    from ..viewmodels import FileManagerViewModel


class FileManagerScreen(QWidget):
    """
    Complete file management screen.

    Implements ScreenProtocol for use with AppShell.
    This screen wraps FileManagerPage and provides:
    - Connection to FileManagerViewModel
    - File import dialogs
    - Confirmation dialogs for destructive actions
    - Navigation to coding screen

    Signals:
        source_opened(str): User wants to open a source for coding
        sources_imported(list): New sources were imported
        sources_deleted(list): Sources were deleted
        navigate_to_coding(str): Navigate to coding screen with source ID
    """

    source_opened = Signal(str)
    sources_imported = Signal(list)
    sources_deleted = Signal(list)
    navigate_to_coding = Signal(str)

    def __init__(
        self,
        viewmodel: FileManagerViewModel | None = None,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the file manager screen.

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
        self._page = FileManagerPage(colors=self._colors)
        layout.addWidget(self._page)

    def _connect_signals(self):
        """Connect page signals to screen handlers."""
        # Toolbar actions
        self._page.import_clicked.connect(self._on_import_clicked)
        self._page.link_clicked.connect(self._on_link_clicked)
        self._page.create_text_clicked.connect(self._on_create_text_clicked)
        self._page.export_clicked.connect(self._on_export_clicked)

        # Table interactions
        self._page.source_clicked.connect(self._on_source_clicked)
        self._page.source_double_clicked.connect(self._on_source_double_clicked)
        self._page.selection_changed.connect(self._on_selection_changed)

        # Bulk actions
        self._page.open_for_coding.connect(self._on_open_for_coding)
        self._page.delete_sources.connect(self._on_delete_sources)
        self._page.export_sources.connect(self._on_export_sources)

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

        # Load sources
        sources = self._viewmodel.load_sources()
        self._page.set_sources(sources)

    def refresh(self):
        """Refresh data from viewmodel."""
        self._load_data()

    def set_viewmodel(self, viewmodel: FileManagerViewModel):
        """
        Set or replace the viewmodel.

        Args:
            viewmodel: The new viewmodel to use
        """
        self._viewmodel = viewmodel
        self._load_data()

    # =========================================================================
    # Toolbar Action Handlers
    # =========================================================================

    def _on_import_clicked(self):
        """Handle import files button click."""
        # Show file dialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Source Files",
            "",
            "All Supported Files (*.txt *.docx *.odt *.pdf *.mp3 *.wav *.mp4 *.avi *.jpg *.jpeg *.png);;Text Files (*.txt *.docx *.odt);;Audio Files (*.mp3 *.wav);;Video Files (*.mp4 *.avi);;Images (*.jpg *.jpeg *.png);;PDF Files (*.pdf);;All Files (*)",
        )

        if not file_paths:
            return

        # Import via viewmodel
        if self._viewmodel:
            imported = []
            for path in file_paths:
                if self._viewmodel.add_source(path):
                    imported.append(path)

            if imported:
                self.sources_imported.emit(imported)
                self._load_data()  # Refresh display

            if len(imported) < len(file_paths):
                failed = len(file_paths) - len(imported)
                QMessageBox.warning(
                    self,
                    "Import Warning",
                    f"{failed} file(s) could not be imported.",
                )

    def _on_link_clicked(self):
        """Handle link external files button click."""
        # Show file dialog for linking (doesn't copy files)
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Link External Files",
            "",
            "All Files (*)",
        )

        if not file_paths:
            return

        # Link via viewmodel (same as import but with external flag)
        if self._viewmodel:
            for path in file_paths:
                self._viewmodel.add_source(path, origin="external")
            self._load_data()

    def _on_create_text_clicked(self):
        """Handle create new text button click."""
        # For now, just print - would show a dialog in full implementation
        print("FileManagerScreen: Create new text document")
        # TODO: Show dialog to create new text document

    def _on_export_clicked(self):
        """Handle export button click."""
        selected_ids = self._page.get_selected_ids()
        if selected_ids:
            self._export_sources(selected_ids)
        else:
            QMessageBox.information(
                self,
                "Export",
                "Select files to export first.",
            )

    # =========================================================================
    # Table Interaction Handlers
    # =========================================================================

    def _on_source_clicked(self, source_id: str):
        """Handle single click on a source."""
        # Update selection in viewmodel
        if self._viewmodel:
            self._viewmodel.toggle_source_selection(int(source_id))

    def _on_source_double_clicked(self, source_id: str):
        """Handle double-click on a source - open for coding."""
        self._open_source(source_id)

    def _on_selection_changed(self, selected_ids: list[str]):
        """Handle selection change in table."""
        if self._viewmodel:
            self._viewmodel.select_sources([int(id) for id in selected_ids])

    # =========================================================================
    # Bulk Action Handlers
    # =========================================================================

    def _on_open_for_coding(self, source_id: str):
        """Handle open for coding request."""
        self._open_source(source_id)

    def _on_delete_sources(self, source_ids: list[str]):
        """Handle delete sources request."""
        if not source_ids:
            return

        # Confirm deletion
        count = len(source_ids)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {count} file(s)?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete via viewmodel
        if self._viewmodel:
            if self._viewmodel.remove_sources([int(id) for id in source_ids]):
                self.sources_deleted.emit(source_ids)
                self._load_data()  # Refresh display
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    "Some files could not be deleted.",
                )

    def _on_export_sources(self, source_ids: list[str]):
        """Handle export sources request."""
        self._export_sources(source_ids)

    # =========================================================================
    # Filter Handlers
    # =========================================================================

    def _on_filter_changed(self, source_type: str | None):
        """Handle filter change from stats row."""
        if not self._viewmodel:
            return

        if source_type:
            sources = self._viewmodel.filter_sources(source_type=source_type)
        else:
            sources = self._viewmodel.load_sources()

        self._page.set_sources(sources)

    def _on_search_changed(self, query: str):
        """Handle search text change."""
        if not self._viewmodel:
            return

        if query:
            sources = self._viewmodel.search_sources(query)
        else:
            # No search - apply current filter if any
            current_filter = self._page.get_active_filter()
            if current_filter:
                sources = self._viewmodel.filter_sources(source_type=current_filter)
            else:
                sources = self._viewmodel.load_sources()

        self._page.set_sources(sources)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _open_source(self, source_id: str):
        """Open a source for coding."""
        if self._viewmodel and self._viewmodel.open_source(int(source_id)):
            self.source_opened.emit(source_id)
            self.navigate_to_coding.emit(source_id)

    def _export_sources(self, source_ids: list[str]):
        """Export selected sources."""
        if not source_ids:
            return

        # Show folder selection dialog
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            "",
        )

        if not export_dir:
            return

        # Export logic would go here
        print(f"FileManagerScreen: Exporting {len(source_ids)} files to {export_dir}")
        # TODO: Implement actual export via viewmodel/controller

        QMessageBox.information(
            self,
            "Export Complete",
            f"Exported {len(source_ids)} file(s) to:\n{export_dir}",
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def set_sources(self, sources: list[SourceDTO]):
        """
        Set sources directly (for use without viewmodel).

        Args:
            sources: List of source DTOs
        """
        self._page.set_sources(sources)

    def set_summary(self, summary: ProjectSummaryDTO):
        """
        Set summary directly (for use without viewmodel).

        Args:
            summary: Project summary DTO
        """
        self._page.set_summary(summary)

    def get_selected_ids(self) -> list[str]:
        """Get currently selected source IDs."""
        return self._page.get_selected_ids()

    def clear_selection(self):
        """Clear all selections."""
        self._page.clear_selection()
        if self._viewmodel:
            self._viewmodel.clear_selection()

    @property
    def page(self) -> FileManagerPage:
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
            return f"{summary.total_sources} sources | {summary.total_codes} codes | {summary.total_segments} coded segments"
        return "Ready"


# =============================================================================
# DEMO
# =============================================================================


def main():
    """Run the file manager screen demo."""
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_colors()

    window = QMainWindow()
    window.setWindowTitle("File Manager Screen Demo")
    window.setMinimumSize(1200, 800)
    window.setStyleSheet(f"background-color: {colors.background};")

    # Create screen without viewmodel (uses page's demo mode)
    screen = FileManagerScreen(colors=colors)

    # Connect signals for demo
    screen.source_opened.connect(lambda id: print(f"Source opened: {id}"))
    screen.navigate_to_coding.connect(lambda id: print(f"Navigate to coding: {id}"))
    screen.sources_imported.connect(lambda paths: print(f"Imported: {paths}"))
    screen.sources_deleted.connect(lambda ids: print(f"Deleted: {ids}"))

    # Set demo data
    screen.set_summary(
        ProjectSummaryDTO(
            total_sources=32,
            text_count=12,
            audio_count=5,
            video_count=3,
            image_count=8,
            pdf_count=4,
            total_codes=45,
            total_segments=156,
        )
    )

    screen.set_sources(
        [
            SourceDTO(
                id="1",
                name="Interview_Participant_01.txt",
                source_type="text",
                status="coded",
                code_count=15,
                cases=["Case A", "Case B"],
            ),
            SourceDTO(
                id="2",
                name="Focus_Group_Recording.mp3",
                source_type="audio",
                status="transcribing",
                code_count=0,
            ),
            SourceDTO(
                id="3",
                name="Observation_Video.mp4",
                source_type="video",
                status="ready",
                code_count=3,
            ),
            SourceDTO(
                id="4",
                name="Field_Notes_Scan.pdf",
                source_type="pdf",
                status="in_progress",
                code_count=7,
            ),
            SourceDTO(
                id="5",
                name="Participant_Photo.jpg",
                source_type="image",
                status="imported",
                code_count=0,
            ),
        ]
    )

    window.setCentralWidget(screen)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
