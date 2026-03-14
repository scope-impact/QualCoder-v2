"""
Pull File Use Case.

Downloads a file from S3 into the local project.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    S3ScannerProtocol,
    StoreRepository,
)
from src.contexts.storage.core.commands import PullFileCommand
from src.contexts.storage.core.derivers import StorageState, derive_pull_file
from src.contexts.storage.core.events import FilePulled
from src.contexts.storage.core.failure_events import FileNotPulled
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")


def pull_file(
    command: PullFileCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    event_bus: EventBus,
) -> OperationResult:
    """
    Pull a file from S3 to local project.

    1. Load store config
    2. Validate key (pure)
    3. Download file (I/O)
    4. Publish event
    """
    logger.debug("pull_file: key=%s", command.key)

    store = store_repo.get()
    state = StorageState(configured_store=store)

    result = derive_pull_file(
        key=command.key,
        local_path=command.local_path,
        state=state,
    )

    if isinstance(result, FailureEvent):
        logger.error("pull_file failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: FilePulled = result

    try:
        downloaded = s3_scanner.sync_file(
            bucket=store.bucket_name,
            key=command.key,
            local_path=command.local_path,
        )
    except Exception:
        logger.exception("pull_file: sync failed for %s", command.key)
        failure = FileNotPulled.download_failed(command.key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    event_bus.publish(event)

    if downloaded:
        logger.info("File pulled: %s -> %s", command.key, command.local_path)
    else:
        logger.info("File already in sync: %s", command.key)

    return OperationResult.ok(data=command.local_path)
