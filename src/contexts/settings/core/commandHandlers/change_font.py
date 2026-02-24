"""
Change Font Use Case

Functional use case for changing font settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commands import ChangeFontCommand
from src.contexts.settings.core.derivers import derive_font_change
from src.contexts.settings.core.entities import FontPreference
from src.contexts.settings.core.failure_events import SettingsNotChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def change_font(
    command: ChangeFontCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus,
) -> OperationResult:
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
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with FontChanged event on success
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_font_change(
        family=command.family,
        size=command.size,
        current_settings=current_settings,
    )

    if isinstance(result, SettingsNotChanged):
        return OperationResult.from_failure(result)

    event = result

    # Step 3: Persist changes
    new_font = FontPreference(family=command.family, size=command.size)
    settings_repo.set_font(new_font)

    # Step 4: Publish event
    event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.ok(data=event)
