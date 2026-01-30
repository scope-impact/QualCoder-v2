"""
Files Panel Organism

A panel displaying the list of files available for coding.
Includes a header with filter and memo actions, and a scrollable file list.
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from design_system import (
    ColorPalette,
    FileList,
    PanelHeader,
    get_colors,
)


class FilesPanel(QFrame):
    """
    Panel showing list of files to code.

    Signals:
        file_selected(dict): Emitted when a file is selected, with file data
    """

    file_selected = Signal(dict)

    def __init__(self, colors: ColorPalette = None, parent=None):
        """
        Initialize the files panel.

        Args:
            colors: Color palette to use
            parent: Parent widget
        """
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._files: list[dict[str, Any]] = []
        self._selected_index: int = -1

        self.setStyleSheet(f"background: {self._colors.transparent}; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = PanelHeader("Files", icon="mdi6.folder-open", colors=self._colors)
        header.add_action("mdi6.filter-variant", tooltip="Filter files")
        header.add_action("mdi6.note", tooltip="File memo")
        layout.addWidget(header)

        # File list
        self._file_list = FileList(colors=self._colors)
        self._file_list.item_clicked.connect(self._on_file_click)
        layout.addWidget(self._file_list)

    def set_files(self, files: list[dict[str, Any]]):
        """
        Set the list of files to display.

        Args:
            files: List of file dictionaries with keys:
                - name: File name
                - type: File type (text, image, av, pdf)
                - meta: Additional metadata string
                - selected (optional): Whether the file is selected
        """
        self._files = files if files else []
        self._selected_index = -1
        self._file_list.clear()

        for i, f in enumerate(self._files):
            if not isinstance(f, dict):
                continue
            self._file_list.add_file(
                id=str(i),
                name=f.get("name", ""),
                file_type=f.get("type", "text"),
                size=f.get("meta", ""),
            )

        # Auto-select first file if available
        if self._files:
            self._selected_index = 0

    def _on_file_click(self, file_id: str):
        """Handle file click event."""
        try:
            index = int(file_id)
            if 0 <= index < len(self._files):
                self._selected_index = index
                self.file_selected.emit(self._files[index])
        except (ValueError, TypeError) as e:
            # Log error for debugging but don't crash
            print(f"FilesPanel: Invalid file_id '{file_id}': {e}")

    def get_selected_file(self) -> dict[str, Any]:
        """Get the currently selected file data."""
        if 0 <= self._selected_index < len(self._files):
            return self._files[self._selected_index].copy()
        return {}

    def get_selected_index(self) -> int:
        """Get the index of the currently selected file."""
        return self._selected_index

    def select_file(self, index: int) -> bool:
        """
        Select a file by index.

        Args:
            index: The file index to select

        Returns:
            True if selection was successful, False otherwise
        """
        if 0 <= index < len(self._files):
            self._selected_index = index
            return True
        return False

    def get_file_count(self) -> int:
        """Get the total number of files."""
        return len(self._files)

    def clear(self):
        """Clear all files from the list."""
        self._files = []
        self._file_list.clear()
