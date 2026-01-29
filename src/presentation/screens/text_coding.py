"""
Text Coding Screen

The main text coding interface for QualCoder.
This screen wraps the TextCodingPage and implements the ScreenProtocol
for integration with AppShell.

Structure:
┌─────────────────────────────────────────────────────────────┐
│ TOOLBAR                                                     │
│ [Text][Image][A/V][PDF] | Coder: [▼] | [icons...] | Search  │
├────────────┬─────────────────────────────────┬──────────────┤
│ LEFT PANEL │     CENTER PANEL                │  RIGHT PANEL │
│ ┌────────┐ │  ┌─────────────────────┐        │ ┌──────────┐ │
│ │ FILES  │ │  │ Editor Header       │        │ │ Selected │ │
│ └────────┘ │  │ ID2.odt [badge]     │        │ │ Code     │ │
│ ┌────────┐ │  ├─────────────────────┤        │ └──────────┘ │
│ │ CODES  │ │  │ Text content with   │        │ ┌──────────┐ │
│ │ tree   │ │  │ coded highlights    │        │ │ Overlaps │ │
│ └────────┘ │  └─────────────────────┘        │ └──────────┘ │
│ [nav btns] │                                 │              │
└────────────┴─────────────────────────────────┴──────────────┘
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from design_system import ColorPalette, get_theme

from ..pages import TextCodingPage
from ..organisms import CodingToolbar
from ..dto import TextCodingDataDTO
from ..sample_data import create_sample_text_coding_data


class TextCodingScreen(QWidget):
    """
    Complete text coding screen.

    Implements ScreenProtocol for use with AppShell.
    This screen wraps TextCodingPage and provides:
    - Sample data loading for demos
    - ScreenProtocol implementation
    - Application-level event handling

    Signals:
        file_selected(dict): A file was selected
        code_selected(dict): A code was selected
        text_selected(str, int, int): Text was selected
    """

    file_selected = pyqtSignal(dict)
    code_selected = pyqtSignal(dict)
    text_selected = pyqtSignal(str, int, int)

    def __init__(
        self,
        data: Optional[TextCodingDataDTO] = None,
        colors: ColorPalette = None,
        parent=None
    ):
        """
        Initialize the text coding screen.

        Args:
            data: Data to display (uses sample data if None)
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_theme("dark")
        self._data: Optional[TextCodingDataDTO] = None

        # Use provided data or sample data
        data = data or create_sample_text_coding_data()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the page
        self._page = TextCodingPage(
            coders=data.coders,
            selected_coder=data.selected_coder,
            colors=self._colors,
        )

        # Connect page signals
        self._page.file_selected.connect(self.file_selected.emit)
        self._page.code_selected.connect(self.code_selected.emit)
        self._page.text_selected.connect(self.text_selected.emit)
        self._page.action_triggered.connect(self._on_action)

        layout.addWidget(self._page)

        # Load the data
        self.load_data(data)

    def load_data(self, data: TextCodingDataDTO):
        """
        Load data into the screen.

        Args:
            data: The data transfer object containing all display data
        """
        self._data = data

        # Files - convert DTOs to dicts for Page
        files = [
            {"name": f.name, "type": f.file_type, "meta": f.meta}
            for f in data.files
        ]
        self._page.set_files(files)

        # Codes - convert DTOs to nested dicts for Page
        categories = [
            {
                "name": cat.name,
                "codes": [
                    {"name": c.name, "color": c.color, "count": c.count}
                    for c in cat.codes
                ]
            }
            for cat in data.categories
        ]
        self._page.set_codes(categories)

        # Document
        if data.document:
            self._page.set_document(
                data.document.title,
                data.document.badge,
                data.document.content
            )

        # Document stats
        if data.document_stats:
            stats = data.document_stats
            self._page.set_document_stats([
                ("mdi6.layers", f"{stats.overlapping_count} overlapping"),
                ("mdi6.label", f"{stats.codes_applied} codes applied"),
                ("mdi6.format-size", f"{stats.word_count} words"),
            ])

        # Selected code details
        if data.selected_code:
            sc = data.selected_code
            self._page.set_selected_code(sc.color, sc.name, sc.memo, sc.example_text)

        # Overlapping codes
        if data.overlapping_segments:
            overlaps = [
                (seg.segment_label, seg.colors)
                for seg in data.overlapping_segments
            ]
            self._page.set_overlapping_codes(overlaps)

        # File memo
        if data.file_memo:
            self._page.set_file_memo(data.file_memo.memo, data.file_memo.progress)

        # Navigation
        if data.navigation:
            self._page.set_navigation(data.navigation.current, data.navigation.total)

    def _on_action(self, action_id: str):
        """Handle toolbar action."""
        # Dispatch to specific handlers
        handlers = {
            "help": self._action_help,
            "text_size": self._action_text_size,
            "important": self._action_toggle_important,
            "annotations": self._action_toggle_annotations,
            "prev": self._action_prev_file,
            "next": self._action_next_file,
            "auto_exact": self._action_auto_exact,
            "auto_fragment": self._action_auto_fragment,
            "speakers": self._action_mark_speakers,
            "undo_auto": self._action_undo_auto,
            "memo": self._action_add_memo,
            "annotate": self._action_annotate,
        }

        handler = handlers.get(action_id)
        if handler:
            handler()
        else:
            print(f"Unknown action: {action_id}")

    # =========================================================================
    # Action Handlers
    # =========================================================================

    def _action_help(self):
        """Show help dialog."""
        print("TODO: Show help dialog")

    def _action_text_size(self):
        """Change text size."""
        print("TODO: Show text size options")

    def _action_toggle_important(self):
        """Toggle showing only important codes."""
        self._show_important_only = not getattr(self, '_show_important_only', False)
        print(f"Important only: {self._show_important_only}")

    def _action_toggle_annotations(self):
        """Toggle showing annotations."""
        self._show_annotations = not getattr(self, '_show_annotations', False)
        print(f"Show annotations: {self._show_annotations}")

    def _action_prev_file(self):
        """Navigate to previous file."""
        self._current_file_index = getattr(self, '_current_file_index', 0)
        if self._current_file_index > 0:
            self._current_file_index -= 1
            self._navigate_to_file(self._current_file_index)

    def _action_next_file(self):
        """Navigate to next file."""
        self._current_file_index = getattr(self, '_current_file_index', 0)
        total_files = len(self._page.files_panel._files)
        if self._current_file_index < total_files - 1:
            self._current_file_index += 1
            self._navigate_to_file(self._current_file_index)

    def _navigate_to_file(self, index: int):
        """Navigate to file at index and update navigation display."""
        files = self._page.files_panel._files
        if 0 <= index < len(files):
            file_data = files[index]
            self._page.set_navigation(index + 1, len(files))
            # Update document display
            self._page.set_document(
                file_data.get("name", ""),
                f"File {index + 1}",
                f"Content of {file_data.get('name', '')}...\n\n(Load actual content here)"
            )
            print(f"Navigated to file: {file_data.get('name')}")

    def _action_auto_exact(self):
        """Auto-code exact text matches."""
        selection = self._page.editor_panel.get_selected_text()
        if selection:
            print(f"TODO: Auto-code exact matches for: '{selection[:50]}...'")
        else:
            print("Select text first to auto-code")

    def _action_auto_fragment(self):
        """Auto-code similar text fragments."""
        selection = self._page.editor_panel.get_selected_text()
        if selection:
            print(f"TODO: Auto-code fragments similar to: '{selection[:50]}...'")
        else:
            print("Select text first to auto-code")

    def _action_mark_speakers(self):
        """Mark speaker turns in transcript."""
        print("TODO: Mark speaker turns")

    def _action_undo_auto(self):
        """Undo last auto-coding operation."""
        print("TODO: Undo last auto-code")

    def _action_add_memo(self):
        """Add memo to current selection or file."""
        selection = self._page.editor_panel.get_selected_text()
        if selection:
            print(f"TODO: Add memo to selection: '{selection[:50]}...'")
        else:
            print("TODO: Add memo to file")

    def _action_annotate(self):
        """Add annotation to current selection."""
        selection = self._page.editor_panel.get_selected_text()
        if selection:
            print(f"TODO: Annotate selection: '{selection[:50]}...'")
        else:
            print("Select text first to annotate")

    # =========================================================================
    # ScreenProtocol implementation
    # =========================================================================

    def get_toolbar_content(self) -> QWidget:
        """Return the coding toolbar (already part of page, return None)."""
        # The toolbar is already embedded in the page
        # Return None to indicate no separate toolbar needed
        return None

    def get_content(self) -> QWidget:
        """Return self as the content."""
        return self

    def get_status_message(self) -> str:
        """Return status bar message."""
        return "Ready"

    # =========================================================================
    # Public API - Delegate to page
    # =========================================================================

    def set_files(self, files: List[Dict[str, Any]]):
        """Set the list of files."""
        self._page.set_files(files)

    def set_codes(self, categories: List[Dict[str, Any]]):
        """Set the code tree."""
        self._page.set_codes(categories)

    def set_document(self, title: str, badge: str = None, text: str = ""):
        """Set the document."""
        self._page.set_document(title, badge, text)

    @property
    def page(self) -> TextCodingPage:
        """Get the underlying page."""
        return self._page


# =============================================================================
# DEMO
# =============================================================================

def main():
    """Run the text coding screen demo."""
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_theme("dark")

    window = QMainWindow()
    window.setWindowTitle("Text Coding Screen")
    window.setMinimumSize(1400, 900)
    window.setStyleSheet(f"background-color: {colors.background};")

    screen = TextCodingScreen(colors=colors)
    window.setCentralWidget(screen)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
