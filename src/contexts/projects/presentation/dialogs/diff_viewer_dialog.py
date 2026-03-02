"""
Diff Viewer Dialog

Displays the diff between two VCS snapshots.

Implements QC-048.07 Diff Viewer Dialog:
- AC #4: See what changed between two points in time
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
    get_pixmap,
)


class DiffHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for git diff output.

    Uses design system colors for theme support (git-cola inspired).
    """

    def __init__(self, colors: ColorPalette, document: QTextDocument):
        super().__init__(document)
        self._colors = colors

        # Define formats using design system colors
        self._add_format = QTextCharFormat()
        self._add_format.setBackground(QColor(colors.diff_add_bg))
        self._add_format.setForeground(QColor(colors.diff_add_fg))

        self._remove_format = QTextCharFormat()
        self._remove_format.setBackground(QColor(colors.diff_remove_bg))
        self._remove_format.setForeground(QColor(colors.diff_remove_fg))

        self._header_format = QTextCharFormat()
        self._header_format.setForeground(QColor(colors.diff_header_fg))
        self._header_format.setFontWeight(QFont.Weight.Bold)

        self._hunk_format = QTextCharFormat()
        self._hunk_format.setForeground(QColor(colors.diff_hunk_fg))

    def highlightBlock(self, text: str):
        """Apply highlighting to a block of text."""
        if text.startswith("+") and not text.startswith("+++"):
            self.setFormat(0, len(text), self._add_format)
        elif text.startswith("-") and not text.startswith("---"):
            self.setFormat(0, len(text), self._remove_format)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self._hunk_format)
        elif (
            text.startswith("diff ")
            or text.startswith("index ")
            or text.startswith("---")
            or text.startswith("+++")
        ):
            self.setFormat(0, len(text), self._header_format)


class DiffViewerDialog(QDialog):
    """
    Dialog for viewing diff between two VCS snapshots.

    Shows a syntax-highlighted diff with additions and deletions.
    """

    def __init__(
        self,
        from_ref: str,
        to_ref: str,
        diff_content: str,
        colors: ColorPalette = None,
        parent=None,
    ):
        super().__init__(parent)
        self._from_ref = from_ref
        self._to_ref = to_ref
        self._diff_content = diff_content
        self._colors = colors or get_colors()

        self.setWindowTitle("View Changes")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {self._colors.background};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Header
        header = QHBoxLayout()
        header.setSpacing(SPACING.md)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("mdi6.file-compare", size=24))
        header.addWidget(icon_label)

        title = QLabel("Changes Between Snapshots")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_xl}px;
            font-weight: 600;
        """)
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        # Ref info
        ref_info = QHBoxLayout()
        ref_info.setSpacing(SPACING.lg)

        from_label = QLabel(f"From: {self._from_ref[:8]}")
        from_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-family: monospace;
            font-size: {TYPOGRAPHY.text_sm}px;
            background: {self._colors.surface};
            padding: 4px 8px;
            border-radius: {RADIUS.sm}px;
        """)
        ref_info.addWidget(from_label)

        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {self._colors.text_hint};")
        ref_info.addWidget(arrow)

        to_label = QLabel(f"To: {self._to_ref[:8]}")
        to_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-family: monospace;
            font-size: {TYPOGRAPHY.text_sm}px;
            background: {self._colors.surface};
            padding: 4px 8px;
            border-radius: {RADIUS.sm}px;
        """)
        ref_info.addWidget(to_label)
        ref_info.addStretch()

        layout.addLayout(ref_info)

        # Diff viewer
        self._diff_view = QPlainTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFont("Consolas, Monaco, monospace", 11))
        self._diff_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px;
            }}
        """)

        # Apply syntax highlighting
        self._highlighter = DiffHighlighter(self._colors, self._diff_view.document())

        # Set content
        if self._diff_content.strip():
            self._diff_view.setPlainText(self._diff_content)
        else:
            self._diff_view.setPlainText("No changes between these snapshots.")

        layout.addWidget(self._diff_view, 1)

        # Stats summary
        stats = self._calculate_stats()
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(SPACING.lg)

        additions_label = QLabel(f"+{stats['additions']} additions")
        additions_label.setStyleSheet(f"""
            color: {self._colors.diff_add_fg};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: 600;
        """)
        stats_layout.addWidget(additions_label)

        deletions_label = QLabel(f"-{stats['deletions']} deletions")
        deletions_label.setStyleSheet(f"""
            color: {self._colors.diff_remove_fg};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: 600;
        """)
        stats_layout.addWidget(deletions_label)

        files_label = QLabel(f"{stats['files']} files changed")
        files_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        stats_layout.addWidget(files_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: 8px 24px;
                font-size: {TYPOGRAPHY.text_base}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {self._colors.primary_dark};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _calculate_stats(self) -> dict:
        """Calculate diff statistics."""
        additions = 0
        deletions = 0
        files = set()

        for line in self._diff_content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
            elif line.startswith("diff --git"):
                # Extract filename
                parts = line.split(" ")
                if len(parts) >= 4:
                    files.add(parts[2])

        return {
            "additions": additions,
            "deletions": deletions,
            "files": len(files),
        }


__all__ = ["DiffViewerDialog"]
