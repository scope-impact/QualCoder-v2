"""
Settings Context: Policies

Reactive handlers that respond to domain events.
Each policy subscribes to events and calls command handlers within THIS context.

Following the DDD Workshop pattern:
- Policies live inside the bounded context
- Policies call the context's own command handlers
- Each context manages its own data
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.shared.infra.cascade_registry import CascadeRegistry
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger(__name__)


# ============================================================
# Event Handlers (called by policies)
# ============================================================


def _handle_theme_changed(event: Any) -> None:
    """Handle theme change - audit logging."""
    logger.info(
        "Theme changed: %s -> %s",
        event.old_theme,
        event.new_theme,
    )


def _handle_font_changed(event: Any) -> None:
    """Handle font change - audit logging."""
    logger.info("Font changed: family=%s, size=%s", event.family, event.size)


def _handle_language_changed(event: Any) -> None:
    """Handle language change - audit logging."""
    logger.info(
        "Language changed: %s -> %s",
        event.old_language,
        event.new_language,
    )


# ============================================================
# Policy Configuration
# ============================================================


def configure_settings_policies(
    event_bus: EventBus,
    cascade_registry: CascadeRegistry,  # noqa: ARG001
) -> None:
    """
    Configure all policies for the settings context.

    Subscribes to relevant events and routes them to handlers.

    Args:
        event_bus: The application's event bus
        cascade_registry: Cascade registry (unused - audit-only handlers)
    """
    # --- Audit-only handlers (subscribe directly to event bus) ---
    event_bus.subscribe("settings.theme_changed", _handle_theme_changed)
    event_bus.subscribe("settings.font_changed", _handle_font_changed)
    event_bus.subscribe("settings.language_changed", _handle_language_changed)

    logger.info("Settings context policies configured")


__all__ = [
    "configure_settings_policies",
]
