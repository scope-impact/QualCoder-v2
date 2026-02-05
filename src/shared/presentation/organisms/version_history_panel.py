"""
Version History Panel

Displays a timeline of VCS snapshots with restore functionality.

Implements QC-048.06 Version History UI:
- AC #3: View history of all changes
- AC #5: Restore to previous state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
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


class SnapshotCard(QFrame):
    """A single snapshot entry in the timeline."""

    restore_clicked = Signal(str)  # git_sha
    view_diff_clicked = Signal(str, str)  # from_sha, to_sha

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
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("snapshot_card")

        # Card styling
        bg = (
            self._colors.surface
            if not self._snapshot.is_current
            else self._colors.surface_light
        )
        border = (
            self._colors.primary if self._snapshot.is_current else self._colors.border
        )
        self.setStyleSheet(f"""
            QFrame#snapshot_card {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {RADIUS.md}px;
                padding: {SPACING.sm}px;
            }}
            QFrame#snapshot_card:hover {{
                background: {self._colors.surface_light};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        # Header row: timestamp + current badge
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        # Timeline dot
        dot = QLabel("●")
        dot.setStyleSheet(f"""
            color: {self._colors.primary if self._snapshot.is_current else self._colors.text_secondary};
            font-size: 10px;
        """)
        header.addWidget(dot)

        # Timestamp
        time_str = self._snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        header.addWidget(time_label)

        header.addStretch()

        # Current badge
        if self._snapshot.is_current:
            badge = QLabel("Current")
            badge.setStyleSheet(f"""
                background: {self._colors.primary};
                color: {self._colors.primary_foreground};
                padding: 2px 8px;
                border-radius: {RADIUS.sm}px;
                font-size: {TYPOGRAPHY.text_xs}px;
                font-weight: 600;
            """)
            header.addWidget(badge)

        layout.addLayout(header)

        # Message
        msg_label = QLabel(self._snapshot.message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_base}px;
        """)
        layout.addWidget(msg_label)

        # SHA (truncated)
        sha_short = (
            self._snapshot.git_sha[:8]
            if len(self._snapshot.git_sha) > 8
            else self._snapshot.git_sha
        )
        sha_label = QLabel(f"SHA: {sha_short}")
        sha_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_xs}px;
            font-family: monospace;
        """)
        layout.addWidget(sha_label)

        # Action buttons (only if not current)
        if not self._snapshot.is_current:
            actions = QHBoxLayout()
            actions.setSpacing(SPACING.sm)
            actions.addStretch()

            # View diff button (if previous exists)
            if self._previous_sha:
                diff_btn = QPushButton("View Changes")
                diff_btn.setIcon(get_qicon("mdi6.file-compare"))
                diff_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                diff_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {self._colors.text_secondary};
                        border: 1px solid {self._colors.border};
                        border-radius: {RADIUS.sm}px;
                        padding: 4px 8px;
                        font-size: {TYPOGRAPHY.text_sm}px;
                    }}
                    QPushButton:hover {{
                        background: {self._colors.surface_light};
                        color: {self._colors.text_primary};
                    }}
                """)
                diff_btn.clicked.connect(
                    lambda: self.view_diff_clicked.emit(
                        self._previous_sha, self._snapshot.git_sha
                    )
                )
                actions.addWidget(diff_btn)

            # Restore button
            restore_btn = QPushButton("Restore")
            restore_btn.setIcon(get_qicon("mdi6.restore"))
            restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            restore_btn.setStyleSheet(f"""
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
            restore_btn.clicked.connect(
                lambda: self.restore_clicked.emit(self._snapshot.git_sha)
            )
            actions.addWidget(restore_btn)

            layout.addLayout(actions)


class VersionHistoryPanel(QFrame):
    """
    Panel showing version control history timeline.

    Displays snapshots in reverse chronological order with restore options.

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
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        # Header
        header = QHBoxLayout()
        header.setSpacing(SPACING.sm)

        title = QLabel("Version History")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: 600;
        """)
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton()
        refresh_btn.setIcon(get_qicon("mdi6.refresh"))
        refresh_btn.setToolTip("Refresh history")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                padding: 4px;
            }}
            QPushButton:hover {{
                background: {self._colors.surface_light};
                border-radius: {RADIUS.sm}px;
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Scroll area for snapshots
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(SPACING.sm)
        self._scroll_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll, 1)

        # Empty state
        self._empty_label = QLabel(
            "No version history yet.\nMake changes to start tracking."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            color: {self._colors.text_hint};
            font-size: {TYPOGRAPHY.text_sm}px;
            padding: {SPACING.xl}px;
        """)
        self._scroll_layout.insertWidget(0, self._empty_label)

    def set_snapshots(self, snapshots: list[SnapshotItem]):
        """Update the displayed snapshots."""
        self._snapshots = snapshots

        # Clear existing cards
        while self._scroll_layout.count() > 1:  # Keep the stretch
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show/hide empty state
        self._empty_label.setVisible(len(snapshots) == 0)

        if not snapshots:
            self._scroll_layout.insertWidget(0, self._empty_label)
            return

        # Add snapshot cards (reverse order - newest first)
        for i, snapshot in enumerate(snapshots):
            previous_sha = snapshots[i + 1].git_sha if i + 1 < len(snapshots) else None
            card = SnapshotCard(
                snapshot=snapshot,
                previous_sha=previous_sha,
                colors=self._colors,
            )
            card.restore_clicked.connect(self.restore_requested.emit)
            card.view_diff_clicked.connect(self.view_diff_requested.emit)
            self._scroll_layout.insertWidget(i, card)

    def clear(self):
        """Clear all snapshots."""
        self.set_snapshots([])


__all__ = ["VersionHistoryPanel", "SnapshotItem", "SnapshotCard"]
