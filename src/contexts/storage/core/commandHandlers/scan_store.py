"""
Scan Store Use Case.

Lists files available in the configured S3 data store.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    S3ScannerProtocol,
    StoreRepository,
)
from src.contexts.storage.core.commands import ScanStoreCommand
from src.contexts.storage.core.derivers import StorageState, derive_scan_store
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")


def scan_store(
    command: ScanStoreCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    event_bus: EventBus,
) -> OperationResult:
    """
    Scan the configured data store for available files.

    1. Load store config
    2. Scan S3 via scanner
    3. Derive event (pure)
    4. Publish event
    """
    logger.debug("scan_store: prefix=%s", command.prefix)

    store = store_repo.get()
    state = StorageState(configured_store=store)

    if store is None:
        result = derive_scan_store(
            discovered_files=(),
            prefix=command.prefix,
            state=state,
        )
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    files = s3_scanner.list_files(
        bucket=store.bucket_name,
        prefix=command.prefix,
    )

    result = derive_scan_store(
        discovered_files=tuple(files),
        prefix=command.prefix,
        state=state,
    )

    if isinstance(result, FailureEvent):
        logger.error("scan_store failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event_bus.publish(result)

    logger.info("Store scanned: %d files found", len(files))

    return OperationResult.ok(data=list(files))
