"""
Files Panel Organism

A panel displaying the list of files available for coding.
Includes a header with filter and memo actions, and a scrollable file list.
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt, Signal

from design_system import (
    ColorPalette, get_theme, SPACING, RADIUS, TYPOGRAPHY,
    Icon, FileList,
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
        self._colors = colors or get_theme("dark")
        self._files = []

        self.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header("Files", "mdi6.folder-open", [
            ("mdi6.filter-variant", "Filter files"),
            ("mdi6.note", "File memo"),
        ])
        layout.addWidget(header)

        # File list
        self._file_list = FileList(colors=self._colors)
        self._file_list.item_clicked.connect(self._on_file_click)
        layout.addWidget(self._file_list)

    def _create_header(self, title: str, icon_name: str, actions: List[tuple]) -> QFrame:
        """Create a panel header with icon and actions."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors.surface_light};
                border-bottom: 1px solid {self._colors.border};
            }}
        """)

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        h_layout.setSpacing(SPACING.sm)

        # Icon
        icon = Icon(icon_name, size=16, color=self._colors.primary, colors=self._colors)
        h_layout.addWidget(icon)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            color: {self._colors.text_primary};
        """)
        h_layout.addWidget(title_label)
        h_layout.addStretch()

        # Actions
        for action_icon, tooltip in actions:
            btn = QFrame()
            btn.setFixedSize(24, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: {RADIUS.xs}px;
                }}
                QFrame:hover {{
                    background-color: {self._colors.surface_lighter};
                }}
            """)
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            action_i = Icon(action_icon, size=14, color=self._colors.text_secondary, colors=self._colors)
            btn_layout.addWidget(action_i, alignment=Qt.AlignmentFlag.AlignCenter)
            h_layout.addWidget(btn)

        return header

    def set_files(self, files: List[Dict[str, Any]]):
        """
        Set the list of files to display.

        Args:
            files: List of file dictionaries with keys:
                - name: File name
                - type: File type (text, image, av, pdf)
                - meta: Additional metadata string
                - selected (optional): Whether the file is selected
        """
        self._files = files
        self._file_list.clear()
        for i, f in enumerate(files):
            self._file_list.add_file(
                id=str(i),
                name=f.get("name", ""),
                file_type=f.get("type", "text"),
                size=f.get("meta", ""),
            )

    def _on_file_click(self, file_id: str):
        """Handle file click event."""
        try:
            index = int(file_id)
            if 0 <= index < len(self._files):
                self.file_selected.emit(self._files[index])
        except ValueError:
            pass

    def get_selected_file(self) -> Dict[str, Any]:
        """Get the currently selected file data."""
        # TODO: Implement selection tracking in FileList
        return self._files[0] if self._files else {}

    def clear(self):
        """Clear all files from the list."""
        self._files = []
        self._file_list.clear()
