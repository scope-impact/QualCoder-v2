"""
Push Export Use Case.

Uploads a coded export from local project to S3.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from src.contexts.storage.core.commands import PushExportCommand
from src.contexts.storage.core.derivers import StorageState, derive_push_export
from src.contexts.storage.core.entities import DataStore
from src.contexts.storage.core.events import ExportPushed
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")


class StoreRepository(Protocol):
    def get(self) -> DataStore | None: ...


class S3ScannerProtocol(Protocol):
    def upload_file(self, bucket: str, key: str, local_path: str) -> None: ...


def push_export(
    command: PushExportCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    event_bus: object,
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

    # Perform actual upload
    s3_scanner.upload_file(
        bucket=store.bucket_name,
        key=command.destination_key,
        local_path=command.local_path,
    )

    event_bus.publish(event)

    logger.info("Export pushed: %s -> %s", command.local_path, command.destination_key)

    return OperationResult.ok(data=command.destination_key)
