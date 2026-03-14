"""
Storage Context: Shared State and Protocol Definitions

Defines repository and service Protocols used across command handlers.
Follows the pattern from src/contexts/coding/core/commandHandlers/_state.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from src.contexts.storage.core.entities import DataStore, RemoteFile

if TYPE_CHECKING:
    pass


class StoreRepository(Protocol):
    """Protocol for data store configuration persistence."""

    def get(self) -> DataStore | None: ...
    def save(self, store: DataStore) -> None: ...


class S3ScannerProtocol(Protocol):
    """Protocol for S3 operations (list, download, upload)."""

    def list_files(self, bucket: str, prefix: str = "") -> list[RemoteFile]: ...
    def download_file(self, bucket: str, key: str, local_path: str) -> None: ...
    def upload_file(self, bucket: str, key: str, local_path: str) -> None: ...
