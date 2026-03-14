"""
Scan and Import Use Case.

Composite handler: pulls a file from S3, auto-detects format
by extension, and routes to the appropriate importer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from src.contexts.storage.core.commandHandlers._state import (
    S3ScannerProtocol,
    StoreRepository,
)
from src.contexts.storage.core.commands import ScanAndImportCommand
from src.contexts.storage.core.entities import RemoteFile
from src.contexts.storage.core.failure_events import FileNotPulled
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.core")

# Supported import format extensions
_IMPORTABLE_EXTENSIONS: dict[str, str] = {
    ".qdpx": "qdpx",
    ".rqda": "rqda",
    ".csv": "csv",
    ".txt": "txt",
    ".db": "sqlite",
    ".sqlite": "sqlite",
    ".sqlite3": "sqlite",
}


def detect_import_format(key: str) -> str | None:
    """
    Detect the import format from an S3 key's file extension.

    Returns:
        Format string ("qdpx", "rqda", "csv", "txt", "sqlite")
        or None if extension is not importable.
    """
    ext = PurePosixPath(key).suffix.lower()
    return _IMPORTABLE_EXTENSIONS.get(ext)


def list_importable_files(files: list[RemoteFile]) -> list[RemoteFile]:
    """
    Filter a list of RemoteFiles to only those with importable extensions.

    Use after scan_store to show the user which files can be imported.
    """
    return [f for f in files if detect_import_format(f.key) is not None]


def scan_and_import(
    command: ScanAndImportCommand,
    store_repo: StoreRepository,
    s3_scanner: S3ScannerProtocol,
    importers: dict[str, Callable[..., OperationResult]],
    event_bus: EventBus,
) -> OperationResult:
    """
    Pull a file from S3 and auto-import based on format detection.

    1. Validate store is configured
    2. Detect import format from key extension
    3. Pull file from S3
    4. Route to the correct importer
    """
    logger.debug("scan_and_import: key=%s", command.key)

    # 1. Validate store config
    store = store_repo.get()
    if store is None:
        failure = FileNotPulled.not_configured()
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    # 2. Detect format
    fmt = detect_import_format(command.key)
    if fmt is None:
        ext = PurePosixPath(command.key).suffix
        return OperationResult.fail(
            error=f"Unsupported file format: '{ext}'",
            error_code="SCAN_AND_IMPORT/UNSUPPORTED_FORMAT",
            suggestions=tuple(
                f"Supported: {', '.join(sorted(set(_IMPORTABLE_EXTENSIONS.values())))}"
            ),
        )

    # 3. Check importer is registered
    importer = importers.get(fmt)
    if importer is None:
        return OperationResult.fail(
            error=f"No importer registered for format '{fmt}'",
            error_code="SCAN_AND_IMPORT/NO_IMPORTER",
            suggestions=(f"Register an importer for '{fmt}' format",),
        )

    # 4. Pull file from S3
    filename = PurePosixPath(command.key).name
    local_path = str(Path(command.local_staging_dir) / filename)

    try:
        s3_scanner.download_file(
            bucket=store.bucket_name,
            key=command.key,
            local_path=local_path,
        )
    except Exception:
        logger.exception("scan_and_import: download failed for %s", command.key)
        failure = FileNotPulled.download_failed(command.key)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    logger.info(
        "Pulled %s -> %s, routing to '%s' importer", command.key, local_path, fmt
    )

    # 5. Route to importer
    return importer(source_path=local_path)
