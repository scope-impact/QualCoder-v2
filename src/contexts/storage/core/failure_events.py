"""
Storage Context: Failure Events

Publishable failure events for the storage bounded context.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent


# ============================================================
# Store Failure Events
# ============================================================


@dataclass(frozen=True)
class StoreNotConfigured(FailureEvent):
    """Failure event: Store configuration failed."""

    bucket_name: str | None = None

    @classmethod
    def invalid_bucket(cls, bucket_name: str) -> StoreNotConfigured:
        """Bucket name is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="STORE_NOT_CONFIGURED/INVALID_BUCKET",
            bucket_name=bucket_name,
        )

    @classmethod
    def invalid_region(cls) -> StoreNotConfigured:
        """Region is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="STORE_NOT_CONFIGURED/INVALID_REGION",
        )

    @property
    def message(self) -> str:
        match self.reason:
            case "INVALID_BUCKET":
                return f"Invalid S3 bucket name: '{self.bucket_name}'"
            case "INVALID_REGION":
                return "AWS region cannot be empty"
            case _:
                return super().message


@dataclass(frozen=True)
class StoreNotScanned(FailureEvent):
    """Failure event: Store scan failed."""

    @classmethod
    def not_configured(cls) -> StoreNotScanned:
        """No data store configured."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="STORE_NOT_SCANNED/NOT_CONFIGURED",
        )

    @classmethod
    def connection_failed(cls, error: str) -> StoreNotScanned:
        """Could not connect to S3."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="STORE_NOT_SCANNED/CONNECTION_FAILED",
        )

    @property
    def message(self) -> str:
        match self.reason:
            case "NOT_CONFIGURED":
                return "No data store configured. Configure an S3 bucket first."
            case "CONNECTION_FAILED":
                return "Could not connect to S3. Check your credentials and network."
            case _:
                return super().message


# ============================================================
# File Transfer Failure Events
# ============================================================


@dataclass(frozen=True)
class FileNotPulled(FailureEvent):
    """Failure event: File pull failed."""

    key: str | None = None

    @classmethod
    def not_configured(cls) -> FileNotPulled:
        """No data store configured."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FILE_NOT_PULLED/NOT_CONFIGURED",
        )

    @classmethod
    def invalid_key(cls, key: str) -> FileNotPulled:
        """S3 key is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FILE_NOT_PULLED/INVALID_KEY",
            key=key,
        )

    @classmethod
    def download_failed(cls, key: str) -> FileNotPulled:
        """Download from S3 failed."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FILE_NOT_PULLED/DOWNLOAD_FAILED",
            key=key,
        )

    @property
    def message(self) -> str:
        match self.reason:
            case "NOT_CONFIGURED":
                return "No data store configured. Configure an S3 bucket first."
            case "INVALID_KEY":
                return f"Invalid S3 key: '{self.key}'"
            case "DOWNLOAD_FAILED":
                return f"Failed to download '{self.key}' from S3"
            case _:
                return super().message


@dataclass(frozen=True)
class ExportNotPushed(FailureEvent):
    """Failure event: Export push failed."""

    destination_key: str | None = None

    @classmethod
    def not_configured(cls) -> ExportNotPushed:
        """No data store configured."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="EXPORT_NOT_PUSHED/NOT_CONFIGURED",
        )

    @classmethod
    def invalid_key(cls, key: str) -> ExportNotPushed:
        """Destination key is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="EXPORT_NOT_PUSHED/INVALID_KEY",
            destination_key=key,
        )

    @classmethod
    def upload_failed(cls, key: str) -> ExportNotPushed:
        """Upload to S3 failed."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="EXPORT_NOT_PUSHED/UPLOAD_FAILED",
            destination_key=key,
        )

    @property
    def message(self) -> str:
        match self.reason:
            case "NOT_CONFIGURED":
                return "No data store configured. Configure an S3 bucket first."
            case "INVALID_KEY":
                return f"Invalid destination key: '{self.destination_key}'"
            case "UPLOAD_FAILED":
                return f"Failed to upload to '{self.destination_key}' in S3"
            case _:
                return super().message


# ============================================================
# Type Unions
# ============================================================

StorageFailureEvent = (
    StoreNotConfigured | StoreNotScanned | FileNotPulled | ExportNotPushed
)
