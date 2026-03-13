"""
Storage Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
"""

from __future__ import annotations

from dataclasses import dataclass

from src.contexts.storage.core.entities import DataStore, RemoteFile, StoreId
from src.contexts.storage.core.events import (
    ExportPushed,
    FilePulled,
    StoreConfigured,
    StoreScanned,
)
from src.contexts.storage.core.failure_events import (
    ExportNotPushed,
    FileNotPulled,
    StoreNotConfigured,
    StoreNotScanned,
)
from src.contexts.storage.core.invariants import (
    is_valid_bucket_name,
    is_valid_s3_key,
    is_valid_store_config,
)


# ============================================================
# State Container (Input to Derivers)
# ============================================================


@dataclass(frozen=True)
class StorageState:
    """
    State container for storage context derivers.
    Contains all the context needed to validate operations.
    """

    configured_store: DataStore | None = None


# ============================================================
# Store Derivers
# ============================================================


def derive_configure_store(
    bucket_name: str,
    region: str,
    prefix: str,
    dvc_remote_name: str,
    state: StorageState,
) -> StoreConfigured | StoreNotConfigured:
    """
    Derive a StoreConfigured event or failure event.
    """
    if not is_valid_bucket_name(bucket_name):
        return StoreNotConfigured.invalid_bucket(bucket_name)

    if not region or not region.strip():
        return StoreNotConfigured.invalid_region()

    store_id = StoreId.new()

    return StoreConfigured.create(
        store_id=store_id,
        bucket_name=bucket_name,
        region=region,
        prefix=prefix,
        dvc_remote_name=dvc_remote_name,
    )


def derive_scan_store(
    discovered_files: tuple[RemoteFile, ...],
    prefix: str,
    state: StorageState,
) -> StoreScanned | StoreNotScanned:
    """
    Derive a StoreScanned event or failure event.
    """
    if state.configured_store is None:
        return StoreNotScanned.not_configured()

    return StoreScanned.create(
        store_id=state.configured_store.id,
        prefix=prefix,
        files=discovered_files,
    )


# ============================================================
# File Transfer Derivers
# ============================================================


def derive_pull_file(
    key: str,
    local_path: str,
    state: StorageState,
) -> FilePulled | FileNotPulled:
    """
    Derive a FilePulled event or failure event.
    """
    if state.configured_store is None:
        return FileNotPulled.not_configured()

    if not is_valid_s3_key(key):
        return FileNotPulled.invalid_key(key)

    return FilePulled.create(
        store_id=state.configured_store.id,
        key=key,
        local_path=local_path,
    )


def derive_push_export(
    local_path: str,
    destination_key: str,
    state: StorageState,
) -> ExportPushed | ExportNotPushed:
    """
    Derive an ExportPushed event or failure event.
    """
    if state.configured_store is None:
        return ExportNotPushed.not_configured()

    if not is_valid_s3_key(destination_key):
        return ExportNotPushed.invalid_key(destination_key)

    return ExportPushed.create(
        store_id=state.configured_store.id,
        local_path=local_path,
        destination_key=destination_key,
    )
