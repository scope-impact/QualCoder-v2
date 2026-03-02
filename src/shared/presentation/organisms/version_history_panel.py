"""
Version History Panel

Displays a split-panel VCS history with inline diff viewer.

Layout:
- Left panel: Compact commit list (clickable)
- Right panel: Diff viewer for selected commit

Implements QC-048.06 Version History UI:
- AC #3: View history of all changes
- AC #4: See what changed between two points in time (inline)
- AC #5: Restore to previous state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
    get_qicon,
)

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class SnapshotItem:
    """Data for a single snapshot in the timeline."""

    git_sha: str
    message: str
    timestamp: datetime
    event_count: int = 0
    is_current: bool = False


class DiffHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for git diff output."""

    def __init__(self, colors: ColorPalette, document: QTextDocument):
        super().__init__(document)
        self._colors = colors

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


class CommitListItem(QFrame):
    """A compact commit entry for the left panel."""

    def __init__(
        self,
        snapshot: SnapshotItem,
        colors: ColorPalette,
        is_selected: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._snapshot = snapshot
        self._colors = colors
        self._is_selected = is_selected
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("commit_item")
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(2)

        # Top row: message + current badge
        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING.xs)

        # Truncate message
        msg = self._snapshot.message
        if len(msg) > 50:
            msg = msg[:47] + "..."

        self._msg_label = QLabel(msg)
        self._msg_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: {"600" if self._snapshot.is_current else "400"};
        """)
        top_row.addWidget(self._msg_label, 1)

        if self._snapshot.is_current:
            badge = QLabel("HEAD")
            badge.setStyleSheet(f"""
                background: {self._colors.primary};
                color: {self._colors.primary_foreground};
                padding: 1px 6px;
                border-radius: {RADIUS.xs}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: 600;
            """)
            top_row.addWidget(badge)

        layout.addLayout(top_row)

        # Bottom row: SHA + timestamp
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(SPACING.sm)

        sha_short = self._snapshot.git_sha[:7]
        self._sha_label = QLabel(sha_short)
        self._sha_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-family: monospace;
        """)
        bottom_row.addWidget(self._sha_label)

        time_str = self._snapshot.timestamp.strftime("%m/%d %H:%M")
        self._time_label = QLabel(time_str)
        self._time_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        bottom_row.addWidget(self._time_label)
        bottom_row.addStretch()

        layout.addLayout(bottom_row)

    def _update_style(self):
        if self._is_selected:
            self.setStyleSheet(f"""
                QFrame#commit_item {{
                    background: {self._colors.primary};
                    border-radius: {RADIUS.sm}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#commit_item {{
                    background: transparent;
                    border-radius: {RADIUS.sm}px;
                }}
                QFrame#commit_item:hover {{
                    background: {self._colors.surface_light};
                }}
            """)

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_style()
        # Update label colors when selected
        if selected:
            self._msg_label.setStyleSheet(f"""
                color: {self._colors.primary_foreground};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: 600;
            """)
            self._sha_label.setStyleSheet(f"""
                color: {self._colors.primary_foreground};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-family: monospace;
                opacity: 0.8;
            """)
            self._time_label.setStyleSheet(f"""
                color: {self._colors.primary_foreground};
                font-size: {TYPOGRAPHY.text_xs}px;
                opacity: 0.8;
            """)
        else:
            self._msg_label.setStyleSheet(f"""
                color: {self._colors.text_primary};
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: {"600" if self._snapshot.is_current else "400"};
            """)
            self._sha_label.setStyleSheet(f"""
                color: {self._colors.text_hint};
                font-size: {TYPOGRAPHY.text_xs}px;
                font-family: monospace;
            """)
            self._time_label.setStyleSheet(f"""
                color: {self._colors.text_hint};
                font-size: {TYPOGRAPHY.text_xs}px;
            """)


