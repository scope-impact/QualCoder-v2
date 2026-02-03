"""
Line Number Gutter Molecule

A widget that displays line numbers in the left margin of a text editor.
Pure presentation component - receives line count, displays numbered labels.

This is a stateless display component that can be synchronized with any
text editor by calling set_line_count() when the document changes.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
)


class LineNumberGutter(QWidget):
    """
    Line number gutter widget for text editors.

    Displays line numbers in the left margin, synchronized with the text editor.
    This is a pure presentation molecule - it doesn't know about the text content,
    only the line count.

    Example:
        gutter = LineNumberGutter()
        gutter.set_line_count(100)

        # Sync with text editor
        text_edit.textChanged.connect(
            lambda: gutter.set_line_count(text_edit.document().blockCount())
        )
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._line_count = 1
        self._line_height = 22  # Approximate line height in pixels

        self._setup_ui()

    def _setup_ui(self):
        """Build the gutter UI."""
        self.setFixedWidth(50)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors.surface_light};
                border-right: 1px solid {self._colors.border};
            }}
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, SPACING.xl, 0, SPACING.xl)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._labels: list[QLabel] = []

    # =========================================================================
    # Public API
    # =========================================================================

    def set_line_count(self, count: int):
        """
        Update the number of lines displayed.

        Args:
            count: Number of lines to display (minimum 1)
        """
        self._line_count = max(1, count)

        # Add labels as needed (lazy creation for performance)
        while len(self._labels) < self._line_count:
            label = self._create_line_label(len(self._labels) + 1)
            self._labels.append(label)
            self._layout.addWidget(label)

        # Show/hide labels based on count
        for i, label in enumerate(self._labels):
            label.setVisible(i < self._line_count)

    def get_line_count(self) -> int:
        """Get the current line count."""
        return self._line_count

    def set_line_height(self, height: int):
        """
        Set the height of each line number label.

        Args:
            height: Height in pixels (should match text editor line height)
        """
        self._line_height = height
        for label in self._labels:
            label.setFixedHeight(height)

    def get_line_height(self) -> int:
        """Get the current line height."""
        return self._line_height

    # =========================================================================
    # Internal
    # =========================================================================

    def _create_line_label(self, line_number: int) -> QLabel:
        """Create a styled label for a line number."""
        label = QLabel(str(line_number))
        label.setStyleSheet(f"""
            color: {self._colors.text_disabled};
            font-family: {TYPOGRAPHY.font_family_mono};
            font-size: {TYPOGRAPHY.text_sm}px;
            padding-right: {SPACING.sm}px;
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(self._line_height)
        return label
