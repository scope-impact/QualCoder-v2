"""
Data Store ViewModel

Connects the Import from S3 dialog and Settings Data Store tab
to storage command handlers.

Responsibilities:
- Check if store is configured
- Scan S3 for remote files
- Pull files from S3 (download + auto-import)
- Cross-reference with source_repo to identify already-imported files
- Provide store configuration info for Settings UI
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from src.contexts.storage.core.commands import (
    ConfigureStoreCommand,
    PullFileCommand,
    ScanStoreCommand,
)
from src.contexts.storage.core.entities import RemoteFile

if TYPE_CHECKING:
    from src.shared.common.operation_result import OperationResult
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.storage.presentation")


class SourceRepoProtocol(Protocol):
    """Minimal protocol for cross-referencing imported sources."""

    def get_all(self) -> list: ...


class DataStoreViewModel:
    """
    ViewModel for Data Store operations.

    Used by:
    - ImportFromS3Dialog (browse + pull files)
    - SettingsDialog Data Store tab (configure + test connection)

    Pure Python class — no Qt dependency, testable without event loop.
    """

    def __init__(
        self,
        store_repo,
        source_repo: SourceRepoProtocol,
        s3_scanner,
        dvc_gateway,
        event_bus: EventBus,
        state=None,
        session=None,
    ) -> None:
        self._store_repo = store_repo
        self._source_repo = source_repo
        self._s3_scanner = s3_scanner
        self._dvc_gateway = dvc_gateway
        self._event_bus = event_bus
        self._state = state
        self._session = session
        self._last_error: str | None = None

    # =========================================================================
    # Configuration
    # =========================================================================

    @property
    def is_configured(self) -> bool:
        """Check if a data store is configured."""
        return self._store_repo.get() is not None

    def get_config(self) -> dict | None:
        """Get current store configuration as dict for UI display."""
        store = self._store_repo.get()
        if store is None:
            return None
        return {
            "bucket_name": store.bucket_name,
            "region": store.region,
            "prefix": store.prefix,
            "dvc_remote_name": store.dvc_remote_name,
        }

    def configure(
        self,
        bucket_name: str,
        region: str,
        prefix: str = "",
        dvc_remote_name: str = "origin",
    ) -> bool:
        """Configure the S3 data store."""
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )

        result = configure_store(
            command=ConfigureStoreCommand(
                bucket_name=bucket_name,
                region=region,
                prefix=prefix,
                dvc_remote_name=dvc_remote_name,
            ),
            store_repo=self._store_repo,
            dvc_gateway=self._dvc_gateway,
            event_bus=self._event_bus,
        )
        self._last_error = result.error if result.is_failure else None
        return result.is_success

    def test_connection(self) -> bool:
        """Test S3 connectivity by listing files with limit=1."""
        store = self._store_repo.get()
        if store is None:
            self._last_error = "Data store not configured"
            return False
        try:
            self._s3_scanner.list_files(
                bucket=store.bucket_name,
                prefix=store.prefix,
            )
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    # =========================================================================
    # Scan & Browse
    # =========================================================================

    def scan(self, prefix: str = "") -> list[RemoteFile]:
        """Scan S3 for available files."""
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store

        store = self._store_repo.get()
        scan_prefix = prefix or (store.prefix if store else "")

        result = scan_store(
            command=ScanStoreCommand(prefix=scan_prefix),
            store_repo=self._store_repo,
            s3_scanner=self._s3_scanner,
            event_bus=self._event_bus,
        )
        if result.is_failure:
            self._last_error = result.error
            return []
        return result.data or []

    def get_imported_filenames(self) -> set[str]:
        """Get set of filenames already imported as sources."""
        try:
            sources = self._source_repo.get_all()
            return {s.name for s in sources}
        except Exception:
            return set()

    # =========================================================================
    # Pull (Download + Auto-Import)
    # =========================================================================

    def pull_file(self, key: str, local_dir: str) -> OperationResult:
        """
        Pull a single file from S3 to local directory.

        Args:
            key: S3 object key
            local_dir: Local directory to download into

        Returns:
            OperationResult with local_path on success
        """
        from pathlib import PurePosixPath

        from src.contexts.storage.core.commandHandlers.pull_file import pull_file

        filename = PurePosixPath(key).name
        local_path = f"{local_dir}/{filename}"

        result = pull_file(
            command=PullFileCommand(key=key, local_path=local_path),
            store_repo=self._store_repo,
            dvc_gateway=self._dvc_gateway,
            event_bus=self._event_bus,
        )
        self._last_error = result.error if result.is_failure else None
        return result

    def pull_and_import(self, key: str, local_dir: str) -> OperationResult:
        """
        Pull file from S3 and auto-import as a source.

        Combines pull_file + import_file_source in a single operation.
        """
        from src.contexts.projects.core.commands import ImportFileSourceCommand
        from src.contexts.sources.core.commandHandlers.import_file_source import (
            import_file_source,
        )

        # Step 1: Download from S3
        pull_result = self.pull_file(key, local_dir)
        if pull_result.is_failure:
            return pull_result

        local_path = pull_result.data

        # Step 2: Auto-import into sources
        import_result = import_file_source(
            command=ImportFileSourceCommand(file_path=local_path, origin="s3"),
            state=self._state,
            source_repo=self._source_repo,
            event_bus=self._event_bus,
            session=self._session,
        )
        if import_result.is_failure:
            self._last_error = import_result.error
        return import_result

    # =========================================================================
    # Error Access
    # =========================================================================

    @property
    def last_error(self) -> str | None:
        """Get the last error message."""
        return self._last_error
