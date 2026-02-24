"""
Configure Cloud Sync Use Case

Functional use case for configuring cloud sync settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure

from src.contexts.settings.core.commands import ConfigureCloudSyncCommand
from src.contexts.settings.core.derivers import derive_cloud_sync_config_change
from src.contexts.settings.core.events import CloudSyncConfigChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def configure_cloud_sync(
    command: ConfigureCloudSyncCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus | None = None,
) -> OperationResult:
    """
    Configure cloud sync settings.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive CloudSyncConfigChanged event (pure)
    3. Persist new settings
    4. Publish event
    5. Return result

    Args:
        command: Command with enabled flag and convex_url
        settings_repo: Repository for settings persistence
        event_bus: Optional event bus for publishing events

    Returns:
        OperationResult with CloudSyncConfigChanged event on success
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_cloud_sync_config_change(
        enabled=command.enabled,
        convex_url=command.convex_url,
        current_settings=current_settings,
    )

    if isinstance(result, Failure):
        failure = result.failure()
        return OperationResult.failure(
            error=failure.reason,
            error_code=failure.error_code,
        )

    event: CloudSyncConfigChanged = result

    # Step 3: Persist changes
    settings_repo.set_cloud_sync_enabled(command.enabled)
    if command.convex_url is not None:
        settings_repo.set_convex_url(command.convex_url)

    # Step 4: Publish event
    if event_bus is not None:
        event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.success(event)
