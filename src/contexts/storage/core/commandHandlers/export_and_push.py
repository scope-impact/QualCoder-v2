"""
Export and Push Use Case.

Composite handler: exports project data (QDPX/codebook/SQLite),
then pushes the resulting file to S3.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    S3ScannerProtocol,
    StoreRepository,
)
from src.contexts.storage.core.commands import ExportAndPushCommand
from src.contexts.storage.core.events import ExportPushed
from src.contexts.storage.core.failure_events import ExportNotPushed
from src.contexts.storage.core.invariants import is_valid_s3_key
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")

# File extensions per export format
_FORMAT_EXTENSIONS = {
    "qdpx": ".qdpx",
    "codebook": ".txt",
    "sqlite": ".db",
    "html": ".html",
}


@dataclass(frozen=True)
class ExportRequest:
    """Input for an exporter callable."""

    output_path: str


def export_and_push(
    command: ExportAndPushCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    exporter: Callable[..., OperationResult],
    event_bus: EventBus,
) -> OperationResult:
    """
    Export project data and push to S3.

    1. Validate store is configured and destination key is valid
    2. Run the exporter to produce a local file
    3. Push the file to S3
    4. Publish ExportPushed event
    """
    logger.debug(
        "export_and_push: format=%s, dest=%s",
        command.export_format,
        command.destination_key,
    )

    # 1. Validate store config and destination key
    store = store_repo.get()
    if store is None:
        failure = ExportNotPushed.not_configured()
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    if not is_valid_s3_key(command.destination_key):
        failure = ExportNotPushed.invalid_key(command.destination_key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    # 2. Run the exporter to produce a local file
    ext = _FORMAT_EXTENSIONS.get(command.export_format, "")
    staging_path = Path(command.local_staging_dir) / f"export{ext}"

    export_result = exporter(ExportRequest(output_path=str(staging_path)))

    if hasattr(export_result, "success") and not export_result.success:
        logger.error("export_and_push: export step failed")
        return export_result

    # 3. Upload to S3
    try:
        s3_scanner.upload_file(
            bucket=store.bucket_name,
            key=command.destination_key,
            local_path=str(staging_path),
        )
    except Exception:
        logger.exception(
            "export_and_push: upload failed for %s", command.destination_key
        )
        failure = ExportNotPushed.upload_failed(command.destination_key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

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
