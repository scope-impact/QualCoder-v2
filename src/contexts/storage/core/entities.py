"""
Storage Context: Entities and Value Objects
Immutable data types representing domain concepts for S3 data store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
