"""
Configure Observability Use Case

Functional use case for configuring logging and telemetry settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commands import ConfigureObservabilityCommand
from src.contexts.settings.core.derivers import derive_observability_config_change
from src.contexts.settings.core.entities import ObservabilityConfig
from src.contexts.settings.core.failure_events import SettingsNotChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def configure_observability(
    command: ConfigureObservabilityCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Configure observability settings (logging level, file logging, telemetry).

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive ObservabilityConfigChanged event (pure)
    3. Persist new observability config
    4. Publish event
    5. Return result

    Args:
        command: Command with observability configuration
        settings_repo: Repository for settings persistence
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with ObservabilityConfigChanged event on success
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_observability_config_change(
        log_level=command.log_level,
        enable_file_logging=command.enable_file_logging,
        enable_telemetry=command.enable_telemetry,
        current_settings=current_settings,
    )

    if isinstance(result, SettingsNotChanged):
        return OperationResult.from_failure(result)

    event = result

    # Step 3: Persist changes
    new_config = ObservabilityConfig(
        log_level=command.log_level.upper(),
        enable_file_logging=command.enable_file_logging,
        enable_telemetry=command.enable_telemetry,
    )
    settings_repo.set_observability_config(new_config)

    # Step 4: Publish event
    event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.ok(data=event)
