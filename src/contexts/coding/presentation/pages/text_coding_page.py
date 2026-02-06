"""
Text Coding Page

Composes the text coding organisms into a complete page layout.
This page can be used standalone for development or within a screen.

Layout:
┌─────────────────────────────────────────────────────────────┐
│ TOOLBAR (CodingToolbar)                                     │
├────────────┬─────────────────────────────┬──────────────────┤
│ LEFT       │     CENTER                  │   RIGHT          │
│ ┌────────┐ │  ┌─────────────────────┐    │ ┌──────────────┐ │
│ │ FILES  │ │  │ TextEditorPanel     │    │ │ DetailsPanel │ │
│ └────────┘ │  │                     │    │ │              │ │
│ ┌────────┐ │  │                     │    │ │              │ │
│ │ CODES  │ │  │                     │    │ │              │ │
│ │        │ │  │                     │    │ │              │ │
│ └────────┘ │  └─────────────────────┘    │ └──────────────┘ │
└────────────┴─────────────────────────────┴──────────────────┘
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from design_system import ColorPalette, get_colors
from src.shared.presentation.organisms import (
    CodesPanel,
    CodingToolbar,
    DetailsPanel,
    FilesPanel,
    TextEditorPanel,
)
from src.shared.presentation.templates import ThreePanelLayout


class TextCodingPage(QWidget):
    """
    Complete text coding page that composes all coding organisms.

    This page manages the layout and data flow between organisms.
    It can be used standalone for development or embedded in a screen.

    Signals:
        file_selected(dict): A file was selected
        code_selected(dict): A code was selected
        text_selected(str, int, int): Text was selected
        action_triggered(str): A toolbar action was triggered
        navigation_clicked(str): Navigation button clicked (prev/next)
        editor_code_applied(str, int, int): Code applied in editor
        ai_chat_clicked(): AI chat button clicked
        ai_suggest_clicked(): AI suggest button clicked
        media_type_changed(str): Media type filter changed
        search_changed(str): Search query changed
    """

    # Existing signals
    file_selected = Signal(dict)
    code_selected = Signal(dict)
    text_selected = Signal(str, int, int)
    action_triggered = Signal(str)

    # Signal routing (QC-007.05)
    navigation_clicked = Signal(str)  # prev/next
    editor_code_applied = Signal(str, int, int)  # code_id, start, end
    ai_chat_clicked = Signal()
    ai_suggest_clicked = Signal()
    media_type_changed = Signal(str)
    search_changed = Signal(str)

    def __init__(
        self,
        coders: list[str] = None,
        selected_coder: str = None,
        left_width: int = 280,
        right_width: int = 300,
        colors: ColorPalette = None,
        parent=None,
    ):
        """
        Initialize the text coding page.

        Args:
            coders: List of coder names for toolbar dropdown
            selected_coder: Initially selected coder
            left_width: Initial width of left panel
            right_width: Initial width of right panel
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._coders = coders or ["default"]
        self._selected_coder = selected_coder

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self._toolbar = CodingToolbar(
            coders=self._coders,
            selected_coder=self._selected_coder,
            colors=self._colors,
        )
        self._toolbar.action_triggered.connect(self.action_triggered.emit)
        self._toolbar.media_type_changed.connect(self.media_type_changed.emit)
        self._toolbar.search_changed.connect(self.search_changed.emit)
        self._toolbar.details_toggle_clicked.connect(self._toggle_details_panel)
        layout.addWidget(self._toolbar)

        # Main content - three panel layout
        self._layout = ThreePanelLayout(
            left_width=left_width,
            right_width=right_width,
            colors=self._colors,
        )

        # Left panel - Files + Codes (stacked)
        left_container = QFrame()
        left_container.setStyleSheet(f"background: {self._colors.transparent};")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._files_panel = FilesPanel(colors=self._colors)
        self._files_panel.setMaximumHeight(220)
        self._files_panel.file_selected.connect(self._on_file_selected)
        left_layout.addWidget(self._files_panel)

        self._codes_panel = CodesPanel(colors=self._colors)
        self._codes_panel.code_selected.connect(self._on_code_selected)
        self._codes_panel.navigation_clicked.connect(self.navigation_clicked.emit)
        left_layout.addWidget(self._codes_panel, 1)

        self._layout.set_left(left_container)

        # Center panel - Text editor
        self._editor_panel = TextEditorPanel(colors=self._colors)
        self._editor_panel.text_selected.connect(self._on_text_selected)
        self._editor_panel.code_applied.connect(self.editor_code_applied.emit)
        self._layout.set_center(self._editor_panel)

        # Right panel - Details
        self._details_panel = DetailsPanel(colors=self._colors)
        self._details_panel.ai_chat_clicked.connect(self.ai_chat_clicked.emit)
        self._details_panel.ai_suggest_clicked.connect(self.ai_suggest_clicked.emit)
        self._layout.set_right(self._details_panel)

        layout.addWidget(self._layout, 1)

    # =========================================================================
    # Public API - Data setters
    # =========================================================================

    def set_files(self, files: list[dict[str, Any]]):
        """
        Set the list of files to display.

        Args:
            files: List of file dictionaries
        """
        self._files_panel.set_files(files)

    def set_codes(self, categories: list[dict[str, Any]]):
        """
        Set the code tree data.

        Args:
            categories: List of category dictionaries with codes
        """
        self._codes_panel.set_codes(categories)

    def set_document(self, title: str, badge: str = None, text: str = ""):
        """
        Set the document to display in the editor.

        Args:
            title: Document title
            badge: Optional badge text
            text: Document content
        """
        self._editor_panel.set_document(title, badge, text)

    def set_document_stats(self, stats: list[tuple]):
        """
        Set the document stats display.

        Args:
            stats: List of (icon_name, text) tuples
        """
        self._editor_panel.set_stats(stats)

    def set_selected_code(self, color: str, name: str, memo: str, example: str = None):
        """
        Update the selected code details panel.

        Args:
            color: Code color
            name: Code name
            memo: Code description
            example: Optional example text
        """
        self._details_panel.set_selected_code(color, name, memo, example)

    def set_overlapping_codes(self, segments: list[tuple]):
        """
        Update the overlapping codes display.

        Args:
            segments: List of (segment_text, [colors]) tuples
        """
        self._details_panel.set_overlapping_codes(segments)

    def set_file_memo(self, memo: str, progress: int = 0):
        """
        Update the file memo display.

        Args:
            memo: Memo text
            progress: Coding progress percentage
        """
        self._details_panel.set_file_memo(memo, progress)

    def set_navigation(self, current: int, total: int):
        """
        Update the toolbar navigation display.

        Args:
            current: Current file index
            total: Total file count
        """
        self._toolbar.set_navigation(current, total)

    # =========================================================================
    # Public API - Accessors
    # =========================================================================

    @property
    def toolbar(self) -> CodingToolbar:
        """Get the toolbar organism."""
        return self._toolbar

    @property
    def files_panel(self) -> FilesPanel:
        """Get the files panel organism."""
        return self._files_panel

    @property
    def codes_panel(self) -> CodesPanel:
        """Get the codes panel organism."""
        return self._codes_panel

    @property
    def editor_panel(self) -> TextEditorPanel:
        """Get the text editor panel organism."""
        return self._editor_panel

    @property
    def details_panel(self) -> DetailsPanel:
        """Get the details panel organism."""
        return self._details_panel

    # =========================================================================
    # Internal signal handlers
    # =========================================================================

    def _on_file_selected(self, file_data: dict):
        """Handle file selection."""
        self.file_selected.emit(file_data)

    def _on_code_selected(self, code_data: dict):
        """Handle code selection."""
        self.code_selected.emit(code_data)

    def _on_text_selected(self, text: str, start: int, end: int):
        """Handle text selection."""
        self.text_selected.emit(text, start, end)

    def _toggle_details_panel(self):
        """Toggle visibility of the details panel."""
        is_visible = self._details_panel.isVisible()
        self._details_panel.setVisible(not is_visible)
        # Update toolbar button state
        self._toolbar.set_details_visible(not is_visible)


