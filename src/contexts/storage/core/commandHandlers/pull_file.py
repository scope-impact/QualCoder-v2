"""
Pull File Use Case.

Pulls tracked data from S3 via DVC.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    DvcGatewayProtocol,
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
    dvc_gateway: DvcGatewayProtocol,
    event_bus: EventBus,
) -> OperationResult:
    """
    Pull tracked data from S3 via DVC.

    1. Load store config
    2. Validate key (pure)
    3. dvc pull (I/O) — DVC handles sync/skip internally
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
        assert store is not None  # guaranteed by derive_pull_file success
        pull_result = dvc_gateway.pull(remote=store.dvc_remote_name)
        if not pull_result.success:
            raise RuntimeError(f"dvc pull failed: {pull_result.message}")
    except Exception:
        logger.exception("pull_file: dvc pull failed for %s", command.key)
        failure = FileNotPulled.download_failed(command.key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    event_bus.publish(event)

    logger.info("File pulled via DVC: %s -> %s", command.key, command.local_path)

    return OperationResult.ok(data=command.local_path)
