"""
Push Export Use Case.

Uploads a coded export from local project to S3.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    S3ScannerProtocol,
    StoreRepository,
)
from src.contexts.storage.core.commands import PushExportCommand
from src.contexts.storage.core.derivers import StorageState, derive_push_export
from src.contexts.storage.core.events import ExportPushed
from src.contexts.storage.core.failure_events import ExportNotPushed
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")


def push_export(
    command: PushExportCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    event_bus: EventBus,
) -> OperationResult:
    """
    Push a coded export to S3.

    1. Load store config
    2. Validate destination key (pure)
    3. Upload file (I/O)
    4. Publish event
    """
    logger.debug("push_export: %s -> %s", command.local_path, command.destination_key)

    store = store_repo.get()
    state = StorageState(configured_store=store)

    result = derive_push_export(
        local_path=command.local_path,
        destination_key=command.destination_key,
        state=state,
    )

    if isinstance(result, FailureEvent):
        logger.error("push_export failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: ExportPushed = result

    try:
        s3_scanner.upload_file(
            bucket=store.bucket_name,
            key=command.destination_key,
            local_path=command.local_path,
        )
    except Exception:
        logger.exception("push_export: upload failed for %s", command.destination_key)
        failure = ExportNotPushed.upload_failed(command.destination_key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    event_bus.publish(event)

    logger.info("Export pushed: %s -> %s", command.local_path, command.destination_key)

    return OperationResult.ok(data=command.destination_key)