# =============================================================================
# DEMO
# =============================================================================


def main():
    """Run the text coding page demo."""
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    colors = get_colors()

    window = QMainWindow()
    window.setWindowTitle("Text Coding Page Demo")
    window.setMinimumSize(1400, 900)
    window.setStyleSheet(f"background-color: {colors.background};")

    # Create page
    page = TextCodingPage(
        coders=["colin", "sarah", "james"],
        selected_coder="colin",
        colors=colors,
    )

    # Load sample data
    page.set_files(
        [
            {
                "name": "Blur - Girls & Boys.mp3.transcribed",
                "type": "text",
                "meta": "Text • 2.4 KB • 3 codes",
            },
            {"name": "ID1.docx", "type": "text", "meta": "Text • 3.1 KB • 7 codes"},
            {"name": "ID2.odt", "type": "text", "meta": "Text • 1.2 KB • 5 codes"},
            {
                "name": "ID3_interview.txt",
                "type": "text",
                "meta": "Text • 8.5 KB • 12 codes",
            },
        ]
    )

    page.set_codes(
        [
            {
                "name": "Abilities",
                "codes": [
                    {"name": "soccer playing", "color": colors.code_yellow, "count": 3},
                    {"name": "struggling", "color": colors.code_red, "count": 5},
                    {"name": "tactics", "color": colors.code_purple, "count": 2},
                ],
            },
            {
                "name": "Opinion of Club",
                "codes": [
                    {
                        "name": "club development",
                        "color": colors.code_green,
                        "count": 4,
                    },
                    {"name": "facilities", "color": colors.code_blue, "count": 1},
                ],
            },
            {
                "name": "Motivation",
                "codes": [
                    {"name": "cost concerns", "color": colors.code_pink, "count": 2},
                    {
                        "name": "learning enthusiasm",
                        "color": colors.code_cyan,
                        "count": 6,
                    },
                    {"name": "time pressure", "color": colors.code_orange, "count": 3},
                ],
            },
        ]
    )

    sample_text = """I have not studied much before. I know that I must get help as I have struggled understanding the lecture slides so far and searching the web did not help.

I really want someone to sit down with me and explain the course material. The tutors seem helpful but there are not enough of them to go around.

The course cost €200.00 and I do not want to waste my money. I have to make the most of this opportunity.

I really like learning new things. I think this course is good for me as I have wanted to learn about world history for a while. The structured content, lecture slides and web links have been really good. I guess some less computer-savvy people would have some trouble accessing the internet-based material, but its like a duck to water for me – no problem at all.

I get the feeling most students are having some problems with the coursework deadlines. There is much to learn and not many of us practice directed learning. We need more guidance on time management and prioritization.

Overall, I am satisfied with the club's facilities and the quality of instruction. The new training ground has made a big difference. I feel like I am improving week by week, which keeps me motivated to continue."""

    page.set_document("ID2.odt", "Case: ID2", sample_text)
    page.set_document_stats(
        [
            ("mdi6.layers", "2 overlapping"),
            ("mdi6.label", "5 codes applied"),
            ("mdi6.format-size", "324 words"),
        ]
    )

    page.set_selected_code(
        colors.code_yellow,
        "soccer playing",
        "Code for references to playing soccer, including training, matches, and general participation in the sport.",
        "I have not studied much before...",
    )

    page.set_overlapping_codes(
        [
            ("Segment 1", [colors.code_green, colors.code_cyan]),
            ("Segment 2", [colors.code_red, colors.code_orange]),
        ]
    )

    page.set_file_memo(
        "Participant ID2 interview transcript. Student is positive about the "
        "course but expresses concerns about workload and cost.",
        65,
    )

    page.set_navigation(2, 5)

    window.setCentralWidget(page)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
