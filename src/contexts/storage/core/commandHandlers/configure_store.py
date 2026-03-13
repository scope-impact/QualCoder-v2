"""
Configure Store Use Case.

Sets up an S3 bucket as the project's data store.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from src.contexts.storage.core.commands import ConfigureStoreCommand
from src.contexts.storage.core.derivers import StorageState, derive_configure_store
from src.contexts.storage.core.entities import DataStore
from src.contexts.storage.core.events import StoreConfigured
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")


class StoreRepository(Protocol):
    def get(self) -> DataStore | None: ...
    def save(self, store: DataStore) -> None: ...


def configure_store(
    command: ConfigureStoreCommand,
    store_repo: StoreRepository,
    event_bus: object,
) -> OperationResult:
    """
    Configure an S3 data store for the project.

    1. Validate config (pure)
    2. Persist store config
    3. Publish event
    """
    logger.debug("configure_store: bucket=%s, region=%s", command.bucket_name, command.region)

    state = StorageState()

    result = derive_configure_store(
        bucket_name=command.bucket_name,
        region=command.region,
        prefix=command.prefix,
        dvc_remote_name=command.dvc_remote_name,
        state=state,
    )

    if isinstance(result, FailureEvent):
        logger.error("configure_store failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: StoreConfigured = result

    store = DataStore(
        id=event.store_id,
        bucket_name=event.bucket_name,
        region=event.region,
        prefix=event.prefix,
        dvc_remote_name=event.dvc_remote_name,
    )
    store_repo.save(store)

    event_bus.publish(event)

    logger.info("Store configured: bucket=%s", store.bucket_name)

    return OperationResult.ok(data=store)
