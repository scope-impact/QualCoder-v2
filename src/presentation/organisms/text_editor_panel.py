"""
Text Editor Panel Organism

A panel for displaying and interacting with text documents for coding.
Shows the document content with header, stats, and selection capabilities.
"""

from typing import List, Optional, Tuple
from PyQt6.QtWidgets import QFrame, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from design_system import (
    ColorPalette, get_theme,
    TextPanel, SelectionPopup,
)


class TextEditorPanel(QFrame):
    """
    Panel for displaying and coding text content.

    Signals:
        text_selected(str, int, int): Emitted when text is selected (text, start, end)
        code_applied(str, int, int): Emitted when a code is applied to selection
    """

    text_selected = pyqtSignal(str, int, int)  # text, start, end
    code_applied = pyqtSignal(str, int, int)   # code_id, start, end

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the text editor panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_theme("dark")

        self.setStyleSheet(f"""
            TextEditorPanel {{
                background-color: {self._colors.background};
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Text panel with header
        self._text_panel = TextPanel(
            title="",
            badge_text=None,
            show_header=True,
            colors=self._colors,
        )
        self._text_panel.text_selected.connect(self.text_selected.emit)
        layout.addWidget(self._text_panel)

        # Selection popup (hidden by default)
        self._selection_popup = SelectionPopup(colors=self._colors)
        self._selection_popup.action_clicked.connect(self._on_popup_action)
        self._selection_popup.hide()

    def set_document(self, title: str, badge: str = None, text: str = ""):
        """
        Set the document to display.

        Args:
            title: Document title to show in header
            badge: Optional badge text (e.g., case ID)
            text: Document text content
        """
        self._text_panel.set_title(title)
        self._text_panel.set_text(text)

    def set_stats(self, stats: List[Tuple[str, str]]):
        """
        Update the stats display in the header.

        Args:
            stats: List of (icon_name, text) tuples
        """
        self._text_panel.set_stats(stats)

    def get_selection(self) -> Optional[Tuple[int, int]]:
        """
        Get the current text selection.

        Returns:
            Tuple of (start, end) positions or None if no selection
        """
        return self._text_panel.get_selection()

    def get_selected_text(self) -> str:
        """
        Get the currently selected text.

        Returns:
            Selected text string or empty string if no selection
        """
        cursor = self._text_panel._text_edit.textCursor()
        return cursor.selectedText() if cursor.hasSelection() else ""

    def highlight_range(self, start: int, end: int, color: str):
        """
        Highlight a range of text with a color.

        Args:
            start: Start position
            end: End position
            color: Highlight color
        """
        # TODO: Implement text highlighting
        pass

    def clear_highlights(self):
        """Clear all text highlights."""
        # TODO: Implement clearing highlights
        pass

    def _on_popup_action(self, action_id: str):
        """Handle selection popup action."""
        selection = self.get_selection()
        if selection:
            start, end = selection
            if action_id == "code":
                # TODO: Show code selection dialog
                pass
            elif action_id == "memo":
                # TODO: Show memo dialog
                pass
            print(f"Popup action: {action_id} on selection {start}-{end}")

    def scroll_to_position(self, position: int):
        """
        Scroll to a specific position in the text.

        Args:
            position: Character position to scroll to
        """
        cursor = self._text_panel._text_edit.textCursor()
        cursor.setPosition(position)
        self._text_panel._text_edit.setTextCursor(cursor)
        self._text_panel._text_edit.ensureCursorVisible()
