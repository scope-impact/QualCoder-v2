"""
Change Font Use Case

Functional use case for changing font settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.contexts.settings.core.commands import ChangeFontCommand
from src.contexts.settings.core.derivers import derive_font_change
from src.contexts.settings.core.entities import FontPreference
from src.contexts.settings.core.events import FontChanged

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def change_font(
    command: ChangeFontCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus | None = None,
) -> Result[FontChanged, str]:
    """
    Change font settings.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive FontChanged event (pure)
    3. Persist new font
    4. Publish event
    5. Return result

    Args:
        command: Command with font family and size
        settings_repo: Repository for settings persistence
        event_bus: Optional event bus for publishing events

    Returns:
        Success with FontChanged event, or Failure with error message
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_font_change(
        family=command.family,
        size=command.size,
        current_settings=current_settings,
    )

    if isinstance(result, Failure):
        # Extract message from failure reason
        failure_reason = result.failure()
        if hasattr(failure_reason, "message"):
            return Failure(failure_reason.message)
        return Failure(str(failure_reason))

    event: FontChanged = result

    # Step 3: Persist changes
    new_font = FontPreference(family=command.family, size=command.size)
    settings_repo.set_font(new_font)

    # Step 4: Publish event
    if event_bus is not None:
        event_bus.publish(event)

    # Step 5: Return result
    return Success(event)
