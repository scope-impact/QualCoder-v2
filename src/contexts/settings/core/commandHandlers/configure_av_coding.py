"""
Configure AV Coding Use Case

Functional use case for configuring audio/video coding settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commands import ConfigureAVCodingCommand
from src.contexts.settings.core.derivers import derive_av_coding_config_change
from src.contexts.settings.core.entities import AVCodingConfig
from src.contexts.settings.core.failure_events import SettingsNotChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def configure_av_coding(
    command: ConfigureAVCodingCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Configure AV coding settings.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive AVCodingConfigChanged event (pure)
    3. Persist new AV coding config
    4. Publish event
    5. Return result

    Args:
        command: Command with timestamp format and speaker format
        settings_repo: Repository for settings persistence
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with AVCodingConfigChanged event on success
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_av_coding_config_change(
        timestamp_format=command.timestamp_format,
        speaker_format=command.speaker_format,
        current_settings=current_settings,
    )

    if isinstance(result, SettingsNotChanged):
        return OperationResult.from_failure(result)

    event = result

    # Step 3: Persist changes
    new_av_coding = AVCodingConfig(
        timestamp_format=command.timestamp_format,
        speaker_format=command.speaker_format,
    )
    settings_repo.set_av_coding_config(new_av_coding)

    # Step 4: Publish event
    event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.ok(data=event)
