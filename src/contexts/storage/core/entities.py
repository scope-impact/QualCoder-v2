"""
Storage Context: Entities and Value Objects
Immutable data types representing domain concepts for S3 data store.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import PurePosixPath

from src.shared.common.uuid7 import new_uuid7


# ============================================================
# Typed Identifiers
# ============================================================


@dataclass(frozen=True)
class StoreId:
    """Typed identifier for DataStore entities."""

    value: str

    @classmethod
    def new(cls) -> StoreId:
        return cls(value=new_uuid7())


# ============================================================
# Value Objects
# ============================================================


@dataclass(frozen=True)
class RemoteFile:
    """
    Metadata about a file in the remote S3 data store.
    Value object — no identity, compared by attributes.
    """

    key: str
    size_bytes: int
    last_modified: datetime
    etag: str | None = None

    @property
    def filename(self) -> str:
        """Extract filename from the S3 key."""
        return PurePosixPath(self.key).name

    @property
    def extension(self) -> str:
        """Extract file extension from the S3 key."""
        return PurePosixPath(self.key).suffix


@dataclass(frozen=True)
class SyncManifest:
    """
    Tracks which files have been pulled from or pushed to the data store.
    Value object for audit trail.
    """

    pulled_keys: tuple[str, ...] = ()
    pushed_keys: tuple[str, ...] = ()


# ============================================================
# Entities
# ============================================================


@dataclass(frozen=True)
class DataStore:
    """
    Configuration for an S3 data store.
    Aggregate Root for the Storage context.
    """

    id: StoreId
    bucket_name: str
    region: str
    prefix: str = ""
    dvc_remote_name: str = "origin"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_prefix(self, new_prefix: str) -> DataStore:
        """Return new DataStore with updated prefix."""
        return replace(self, prefix=new_prefix)

    def with_dvc_remote(self, new_remote: str) -> DataStore:
        """Return new DataStore with updated DVC remote name."""
        return replace(self, dvc_remote_name=new_remote)
