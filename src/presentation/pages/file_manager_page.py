"""
File Manager Page

Composes the File Manager organisms into a complete page layout.
This page can be used standalone for development or within a screen.

Layout:
┌─────────────────────────────────────────────────────────────────────┐
│ TOOLBAR (FileManagerToolbar)                                         │
│ [Import Files] [Link] [Create] [Export]               [Search...  ] │
├─────────────────────────────────────────────────────────────────────┤
│ STATS ROW (SourceStatsRow) - clickable to filter                     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │  Text   │ │  Audio  │ │  Video  │ │ Images  │ │   PDF   │        │
│ │   12    │ │    5    │ │    3    │ │    8    │ │    4    │        │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────────────────┤
│ TABLE (SourceTable) - or EmptyState if no files                      │
│ ┌───┬──────────────────┬───────┬────────┬──────────┬─────────────┐ │
│ │ ☑ │ File Name        │ Codes │ Cases  │ Status   │ Actions     │ │
│ ├───┼──────────────────┼───────┼────────┼──────────┼─────────────┤ │
│ │   │ Interview1.txt   │  12   │ Case A │ Coded    │ [···]       │ │
│ │   │ Recording.mp3    │   3   │ -      │ Ready    │ [···]       │ │
│ └───┴──────────────────┴───────┴────────┴──────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ BULK ACTIONS BAR (shown when files selected)                         │
│ ✓ 3 files selected    [Code] [Delete] [Export]                  [×] │
└─────────────────────────────────────────────────────────────────────┘

Addresses UX Tech Debt items:
- UX-002: Empty state with clear CTA
- UX-003: Stats cards are clickable filters
- UX-004: Double-click opens for coding
- UX-005: Bulk actions when files selected
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QStackedWidget, QVBoxLayout, QWidget

from design_system import ColorPalette, get_colors
from design_system.tokens import SPACING

from ..dto import ProjectSummaryDTO, SourceDTO
from ..organisms import (
    EmptyState,
    FileManagerToolbar,
    SourceStatsRow,
    SourceTable,
)


class FileManagerPage(QWidget):
    """
    Complete File Manager page that composes all related organisms.

    This page manages the layout and data flow between organisms.
    It can be used standalone for development or embedded in a screen.

    Signals:
        import_clicked: User clicked import files
        link_clicked: User clicked link external files
        create_text_clicked: User clicked create new text
        export_clicked: User clicked export
        source_double_clicked(str): User double-clicked a source to open
        source_clicked(str): User single-clicked a source
        selection_changed(list): Selected source IDs changed
        delete_sources(list): User wants to delete selected sources
        export_sources(list): User wants to export selected sources
        open_for_coding(str): User wants to open a source for coding
        filter_changed(str | None): Type filter changed (None = show all)
        search_changed(str): Search text changed
    """

    # Toolbar actions
    import_clicked = Signal()
    link_clicked = Signal()
    create_text_clicked = Signal()
    export_clicked = Signal()

    # Table interactions
    source_clicked = Signal(str)
    source_double_clicked = Signal(str)
    selection_changed = Signal(list)

    # Bulk actions
    delete_sources = Signal(list)
    export_sources = Signal(list)
    open_for_coding = Signal(str)

    # Filtering
    filter_changed = Signal(object)  # str | None
    search_changed = Signal(str)

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the File Manager page.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._current_filter: str | None = None
        self._current_search: str = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the page layout."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.background};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.lg, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.lg)

        # Toolbar
        self._toolbar = FileManagerToolbar(colors=self._colors)
        layout.addWidget(self._toolbar)

        # Stats row
        self._stats_row = SourceStatsRow(colors=self._colors)
        layout.addWidget(self._stats_row)

        # Content area: either table or empty state
        self._content_stack = QStackedWidget()

        # Empty state
        self._empty_state = EmptyState(colors=self._colors)
        self._content_stack.addWidget(self._empty_state)

        # Table container
        self._table_container = QFrame()
        self._table_container.setStyleSheet("background: transparent;")
        table_layout = QVBoxLayout(self._table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self._source_table = SourceTable(colors=self._colors)
        table_layout.addWidget(self._source_table)

        self._content_stack.addWidget(self._table_container)

        layout.addWidget(self._content_stack, 1)

        # Start with empty state
        self._content_stack.setCurrentWidget(self._empty_state)

    def _connect_signals(self):
        """Connect internal signals."""
        # Toolbar signals
        self._toolbar.import_clicked.connect(self.import_clicked.emit)
        self._toolbar.link_clicked.connect(self.link_clicked.emit)
        self._toolbar.create_text_clicked.connect(self.create_text_clicked.emit)
        self._toolbar.export_clicked.connect(self.export_clicked.emit)
        self._toolbar.search_changed.connect(self._on_search_changed)

        # Stats row signals
        self._stats_row.filter_changed.connect(self._on_filter_changed)

        # Table signals
        self._source_table.source_clicked.connect(self.source_clicked.emit)
        self._source_table.source_double_clicked.connect(
            self.source_double_clicked.emit
        )
        self._source_table.selection_changed.connect(self._on_selection_changed)
        self._source_table.open_for_coding.connect(self.open_for_coding.emit)
        self._source_table.delete_sources.connect(self.delete_sources.emit)
        self._source_table.export_sources.connect(self.export_sources.emit)

        # Empty state signals
        self._empty_state.import_clicked.connect(self.import_clicked.emit)
        self._empty_state.link_clicked.connect(self.link_clicked.emit)

    # =========================================================================
    # Public API - Data Setters
    # =========================================================================

    def set_sources(self, sources: list[SourceDTO]):
        """
        Set the list of sources to display.

        Automatically switches between empty state and table view.

        Args:
            sources: List of SourceDTO objects
        """
        if not sources:
            self._content_stack.setCurrentWidget(self._empty_state)
        else:
            self._source_table.set_sources(sources)
            self._content_stack.setCurrentWidget(self._table_container)

    def set_summary(self, summary: ProjectSummaryDTO):
        """
        Set the project summary statistics.

        Args:
            summary: ProjectSummaryDTO with counts by type
        """
        self._stats_row.set_counts(
            text_count=summary.text_count,
            audio_count=summary.audio_count,
            video_count=summary.video_count,
            image_count=summary.image_count,
            pdf_count=summary.pdf_count,
        )

    def set_stats(
        self,
        text_count: int = 0,
        audio_count: int = 0,
        video_count: int = 0,
        image_count: int = 0,
        pdf_count: int = 0,
    ):
        """
        Set individual stat counts.

        Args:
            text_count: Number of text files
            audio_count: Number of audio files
            video_count: Number of video files
            image_count: Number of image files
            pdf_count: Number of PDF files
        """
        self._stats_row.set_counts(
            text_count=text_count,
            audio_count=audio_count,
            video_count=video_count,
            image_count=image_count,
            pdf_count=pdf_count,
        )

    # =========================================================================
    # Public API - State
    # =========================================================================

    def get_selected_ids(self) -> list[str]:
        """Get list of selected source IDs."""
        return self._source_table.get_selected_ids()

    def clear_selection(self):
        """Clear all selections."""
        self._source_table.clear_selection()

    def clear_filter(self):
        """Clear the type filter."""
        self._stats_row.clear_filter()
        self._current_filter = None

    def clear_search(self):
        """Clear the search box."""
        self._toolbar.clear_search()
        self._current_search = ""

    def get_active_filter(self) -> str | None:
        """Get the currently active type filter."""
        return self._current_filter

    def get_search_text(self) -> str:
        """Get the current search text."""
        return self._current_search

    # =========================================================================
    # Public API - Accessors
    # =========================================================================

    @property
    def toolbar(self) -> FileManagerToolbar:
        """Get the toolbar organism."""
        return self._toolbar

    @property
    def stats_row(self) -> SourceStatsRow:
        """Get the stats row organism."""
        return self._stats_row

    @property
    def source_table(self) -> SourceTable:
        """Get the source table organism."""
        return self._source_table

    @property
    def empty_state(self) -> EmptyState:
        """Get the empty state organism."""
        return self._empty_state

    # =========================================================================
    # Internal Signal Handlers
    # =========================================================================

    def _on_filter_changed(self, source_type: str | None):
        """Handle filter change from stats row."""
        self._current_filter = source_type
        self.filter_changed.emit(source_type)

    def _on_search_changed(self, text: str):
        """Handle search change from toolbar."""
        self._current_search = text
        self.search_changed.emit(text)

    def _on_selection_changed(self, selected_ids: list[str]):
        """Handle selection change from table."""
        self.selection_changed.emit(selected_ids)


# =============================================================================
# DEMO
# =============================================================================


def main():
    """Run the File Manager page demo."""
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_colors()

    window = QMainWindow()
    window.setWindowTitle("File Manager Page Demo")
    window.setMinimumSize(1200, 800)
    window.setStyleSheet(f"background-color: {colors.background};")

    # Create page
    page = FileManagerPage(colors=colors)

    # Connect signals for demo
    page.import_clicked.connect(lambda: print("Import clicked"))
    page.source_double_clicked.connect(lambda id: print(f"Double-clicked: {id}"))
    page.selection_changed.connect(lambda ids: print(f"Selected: {ids}"))
    page.filter_changed.connect(lambda f: print(f"Filter: {f}"))
    page.search_changed.connect(lambda s: print(f"Search: {s}"))

    # Set stats
    page.set_stats(
        text_count=12,
        audio_count=5,
        video_count=3,
        image_count=8,
        pdf_count=4,
    )

    # Sample sources
    sources = [
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
        SourceDTO(
            id="6",
            name="Interview_Participant_02.docx",
            source_type="text",
            status="coded",
            code_count=22,
            cases=["Case A"],
        ),
        SourceDTO(
            id="7",
            name="Meeting_Recording.wav",
            source_type="audio",
            status="ready",
            code_count=5,
        ),
    ]

    page.set_sources(sources)

    window.setCentralWidget(page)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
