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

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QVBoxLayout,
    QWidget,
)

from design_system import ColorPalette, get_colors
from src.shared.presentation.dto import ProjectSummaryDTO, SourceDTO

from ..pages import FileManagerPage

logger = logging.getLogger("qualcoder.sources.presentation")

if TYPE_CHECKING:
    from src.contexts.exchange.presentation.viewmodels.exchange_viewmodel import (
        ExchangeViewModel,
    )

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
        self._exchange_vm: ExchangeViewModel | None = None

        self._setup_ui()
        self._connect_signals()

        # Load initial data if viewmodel provided
        if self._viewmodel:
            self._load_all()

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
        self._page.view_metadata.connect(self._on_view_metadata)

        # Filtering
        self._page.filter_changed.connect(self._on_filter_changed)
        self._page.search_changed.connect(self._on_search_changed)

        # Folder actions
        self._page.folder_selected.connect(self._on_folder_selected)
        self._page.create_folder_requested.connect(self._on_create_folder)
        self._page.rename_folder_requested.connect(self._on_rename_folder)
        self._page.delete_folder_requested.connect(self._on_delete_folder)
        self._page.move_sources_to_folder.connect(self._on_move_sources_to_folder)

        # Exchange actions
        self._page.import_code_list.connect(self._on_import_code_list)
        self._page.import_csv.connect(self._on_import_csv)
        self._page.import_refi_qda.connect(self._on_import_refi_qda)
        self._page.import_rqda.connect(self._on_import_rqda)
        self._page.export_codebook.connect(self._on_export_codebook)
        self._page.export_html.connect(self._on_export_html)
        self._page.export_refi_qda.connect(self._on_export_refi_qda)

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_data(self):
        """Reload sources and summary from viewmodel.

        Folders are loaded separately via ``_load_folders`` (triggered by
        ``folders_changed`` signal).  Keeping them separate avoids
        redundant DB queries — source add/remove doesn't change folders.
        """
        if not self._viewmodel:
            return

        # Load summary stats
        summary = self._viewmodel.get_summary()
        self._page.set_summary(summary)

        # Load sources
        sources = self._viewmodel.load_sources()
        self._page.set_sources(sources)

    def _load_all(self):
        """Full reload of sources, summary, and folders.

        Used on initial load and viewmodel replacement.
        """
        self._load_data()
        self._load_folders()

    def refresh(self):
        """Refresh data from viewmodel."""
        self._load_all()

    def set_viewmodel(self, viewmodel: FileManagerViewModel):
        """
        Set or replace the viewmodel.

        Args:
            viewmodel: The new viewmodel to use
        """
        # Disconnect previous viewmodel signals if any
        if self._viewmodel is not None:
            self._viewmodel.teardown()
            self._disconnect_viewmodel_signals()

        self._viewmodel = viewmodel
        self._connect_viewmodel_signals()
        self._load_all()

    def _connect_viewmodel_signals(self) -> None:
        """Connect to viewmodel signals for reactive UI updates (e.g. MCP-triggered changes)."""
        if self._viewmodel is None:
            return

        self._viewmodel.sources_changed.connect(self._load_data)
        self._viewmodel.summary_changed.connect(self._refresh_summary)
        self._viewmodel.folders_changed.connect(self._load_folders)

    def _disconnect_viewmodel_signals(self) -> None:
        """Disconnect from previous viewmodel signals."""
        if self._viewmodel is None:
            return

        self._viewmodel.sources_changed.disconnect(self._load_data)
        self._viewmodel.summary_changed.disconnect(self._refresh_summary)
        self._viewmodel.folders_changed.disconnect(self._load_folders)

    def _refresh_summary(self) -> None:
        """Refresh only the summary stats from viewmodel."""
        if self._viewmodel:
            summary = self._viewmodel.get_summary()
            self._page.set_summary(summary)

    # =========================================================================
    # Toolbar Action Handlers
    # =========================================================================

    def _on_import_clicked(self):
        """Handle import files button click.

        Uses a background worker for extraction so the UI stays responsive.
        A modal QProgressDialog shows per-file progress and supports cancel.
        """
        # Show file dialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Source Files",
            "",
            "All Supported Files (*.txt *.docx *.odt *.pdf *.mp3 *.wav *.mp4 *.avi *.jpg *.jpeg *.png *.heic *.heif);;Text Files (*.txt *.docx *.odt);;Audio Files (*.mp3 *.wav);;Video Files (*.mp4 *.avi);;Images (*.jpg *.jpeg *.png *.heic *.heif);;PDF Files (*.pdf);;All Files (*)",
        )

        if not file_paths:
            return

        if not self._viewmodel:
            return

        total = len(file_paths)
        logger.info("_on_import_clicked: user selected %d file(s)", total)

        # --- Set up progress dialog ---
        self._import_progress = QProgressDialog(
            f"Importing 0/{total} files...",
            "Cancel",
            0,
            total,
            self,
        )
        self._import_progress.setWindowTitle("Importing Files")
        self._import_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._import_progress.setMinimumDuration(0)  # show immediately
        self._import_progress.canceled.connect(self._on_import_canceled)

        # --- Connect batch signals ---
        self._viewmodel.batch_import_progress.connect(self._on_batch_progress)
        self._viewmodel.batch_import_finished.connect(self._on_batch_finished)

        # --- Start background import ---
        self._viewmodel.import_sources_batch(file_paths)

    def _on_import_canceled(self):
        """User clicked Cancel on the progress dialog."""
        logger.info("_on_import_canceled: user requested cancel")
        if self._viewmodel:
            self._viewmodel.cancel_import()

    def _on_batch_progress(self, current: int, total: int, filename: str):
        """Update progress dialog as files are processed."""
        if hasattr(self, "_import_progress") and self._import_progress:
            self._import_progress.setLabelText(
                f"Importing {current}/{total} — {filename}"
            )
            self._import_progress.setValue(current)

    def _on_batch_finished(self, imported: int, failed: int):
        """Handle batch import completion."""
        logger.info(
            "_on_batch_finished: %d imported, %d failed", imported, failed
        )

        # Clean up progress dialog
        if hasattr(self, "_import_progress") and self._import_progress:
            self._import_progress.close()
            self._import_progress = None

        # Disconnect batch signals
        if self._viewmodel:
            self._viewmodel.batch_import_progress.disconnect(self._on_batch_progress)
            self._viewmodel.batch_import_finished.disconnect(self._on_batch_finished)

        # No explicit _load_data() — _on_batch_done already emits
        # sources_changed which triggers _load_data via signal connection.

        if imported:
            self.sources_imported.emit([])  # exact paths not tracked; signal observers

        if failed > 0:
            QMessageBox.warning(
                self,
                "Import Warning",
                f"{failed} file(s) could not be imported.\nSee log for details.",
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

        # Link via viewmodel (same as import but with external flag).
        # Suppress per-file reloads; context manager emits single
        # sources_changed on exit → screen._load_data runs once.
        if self._viewmodel:
            total = len(file_paths)
            logger.info("_on_link_clicked: linking %d file(s)", total)
            linked = 0
            with self._viewmodel.suppress_reloads():
                for i, path in enumerate(file_paths):
                    logger.debug(
                        "_on_link_clicked: [%d/%d] %s", i + 1, total, path
                    )
                    if self._viewmodel.add_source(path, origin="external"):
                        linked += 1
            logger.info("_on_link_clicked: linked %d/%d", linked, total)

    def _on_create_text_clicked(self):
        """Handle create new text button click."""
        # For now, just print - would show a dialog in full implementation
        logger.debug("FileManagerScreen: Create new text document")
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
            self._viewmodel.toggle_source_selection(source_id)

    def _on_source_double_clicked(self, source_id: str):
        """Handle double-click on a source - open for coding."""
        self._open_source(source_id)

    def _on_selection_changed(self, selected_ids: list[str]):
        """Handle selection change in table."""
        if self._viewmodel:
            self._viewmodel.select_sources(selected_ids)

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

        # Delete via viewmodel — suppress_reloads inside remove_sources
        # emits sources_changed once → _load_data runs via signal connection
        if self._viewmodel:
            if self._viewmodel.remove_sources(source_ids):
                self.sources_deleted.emit(source_ids)
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    "Some files could not be deleted.",
                )

    def _on_export_sources(self, source_ids: list[str]):
        """Handle export sources request."""
        self._export_sources(source_ids)

    def _on_view_metadata(self, source_id: str):
        """Handle view metadata request - show metadata dialog."""
        from ..dialogs.source_metadata_dialog import (
            SourceMetadata,
            SourceMetadataDialog,
        )

        # Get source info from viewmodel
        if self._viewmodel:
            source = self._viewmodel.get_source(source_id)
            if source:
                metadata = SourceMetadata(
                    id=source.id,
                    name=source.name,
                    source_type=source.source_type,
                    status=source.status,
                    file_size=source.file_size or 0,
                    code_count=source.code_count or 0,
                    memo=source.memo,
                    origin=source.origin,
                )
                dialog = SourceMetadataDialog(metadata, self._colors, self)
                dialog.save_clicked.connect(
                    lambda m: self._save_source_metadata(source_id, m)
                )
                dialog.exec()

    def _save_source_metadata(self, source_id: str, metadata):
        """Save updated source metadata."""
        if self._viewmodel:
            self._viewmodel.update_source(
                source_id,
                memo=metadata.memo,
                origin=metadata.origin,
            )
            self._load_data()

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
    # Folder Action Handlers
    # =========================================================================

    def _on_folder_selected(self, folder_node):
        """Handle folder selection in tree."""
        # Could filter sources by folder here
        pass

    def _on_create_folder(self, parent_id):
        """Handle create folder request."""
        if not self._viewmodel:
            return

        # Show input dialog for folder name
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self,
            "Create Folder",
            "Folder name:",
        )

        if ok and name and self._viewmodel.create_folder(name, parent_id or None):
            self._load_folders()

    def _on_rename_folder(self, folder_id: str):
        """Handle rename folder request."""
        if not self._viewmodel:
            return

        from PySide6.QtWidgets import QInputDialog

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "New folder name:",
        )

        if ok and new_name and self._viewmodel.rename_folder(folder_id, new_name):
            self._load_folders()

    def _on_delete_folder(self, folder_id: str):
        """Handle delete folder request."""
        if not self._viewmodel:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this folder?\n\nNote: Only empty folders can be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._viewmodel.delete_folder(folder_id):
                self._load_folders()
            else:
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    "Could not delete folder. Make sure it is empty.",
                )

    def _on_move_sources_to_folder(self, source_ids: list[str], folder_id):
        """Handle moving sources to a folder."""
        if not self._viewmodel:
            return

        folder_id_str = str(folder_id) if folder_id is not None else None
        success = True
        with self._viewmodel.suppress_reloads():
            for source_id in source_ids:
                if not self._viewmodel.move_source_to_folder(source_id, folder_id_str):
                    success = False
        # suppress_reloads emits sources_changed on exit → _load_data
        if not success:
            QMessageBox.warning(
                self,
                "Move Failed",
                "Some sources could not be moved.",
            )

    def _load_folders(self):
        """Load folders from viewmodel and update tree."""
        if self._viewmodel:
            folders = self._viewmodel.get_folders()
            self._page.set_folders(folders)

    # =========================================================================
    # Exchange ViewModel
    # =========================================================================

    def set_exchange_viewmodel(self, exchange_vm: ExchangeViewModel) -> None:
        """Set the exchange viewmodel for import/export operations."""
        self._exchange_vm = exchange_vm

    # =========================================================================
    # Exchange Import/Export Handlers
    # =========================================================================

    def _do_exchange_import(
        self, title: str, file_filter: str, vm_method: str, success_msg: str
    ) -> None:
        """Shared logic for all exchange import operations."""
        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if not path or not self._exchange_vm:
            return
        if getattr(self._exchange_vm, vm_method)(path):
            QMessageBox.information(self, "Import", success_msg)
            self._load_data()
        else:
            QMessageBox.warning(
                self, "Import Failed", self._exchange_vm.last_error or "Unknown error."
            )

    def _do_exchange_export(
        self, title: str, default_name: str, file_filter: str, vm_method: str
    ) -> None:
        """Shared logic for all exchange export operations."""
        path, _ = QFileDialog.getSaveFileName(self, title, default_name, file_filter)
        if not path or not self._exchange_vm:
            return
        if getattr(self._exchange_vm, vm_method)(path):
            QMessageBox.information(self, "Export", f"Exported to:\n{path}")
        else:
            QMessageBox.warning(
                self, "Export Failed", self._exchange_vm.last_error or "Unknown error."
            )

    def _on_import_code_list(self) -> None:
        self._do_exchange_import(
            "Import Code List",
            "Text Files (*.txt);;All Files (*)",
            "import_code_list",
            "Code list imported successfully.",
        )

    def _on_import_csv(self) -> None:
        self._do_exchange_import(
            "Import Survey CSV",
            "CSV Files (*.csv);;All Files (*)",
            "import_survey_csv",
            "Survey data imported successfully.",
        )

    def _on_import_refi_qda(self) -> None:
        self._do_exchange_import(
            "Import REFI-QDA Project",
            "REFI-QDA Files (*.qdpx);;All Files (*)",
            "import_refi_qda",
            "REFI-QDA project imported successfully.",
        )

    def _on_import_rqda(self) -> None:
        self._do_exchange_import(
            "Import RQDA Project",
            "RQDA Files (*.rqda);;All Files (*)",
            "import_rqda",
            "RQDA project imported successfully.",
        )

    def _on_export_codebook(self) -> None:
        self._do_exchange_export(
            "Export Codebook", "codebook.txt", "Text Files (*.txt)", "export_codebook"
        )

    def _on_export_html(self) -> None:
        self._do_exchange_export(
            "Export Coded HTML",
            "coded_text.html",
            "HTML Files (*.html)",
            "export_coded_html",
        )

    def _on_export_refi_qda(self) -> None:
        self._do_exchange_export(
            "Export REFI-QDA Project",
            "project.qdpx",
            "REFI-QDA Files (*.qdpx)",
            "export_refi_qda",
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _open_source(self, source_id: str):
        """Open a source for coding."""
        if self._viewmodel and self._viewmodel.open_source(source_id):
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
        logger.debug(
            "FileManagerScreen: Exporting %d files to %s", len(source_ids), export_dir
        )
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
