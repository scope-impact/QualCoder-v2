"""
Export and Push Use Case.

Composite handler: exports project data (QDPX/codebook/SQLite),
then pushes the resulting file to S3.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Protocol

from src.contexts.storage.core.commands import ExportAndPushCommand
from src.contexts.storage.core.derivers import StorageState, derive_push_export
from src.contexts.storage.core.entities import DataStore
from src.contexts.storage.core.events import ExportPushed
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult

logger = logging.getLogger("qualcoder.storage.core")

# File extensions per export format
_FORMAT_EXTENSIONS = {
    "qdpx": ".qdpx",
    "codebook": ".txt",
    "sqlite": ".db",
    "html": ".html",
}


class StoreRepository(Protocol):
    def get(self) -> DataStore | None: ...


class S3ScannerProtocol(Protocol):
    def upload_file(self, bucket: str, key: str, local_path: str) -> None: ...


def export_and_push(
    command: ExportAndPushCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    exporter: Callable[..., OperationResult],
    event_bus: Any,
) -> OperationResult:
    """
    Export project data and push to S3.

    1. Validate store is configured and destination key is valid
    2. Run the exporter to produce a local file
    3. Push the file to S3
    4. Publish ExportPushed event

    Args:
        command: Export format, destination key, and staging dir
        store_repo: Repository for store config
        s3_scanner: S3 client for uploading
        exporter: Callable that produces a file; receives a command with
                  output_path and returns OperationResult
        event_bus: For publishing domain events
    """
    logger.debug(
        "export_and_push: format=%s, dest=%s",
        command.export_format,
        command.destination_key,
    )

    # 1. Validate store config
    store = store_repo.get()
    state = StorageState(configured_store=store)

    result = derive_push_export(
        local_path="(pending)",
        destination_key=command.destination_key,
        state=state,
    )

    if isinstance(result, FailureEvent):
        logger.error("export_and_push failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    # 2. Run the exporter to produce a local file
    ext = _FORMAT_EXTENSIONS.get(command.export_format, "")
    staging_path = Path(command.local_staging_dir) / f"export{ext}"

    # Build a simple command-like object for the exporter
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _ExportCmd:
        output_path: str

    export_result = exporter(_ExportCmd(output_path=str(staging_path)))

    if hasattr(export_result, "success") and not export_result.success:
        logger.error("export_and_push: export step failed")
        return export_result

    # 3. Upload to S3
    s3_scanner.upload_file(
        bucket=store.bucket_name,
        key=command.destination_key,
        local_path=str(staging_path),
    )

    # 4. Publish event
    event = ExportPushed.create(
        store_id=store.id,
        local_path=str(staging_path),
        destination_key=command.destination_key,
    )
    event_bus.publish(event)

    logger.info(
        "Exported %s and pushed to %s",
        command.export_format,
        command.destination_key,
    )

    return OperationResult.ok(
        data={
            "export_format": command.export_format,
            "destination_key": command.destination_key,
            "local_path": str(staging_path),
        }
    )
