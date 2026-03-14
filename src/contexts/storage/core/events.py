"""
Storage Context: Domain Events
Immutable records of things that happened in the storage domain.

Event type convention: storage.{entity}_{action}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.contexts.storage.core.entities import RemoteFile, StoreId
from src.shared.common.types import DomainEvent

# ============================================================
# Store Events
# ============================================================


@dataclass(frozen=True)
class StoreConfigured(DomainEvent):
    """An S3 data store was configured."""

    event_type: ClassVar[str] = "storage.store_configured"

    store_id: StoreId
    bucket_name: str
    region: str
    prefix: str
    dvc_remote_name: str

    @classmethod
    def create(
        cls,
        store_id: StoreId,
        bucket_name: str,
        region: str,
        prefix: str = "",
        dvc_remote_name: str = "origin",
    ) -> StoreConfigured:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            store_id=store_id,
            bucket_name=bucket_name,
            region=region,
            prefix=prefix,
            dvc_remote_name=dvc_remote_name,
        )


@dataclass(frozen=True)
class StoreScanned(DomainEvent):
    """The data store was scanned and files were discovered."""

    event_type: ClassVar[str] = "storage.store_scanned"

    store_id: StoreId
    prefix: str
    files: tuple[RemoteFile, ...]
    file_count: int

    @classmethod
    def create(
        cls,
        store_id: StoreId,
        prefix: str,
        files: tuple[RemoteFile, ...],
    ) -> StoreScanned:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            store_id=store_id,
            prefix=prefix,
            files=files,
            file_count=len(files),
        )


# ============================================================
# File Transfer Events
# ============================================================


@dataclass(frozen=True)
class FilePulled(DomainEvent):
    """A file was pulled from S3 to local project."""

    event_type: ClassVar[str] = "storage.file_pulled"

    store_id: StoreId
    key: str
    local_path: str

    @classmethod
    def create(
        cls,
        store_id: StoreId,
        key: str,
        local_path: str,
    ) -> FilePulled:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            store_id=store_id,
            key=key,
            local_path=local_path,
        )


@dataclass(frozen=True)
class ExportPushed(DomainEvent):
    """A coded export was pushed to S3."""

    event_type: ClassVar[str] = "storage.export_pushed"

    store_id: StoreId
    local_path: str
    destination_key: str

    @classmethod
    def create(
        cls,
        store_id: StoreId,
        local_path: str,
        destination_key: str,
    ) -> ExportPushed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            store_id=store_id,
            local_path=local_path,
            destination_key=destination_key,
        )
