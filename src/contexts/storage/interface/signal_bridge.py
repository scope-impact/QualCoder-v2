"""
Storage Signal Bridge - Domain Events to Qt Signals

Converts domain events from the Storage context into Qt signals
for reactive UI updates.

Usage:
    from src.contexts.storage.interface.signal_bridge import StorageSignalBridge

    bridge = StorageSignalBridge.instance(event_bus)
    bridge.store_configured.connect(on_store_configured)
    bridge.start()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from PySide6.QtCore import Signal

from src.contexts.storage.core.events import (
    ExportPushed,
    FilePulled,
    StoreConfigured,
    StoreScanned,
)
from src.shared.infra.signal_bridge.base import BaseSignalBridge, EventConverter

# =============================================================================
# Payloads - Data transferred via signals
# =============================================================================


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class StorePayload:
    """Payload for store configuration signals."""

    event_type: str
    store_id: str
    bucket_name: str
    region: str
    prefix: str = ""
    dvc_remote_name: str = "origin"
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class ScanPayload:
    """Payload for store scan signals."""

    event_type: str
    store_id: str
    prefix: str
    file_count: int
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class PullPayload:
    """Payload for file pull signals."""

    event_type: str
    store_id: str
    key: str
    local_path: str
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


@dataclass(frozen=True)
class PushPayload:
    """Payload for export push signals."""

    event_type: str
    store_id: str
    local_path: str
    destination_key: str
    timestamp: datetime = field(default_factory=_now)
    session_id: str = "local"
    is_ai_action: bool = False


# =============================================================================
# Converters - Transform events to payloads
# =============================================================================


class StoreConfiguredConverter(EventConverter):
    """Convert StoreConfigured event to payload."""

    def convert(self, event: StoreConfigured) -> StorePayload:
        return StorePayload(
            event_type="storage.store_configured",
            store_id=event.store_id.value,
            bucket_name=event.bucket_name,
            region=event.region,
            prefix=event.prefix,
            dvc_remote_name=event.dvc_remote_name,
        )


class StoreScannedConverter(EventConverter):
    """Convert StoreScanned event to payload."""

    def convert(self, event: StoreScanned) -> ScanPayload:
        return ScanPayload(
            event_type="storage.store_scanned",
            store_id=event.store_id.value,
            prefix=event.prefix,
            file_count=event.file_count,
        )


class FilePulledConverter(EventConverter):
    """Convert FilePulled event to payload."""

    def convert(self, event: FilePulled) -> PullPayload:
        return PullPayload(
            event_type="storage.file_pulled",
            store_id=event.store_id.value,
            key=event.key,
            local_path=event.local_path,
        )


class ExportPushedConverter(EventConverter):
    """Convert ExportPushed event to payload."""

    def convert(self, event: ExportPushed) -> PushPayload:
        return PushPayload(
            event_type="storage.export_pushed",
            store_id=event.store_id.value,
            local_path=event.local_path,
            destination_key=event.destination_key,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class StorageSignalBridge(BaseSignalBridge):
    """
    Signal bridge for the Storage bounded context.

    Emits Qt signals when storage domain events occur.

    Signals:
        store_configured: Emitted when S3 store is configured
        store_scanned: Emitted when store files are discovered
        file_pulled: Emitted when a file is pulled from S3
        export_pushed: Emitted when an export is pushed to S3
    """

    # Store signals
    store_configured = Signal(object)
    store_scanned = Signal(object)

    # File transfer signals
    file_pulled = Signal(object)
    export_pushed = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "storage"

    def _register_converters(self) -> None:
        """Register all event converters."""
        self.register_converter(
            "storage.store_configured",
            StoreConfiguredConverter(),
            "store_configured",
        )
        self.register_converter(
            "storage.store_scanned",
            StoreScannedConverter(),
            "store_scanned",
        )
        self.register_converter(
            "storage.file_pulled",
            FilePulledConverter(),
            "file_pulled",
        )
        self.register_converter(
            "storage.export_pushed",
            ExportPushedConverter(),
            "export_pushed",
        )
