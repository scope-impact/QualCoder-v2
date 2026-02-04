"""
Sync Status Button - Nav bar widget for cloud sync status and actions.

Displays sync status icon and triggers sync pull on click.
Updates reactively via SyncSignalBridge signals.

Status states:
- offline: Cloud sync disabled (hidden or cloud-off icon)
- syncing: Pull in progress (spinning cloud)
- synced: All changes synced (cloud-check)
- error: Sync error occurred (cloud-alert)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from design_system import RADIUS, SPACING, ColorPalette, Icon

if TYPE_CHECKING:
    from src.shared.infra.signal_bridge.sync import SyncStatusPayload


class SyncStatusButton(QPushButton):
    """
    Button widget displaying cloud sync status.

    Shows status icon in nav bar and triggers sync on click.

    Signals:
        sync_requested: Emitted when user clicks to sync
    """

    sync_requested = Signal()

    # Icon mappings for each status
    ICONS = {
        "offline": "mdi6.cloud-off-outline",
        "syncing": "mdi6.cloud-sync-outline",
        "synced": "mdi6.cloud-check-outline",
        "error": "mdi6.cloud-alert-outline",
        "connecting": "mdi6.cloud-sync-outline",
    }

    TOOLTIPS = {
        "offline": "Cloud sync disabled",
        "syncing": "Syncing...",
        "synced": "Cloud sync active - Click to pull",
        "error": "Sync error - Click to retry",
        "connecting": "Connecting to cloud...",
    }

    def __init__(self, colors: ColorPalette, parent=None):
        super().__init__(parent)
        self._colors = colors
        self._status = "offline"
        self._pending_count = 0
        self._error_message: str | None = None

        self.setObjectName("sync_status_button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._on_clicked)

        # Create icon container
        self._icon_widget: Icon | None = None
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)

        self._apply_style()
        self._update_icon()

    def _on_clicked(self):
        """Handle click - emit sync request if enabled."""
        if self._status != "offline":
            self.sync_requested.emit()

    def set_status(
        self,
        status: str,
        pending_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        """
        Update sync status display.

        Args:
            status: One of "offline", "syncing", "synced", "error", "connecting"
            pending_count: Number of pending changes
            error_message: Error details if status is "error"
        """
        self._status = status
        self._pending_count = pending_count
        self._error_message = error_message

        self._update_icon()
        self._update_tooltip()
        self._apply_style()

        # Hide when offline
        self.setVisible(status != "offline")

    def update_from_payload(self, payload: SyncStatusPayload) -> None:
        """
        Update from SyncStatusPayload (from SyncSignalBridge).

        Args:
            payload: Status payload from signal bridge
        """
        self.set_status(
            status=payload.status,
            pending_count=payload.pending_count,
            error_message=payload.error_message,
        )

    def _update_icon(self) -> None:
        """Update icon based on current status."""
        # Remove old icon
        if self._icon_widget:
            self._layout.removeWidget(self._icon_widget)
            self._icon_widget.deleteLater()
            self._icon_widget = None

        icon_name = self.ICONS.get(self._status, self.ICONS["offline"])
        icon_color = self._get_icon_color()

        self._icon_widget = Icon(
            icon_name,
            size=18,
            color=icon_color,
            colors=self._colors,
        )
        self._layout.addWidget(self._icon_widget)

    def _get_icon_color(self) -> str:
        """Get icon color based on status."""
        if self._status == "synced":
            return self._colors.success
        elif self._status == "error":
            return self._colors.error
        elif self._status in ("syncing", "connecting"):
            return self._colors.warning
        else:
            return self._colors.text_secondary

    def _update_tooltip(self) -> None:
        """Update tooltip based on current status."""
        tooltip = self.TOOLTIPS.get(self._status, "Cloud sync")

        if self._pending_count > 0 and self._status == "synced":
            tooltip = f"Synced ({self._pending_count} pending) - Click to pull"
        elif self._error_message and self._status == "error":
            tooltip = f"Error: {self._error_message}\nClick to retry"

        self.setToolTip(tooltip)

    def _apply_style(self) -> None:
        """Apply button styling."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {RADIUS.sm}px;
                padding: {SPACING.sm}px;
                min-width: 32px;
                max-width: 32px;
            }}
            QPushButton:hover {{
                background-color: {self._colors.surface_light};
            }}
            QPushButton:pressed {{
                background-color: {self._colors.surface};
            }}
        """)
