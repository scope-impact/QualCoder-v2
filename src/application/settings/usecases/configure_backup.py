"""
Configure Backup Use Case

Functional use case for configuring automatic backup settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.settings.commands import ConfigureBackupCommand
from src.contexts.settings.core.derivers import derive_backup_config_change
from src.contexts.settings.core.entities import BackupConfig
from src.contexts.settings.core.events import BackupConfigChanged

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.settings.infra import UserSettingsRepository


def configure_backup(
    command: ConfigureBackupCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus | None = None,
) -> Result[BackupConfigChanged, str]:
    """
    Configure automatic backup settings.

    Functional use case following 5-step pattern:
    1. Load current settings from repository
    2. Derive BackupConfigChanged event (pure)
    3. Persist new backup config
    4. Publish event
    5. Return result

    Args:
        command: Command with backup configuration
        settings_repo: Repository for settings persistence
        event_bus: Optional event bus for publishing events

    Returns:
        Success with BackupConfigChanged event, or Failure with error message
    """
    # Step 1: Load current state
    current_settings = settings_repo.load()

    # Step 2: Derive event (pure)
    result = derive_backup_config_change(
        enabled=command.enabled,
        interval_minutes=command.interval_minutes,
        max_backups=command.max_backups,
        backup_path=command.backup_path,
        current_settings=current_settings,
    )

    if isinstance(result, Failure):
        # Extract message from failure reason
        failure_reason = result.failure()
        if hasattr(failure_reason, "message"):
            return Failure(failure_reason.message)
        return Failure(str(failure_reason))

    event: BackupConfigChanged = result

    # Step 3: Persist changes
    new_backup = BackupConfig(
        enabled=command.enabled,
        interval_minutes=command.interval_minutes,
        max_backups=command.max_backups,
        backup_path=command.backup_path,
    )
    settings_repo.set_backup_config(new_backup)

    # Step 4: Publish event
    if event_bus is not None:
        event_bus.publish(event)

    # Step 5: Return result
    return Success(event)
