"""
Change Theme Use Case

Functional use case for changing the application theme.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commands import ChangeThemeCommand
from src.contexts.settings.core.derivers import derive_theme_change
from src.contexts.settings.core.entities import ThemePreference
from src.contexts.settings.core.failure_events import SettingsNotChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def change_theme(
    command: ChangeThemeCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Change the application theme.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive ThemeChanged event (pure)
    3. Persist new theme
    4. Publish event
    5. Return result

    Args:
        command: Command with new theme name
        settings_repo: Repository for settings persistence
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with ThemeChanged event on success
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_theme_change(
        new_theme=command.theme,
        current_settings=current_settings,
    )

    if isinstance(result, SettingsNotChanged):
        return OperationResult.from_failure(result)

    event = result

    # Step 3: Persist changes
    new_theme = ThemePreference(name=command.theme)
    settings_repo.set_theme(new_theme)

    # Step 4: Publish event
    event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.ok(data=event)
