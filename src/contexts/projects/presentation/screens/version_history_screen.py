"""
Version History Screen

Displays VCS timeline with restore and diff capabilities.

Implements QC-048.06 Version History UI:
- AC #3: View history of all changes
- AC #4: See what changed between two points in time
- AC #5: Restore to previous state
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from design_system import (
    RADIUS,
    SPACING,
    TYPOGRAPHY,
    ColorPalette,
    get_colors,
    get_pixmap,
    get_qicon,
)
from src.shared.presentation.organisms import SnapshotItem, VersionHistoryPanel

if TYPE_CHECKING:
    from src.contexts.projects.presentation.viewmodels import VersionControlViewModel


class VersionHistoryScreen(QWidget):
    """
    Screen for viewing and managing VCS history.

    Provides:
    - Timeline of all snapshots (commits)
    - Restore to any previous snapshot
    - View diff between snapshots
    - Initialize VCS for projects without it
    """

    def __init__(self, colors: ColorPalette = None, parent=None):
        super().__init__(parent)
        self._colors = colors or get_colors()
        self._viewmodel: VersionControlViewModel | None = None
        self._content: QWidget | None = None
        self._toolbar: QWidget | None = None
        self._history_panel: VersionHistoryPanel | None = None
        self._init_container: QWidget | None = None

        self._setup_ui()

    def _setup_ui(self):
        """Build the screen UI."""
        # Main container
        self._content = QWidget()
        self._content.setStyleSheet(f"""
            QWidget {{
                background: {self._colors.background};
            }}
        """)

        layout = QVBoxLayout(self._content)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.lg)

        # Header
        header = QHBoxLayout()
        header.setSpacing(SPACING.md)

        icon_label = QLabel()
        icon_label.setPixmap(get_pixmap("mdi6.source-branch", size=32))
        header.addWidget(icon_label)

        title = QLabel("Version History")
        title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_2xl}px;
            font-weight: 700;
        """)
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

        # Description
        desc = QLabel(
            "Track changes to your project database. "
            "Every mutation is automatically saved, and you can restore to any previous state."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_base}px;
        """)
        layout.addWidget(desc)

        # VCS not initialized container (shown when VCS not set up)
        self._init_container = QFrame()
        self._init_container.setStyleSheet(f"""
            QFrame {{
                background: {self._colors.surface};
                border: 1px dashed {self._colors.border};
                border-radius: {RADIUS.lg}px;
            }}
        """)
        init_layout = QVBoxLayout(self._init_container)
        init_layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        init_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        init_layout.setSpacing(SPACING.md)

        init_icon = QLabel()
        init_icon.setPixmap(get_pixmap("mdi6.git", size=48))
        init_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        init_layout.addWidget(init_icon)

        init_title = QLabel("Version Control Not Initialized")
        init_title.setStyleSheet(f"""
            color: {self._colors.text_primary};
            font-size: {TYPOGRAPHY.text_lg}px;
            font-weight: 600;
        """)
        init_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        init_layout.addWidget(init_title)

        init_desc = QLabel(
            "Initialize version control to start tracking changes to your project."
        )
        init_desc.setStyleSheet(f"""
            color: {self._colors.text_secondary};
            font-size: {TYPOGRAPHY.text_sm}px;
        """)
        init_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        init_layout.addWidget(init_desc)

        self._init_btn = QPushButton("Initialize Version Control")
        self._init_btn.setIcon(get_qicon("mdi6.play"))
        self._init_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._init_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._colors.primary};
                color: {self._colors.primary_foreground};
                border: none;
                border-radius: {RADIUS.md}px;
                padding: 12px 24px;
                font-size: {TYPOGRAPHY.text_base}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {self._colors.primary_dark};
            }}
        """)
        self._init_btn.clicked.connect(self._on_initialize_clicked)
        init_layout.addWidget(self._init_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._init_container)
        self._init_container.hide()

        # Version history panel
        self._history_panel = VersionHistoryPanel(colors=self._colors)
        self._history_panel.restore_requested.connect(self._on_restore_requested)
        self._history_panel.view_diff_requested.connect(self._on_view_diff_requested)
        self._history_panel.refresh_requested.connect(self._on_refresh_requested)
        layout.addWidget(self._history_panel, 1)

        # Build toolbar
        self._setup_toolbar()

    def _setup_toolbar(self):
        """Build the toolbar."""
        self._toolbar = QWidget()
        toolbar_layout = QHBoxLayout(self._toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(SPACING.md)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setIcon(get_qicon("mdi6.refresh"))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self._colors.text_secondary};
                border: 1px solid {self._colors.border};
                border-radius: {RADIUS.sm}px;
                padding: 6px 12px;
                font-size: {TYPOGRAPHY.text_sm}px;
            }}
            QPushButton:hover {{
                background: {self._colors.surface_light};
                color: {self._colors.text_primary};
            }}
        """)
        refresh_btn.clicked.connect(self._on_refresh_requested)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()

    def set_viewmodel(self, viewmodel: VersionControlViewModel):
        """Wire up the viewmodel."""
        self._viewmodel = viewmodel

        # Connect signals
        viewmodel.snapshots_loaded.connect(self._on_snapshots_loaded)
        viewmodel.restore_completed.connect(self._on_restore_completed)
        viewmodel.restore_failed.connect(self._on_restore_failed)
        viewmodel.diff_loaded.connect(self._on_diff_loaded)
        viewmodel.error_occurred.connect(self._on_error)
        viewmodel.vcs_initialized.connect(self._on_vcs_initialized)

        # Initial load
        self.refresh()

    def refresh(self):
        """Refresh the history view."""
        if not self._viewmodel:
            return

        # Check if VCS is initialized
        if not self._viewmodel.is_initialized:
            self._show_init_state()
        else:
            self._show_history_state()
            self._viewmodel.load_snapshots()

    def _show_init_state(self):
        """Show the initialization prompt."""
        self._init_container.show()
        self._history_panel.hide()

    def _show_history_state(self):
        """Show the history panel."""
        self._init_container.hide()
        self._history_panel.show()

    def _on_initialize_clicked(self):
        """Handle initialize button click."""
        if self._viewmodel:
            self._viewmodel.initialize_vcs()

    def _on_vcs_initialized(self):
        """Handle successful VCS initialization."""
        self._show_history_state()

    def _on_snapshots_loaded(self, snapshots: list[SnapshotItem]):
        """Handle loaded snapshots."""
        self._history_panel.set_snapshots(snapshots)

    def _on_restore_requested(self, git_sha: str):
        """Handle restore request with confirmation."""
        reply = QMessageBox.question(
            self,
            "Restore Snapshot",
            f"Are you sure you want to restore to snapshot {git_sha[:8]}?\n\n"
            "This will replace your current database state with the selected snapshot. "
            "A new snapshot will be created first to preserve your current state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes and self._viewmodel:
            self._viewmodel.restore_to_snapshot(git_sha)

    def _on_restore_completed(self, message: str):
        """Handle successful restore."""
        QMessageBox.information(
            self,
            "Restore Complete",
            message,
        )

    def _on_restore_failed(self, error: str):
        """Handle restore failure."""
        QMessageBox.warning(
            self,
            "Restore Failed",
            f"Failed to restore snapshot:\n{error}",
        )

    def _on_view_diff_requested(self, from_ref: str, to_ref: str):
        """Handle view diff request."""
        if self._viewmodel:
            self._viewmodel.load_diff(from_ref, to_ref)

    def _on_diff_loaded(self, _from_ref: str, _to_ref: str, diff_content: str):
        """Update inline diff viewer."""
        self._history_panel.set_diff_content(diff_content)

    def _on_refresh_requested(self):
        """Handle refresh request."""
        self.refresh()

    def _on_error(self, message: str):
        """Handle error."""
        QMessageBox.warning(
            self,
            "Error",
            message,
        )

    # ScreenProtocol implementation
    def get_toolbar_content(self) -> QWidget | None:
        """Return toolbar content."""
        return self._toolbar

    def get_content(self) -> QWidget:
        """Return main content."""
        return self._content

    def get_status_message(self) -> str:
        """Return status message."""
        return "Version History"


__all__ = ["VersionHistoryScreen"]
