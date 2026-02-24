"""
Configure Backup Use Case

Functional use case for configuring automatic backup settings.
Global scope - no project required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commands import ConfigureBackupCommand
from src.contexts.settings.core.derivers import derive_backup_config_change
from src.contexts.settings.core.entities import BackupConfig
from src.contexts.settings.core.failure_events import SettingsNotChanged
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


def configure_backup(
    command: ConfigureBackupCommand,
    settings_repo: UserSettingsRepository,
    event_bus: EventBus,
) -> OperationResult:
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
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with BackupConfigChanged event on success
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

    if isinstance(result, SettingsNotChanged):
        return OperationResult.from_failure(result)

    event = result

    # Step 3: Persist changes
    new_backup = BackupConfig(
        enabled=command.enabled,
        interval_minutes=command.interval_minutes,
        max_backups=command.max_backups,
        backup_path=command.backup_path,
    )
    settings_repo.set_backup_config(new_backup)

    # Step 4: Publish event
    event_bus.publish(event)

    # Step 5: Return result
    return OperationResult.ok(data=event)
