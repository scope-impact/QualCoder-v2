"""
Settings Signal Bridge - Domain Events → Qt Signals for settings changes.

Bridges settings events to UI for reactive updates when configuration changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter

if TYPE_CHECKING:
    from src.contexts.settings.core.events import (
        CloudSyncConfigChanged,
        CloudSyncDisabled,
        CloudSyncEnabled,
    )


# =============================================================================
# Payloads (UI-friendly DTOs)
# =============================================================================


@dataclass(frozen=True)
class CloudSyncConfigPayload:
    """Payload for cloud sync configuration changes."""

    event_type: str
    enabled: bool
    convex_url: str | None
    old_enabled: bool = False
    old_convex_url: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Converters
# =============================================================================


class CloudSyncConfigChangedConverter(EventConverter):
    """Convert CloudSyncConfigChanged event to payload."""

    def convert(self, event: CloudSyncConfigChanged) -> CloudSyncConfigPayload:
        return CloudSyncConfigPayload(
            event_type="settings.cloud_sync_config_changed",
            enabled=event.enabled,
            convex_url=event.convex_url,
            old_enabled=event.old_enabled,
            old_convex_url=event.old_convex_url,
        )


class CloudSyncEnabledConverter(EventConverter):
    """Convert CloudSyncEnabled event to payload."""

    def convert(self, event: CloudSyncEnabled) -> CloudSyncConfigPayload:
        return CloudSyncConfigPayload(
            event_type="settings.cloud_sync_enabled",
            enabled=True,
            convex_url=event.convex_url,
        )


class CloudSyncDisabledConverter(EventConverter):
    """Convert CloudSyncDisabled event to payload."""

    def convert(self, _event: CloudSyncDisabled) -> CloudSyncConfigPayload:
        return CloudSyncConfigPayload(
            event_type="settings.cloud_sync_disabled",
            enabled=False,
            convex_url=None,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class SettingsSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Settings bounded context.

    Emits Qt signals when settings events occur, enabling reactive UI updates.

    Signals:
        cloud_sync_config_changed: Emitted when cloud sync config changes
        cloud_sync_enabled: Emitted when cloud sync is enabled
        cloud_sync_disabled: Emitted when cloud sync is disabled

    Usage:
        bridge = SettingsSignalBridge.instance(event_bus)
        bridge.cloud_sync_config_changed.connect(self._on_cloud_sync_changed)
        bridge.start()
    """

    # Cloud sync signals
    cloud_sync_config_changed = Signal(object)
    cloud_sync_enabled = Signal(object)
    cloud_sync_disabled = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "settings"

    def _register_converters(self) -> None:
        """Register all event converters."""
        self.register_converter(
            "settings.cloud_sync_config_changed",
            CloudSyncConfigChangedConverter(),
            "cloud_sync_config_changed",
        )
        self.register_converter(
            "settings.cloud_sync_enabled",
            CloudSyncEnabledConverter(),
            "cloud_sync_enabled",
        )
        self.register_converter(
            "settings.cloud_sync_disabled",
            CloudSyncDisabledConverter(),
            "cloud_sync_disabled",
        )