class VersionHistoryPanel(QFrame):
    """
    Split-panel version control history with inline diff viewer.

    Left panel: Commit list (clickable)
    Right panel: Diff viewer for selected commit

    Signals:
        restore_requested(str): Emitted when user wants to restore to a snapshot
        view_diff_requested(str, str): Emitted when user wants to view diff
        refresh_requested(): Emitted when user wants to refresh the list
    """

    restore_requested = Signal(str)  # git_sha
    view_diff_requested = Signal(str, str)  # from_sha, to_sha
    refresh_requested = Signal()

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._snapshots: list[SnapshotItem] = []
        self._selected_index: int = -1
        self._diff_content: str = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("version_history_panel")
        self.setStyleSheet(f"""
            QFrame#version_history_panel {{
                background: {self._colors.background};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {self._colors.border};
            }}
        """)

        # Left panel: Commit list
        self._left_panel = QFrame()
        self._left_panel.setObjectName("left_panel")
        self._left_panel.setStyleSheet(f"""
            QFrame#left_panel {{
                background: {self._colors.surface};
                border-top-left-radius: {RADIUS.lg}px;
                border-bottom-left-radius: {RADIUS.lg}px;
            }}
        """)
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        left_layout.setSpacing(SPACING.xs)

        # Left header
        left_header = QHBoxLayout()
        left_header.setSpacing(SPACING.xs)

        commits_title = QLabel("Commits")
        commits_title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_sm}px;
            font-weight: 600;
        """)
        left_header.addWidget(commits_title)
        left_header.addStretch()

        refresh_btn = QPushButton()
        refresh_btn.setIcon(get_qicon("mdi6.refresh"))
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        left_header.addWidget(refresh_btn)

        left_layout.addLayout(left_header)

        # Commit list
        self._commit_list = QListWidget()
        self._commit_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 0;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self._commit_list.currentRowChanged.connect(self._on_commit_selected)
        left_layout.addWidget(self._commit_list, 1)

        # Empty state for left panel
        self._empty_label = QLabel("No commits yet")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_sm}px;
            padding: {SPACING.lg}px;
        """)
        self._empty_label.hide()
        left_layout.addWidget(self._empty_label)

        self._splitter.addWidget(self._left_panel)

        # Right panel: Diff viewer
        self._right_panel = QFrame()
        self._right_panel.setObjectName("right_panel")
        self._right_panel.setStyleSheet(f"""
            QFrame#right_panel {{
                background: {self._colors.background};
                border-top-right-radius: {RADIUS.lg}px;
                border-bottom-right-radius: {RADIUS.lg}px;
            }}
        """)
        right_layout = QVBoxLayout(self._right_panel)
        right_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        right_layout.setSpacing(SPACING.sm)

        # Right header with commit info
        self._diff_header = QFrame()
        diff_header_layout = QHBoxLayout(self._diff_header)
        diff_header_layout.setContentsMargins(0, 0, 0, 0)
        diff_header_layout.setSpacing(SPACING.md)

        self._diff_title = QLabel("Select a commit to view changes")
        self._diff_title.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        diff_header_layout.addWidget(self._diff_title)
        diff_header_layout.addStretch()

        # Restore button (hidden until commit selected)
        self._restore_btn = QPushButton("Restore")
        self._restore_btn.setIcon(get_qicon("mdi6.restore"))
        self._restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restore_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._colors.warning};
                color: {self._colors.warning_foreground};
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: 4px 12px;
                font-size: {TYPOGRAPHY.text_sm}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {self._colors.warning_light};
            }}
        """)
        self._restore_btn.clicked.connect(self._on_restore_clicked)
        self._restore_btn.hide()
        diff_header_layout.addWidget(self._restore_btn)

        right_layout.addWidget(self._diff_header)

        # Stats bar
        self._stats_bar = QFrame()
        stats_layout = QHBoxLayout(self._stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(SPACING.md)

        self._additions_label = QLabel("+0")
        self._additions_label.setStyleSheet(f"""
            color: {self._colors.diff_add_fg};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: 600;
        """)
        stats_layout.addWidget(self._additions_label)

        self._deletions_label = QLabel("-0")
        self._deletions_label.setStyleSheet(f"""
            color: {self._colors.diff_remove_fg};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-weight: 600;
        """)
        stats_layout.addWidget(self._deletions_label)

        self._files_label = QLabel("0 files")
        self._files_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_xs}px;
        """)
        stats_layout.addWidget(self._files_label)
        stats_layout.addStretch()

        self._stats_bar.hide()
        right_layout.addWidget(self._stats_bar)

        # Diff viewer
        self._diff_view = QPlainTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFont("Consolas, Monaco, monospace", 10))
        self._diff_view.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {self._colors.surface};
                color: {self._colors.text_primary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.xs}px;
            }}
        """)
        self._diff_view.setPlaceholderText(
            "Select a commit from the list to view its changes..."
        )
        self._highlighter = DiffHighlighter(self._colors, self._diff_view.document())
        right_layout.addWidget(self._diff_view, 1)

        self._splitter.addWidget(self._right_panel)

        # Set initial sizes (30% left, 70% right)
        self._splitter.setSizes([280, 520])

        layout.addWidget(self._splitter)

    def set_snapshots(self, snapshots: list[SnapshotItem]):
        """Update the displayed snapshots."""
        self._snapshots = snapshots
        self._commit_list.clear()
        self._selected_index = -1

        self._empty_label.setVisible(len(snapshots) == 0)
        self._commit_list.setVisible(len(snapshots) > 0)

        if not snapshots:
            self._diff_view.setPlainText("")
            self._diff_title.setText("No commits yet")
            self._restore_btn.hide()
            self._stats_bar.hide()
            return

        # Add commit items
        for snapshot in snapshots:
            widget = CommitListItem(snapshot, self._colors)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, snapshot)
            self._commit_list.addItem(item)
            self._commit_list.setItemWidget(item, widget)

        # Select first (most recent) commit
        if snapshots:
            self._commit_list.setCurrentRow(0)

    def _on_commit_selected(self, index: int):
        """Handle commit selection."""
        if index < 0 or index >= len(self._snapshots):
            return

        self._selected_index = index
        snapshot = self._snapshots[index]

        # Update selection styling
        for i in range(self._commit_list.count()):
            item = self._commit_list.item(i)
            widget = self._commit_list.itemWidget(item)
            if widget and isinstance(widget, CommitListItem):
                widget.set_selected(i == index)

        # Get previous SHA for diff
        if index + 1 < len(self._snapshots):
            prev_sha = self._snapshots[index + 1].git_sha
            from_ref = prev_sha
            to_ref = snapshot.git_sha

            # Update header
            self._diff_title.setText(
                f"{prev_sha[:7]} → {snapshot.git_sha[:7]}: {snapshot.message}"
            )

            # Show restore button (unless it's the current/HEAD commit)
            self._restore_btn.setVisible(not snapshot.is_current)

            # Request diff load
            self.view_diff_requested.emit(from_ref, to_ref)
        else:
            # First commit - no previous to compare
            self._diff_title.setText(f"Initial commit: {snapshot.message}")
            self._diff_view.setPlainText(
                "This is the initial commit. No previous state to compare."
            )
            self._restore_btn.setVisible(not snapshot.is_current)
            self._stats_bar.hide()

    def set_diff_content(self, diff_content: str):
        """Set the diff content to display."""
        self._diff_content = diff_content

        if diff_content.strip():
            self._diff_view.setPlainText(diff_content)
            stats = self._calculate_stats(diff_content)
            self._additions_label.setText(f"+{stats['additions']}")
            self._deletions_label.setText(f"-{stats['deletions']}")
            self._files_label.setText(f"{stats['files']} files")
            self._stats_bar.show()
        else:
            self._diff_view.setPlainText("No changes in this commit.")
            self._stats_bar.hide()

    def _calculate_stats(self, diff_content: str) -> dict:
        """Calculate diff statistics."""
        additions = 0
        deletions = 0
        files = set()

        for line in diff_content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
            elif line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    files.add(parts[2])

        return {
            "additions": additions,
            "deletions": deletions,
            "files": len(files),
        }

    def _on_restore_clicked(self):
        """Handle restore button click."""
        if self._selected_index >= 0:
            snapshot = self._snapshots[self._selected_index]
            self.restore_requested.emit(snapshot.git_sha)

    def clear(self):
        """Clear all snapshots."""
        self.set_snapshots([])


# Keep SnapshotCard for backwards compatibility (used in tests)
class SnapshotCard(QFrame):
    """A single snapshot entry (legacy, for test compatibility)."""

    restore_clicked = Signal(str)
    view_diff_clicked = Signal(str, str)

    def __init__(
        self,
        snapshot: SnapshotItem,
        previous_sha: str | None,
        colors: ColorPalette,
        parent=None,
    ):
        super().__init__(parent)
        self._snapshot = snapshot
        self._previous_sha = previous_sha
        self._colors = colors
        self.setObjectName("snapshot_card")


__all__ = ["VersionHistoryPanel", "SnapshotItem", "SnapshotCard", "CommitListItem"]
