"""
Change Language Use Case

Functional use case for changing the application language.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.contexts.settings.core.commandHandlers._helpers import extract_failure_message
from src.contexts.settings.core.commands import ChangeLanguageCommand
from src.contexts.settings.core.derivers import derive_language_change
from src.contexts.settings.core.entities import LanguagePreference
from src.contexts.settings.core.events import LanguageChanged
from src.contexts.settings.core.invariants import VALID_LANGUAGES

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def change_language(
    command: ChangeLanguageCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus | None = None,
) -> Result[LanguageChanged, str]:
    """
    Change the application language.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive LanguageChanged event (pure)
    3. Persist new language
    4. Publish event
    5. Return result

    Args:
        command: Command with language code
        settings_repo: Repository for settings persistence
        event_bus: Optional event bus for publishing events

    Returns:
        Success with LanguageChanged event, or Failure with error message
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_language_change(
        new_language_code=command.language_code,
        current_settings=current_settings,
    )

    if isinstance(result, Failure):
        return Failure(extract_failure_message(result.failure()))

    event: LanguageChanged = result

    # Step 3: Persist changes
    language_name = VALID_LANGUAGES.get(command.language_code, "Unknown")
    new_language = LanguagePreference(
        code=command.language_code,
        name=language_name,
    )
    settings_repo.set_language(new_language)

    # Step 4: Publish event
    if event_bus is not None:
        event_bus.publish(event)

    # Step 5: Return result
    return Success(event)
