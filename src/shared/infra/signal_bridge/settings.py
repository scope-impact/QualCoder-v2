"""
Settings Signal Bridge - Domain Events → Qt Signals for settings changes.

Bridges settings events to UI for reactive updates when configuration changes.
"""

from __future__ import annotations

from src.shared.infra.signal_bridge.base import BaseSignalBridge


# =============================================================================
# Signal Bridge
# =============================================================================


class SettingsSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Settings bounded context.

    Emits Qt signals when settings events occur, enabling reactive UI updates.

    Usage:
        bridge = SettingsSignalBridge.instance(event_bus)
        bridge.start()
    """

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "settings"

    def _register_converters(self) -> None:
        """Register all event converters."""
        pass
