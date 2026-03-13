"""
Storage Commands - Command DTOs for storage operations.

All commands are immutable (frozen) and contain only primitive types.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigureStoreCommand:
    """Command to configure an S3 data store."""

    bucket_name: str
    region: str
    prefix: str = ""
    dvc_remote_name: str = "origin"


@dataclass(frozen=True)
class ScanStoreCommand:
    """Command to scan/browse files in the data store."""

    prefix: str = ""


@dataclass(frozen=True)
class PullFileCommand:
    """Command to pull a file from S3 into local project."""

    key: str
    local_path: str


@dataclass(frozen=True)
class PushExportCommand:
    """Command to push a coded export to S3."""

    local_path: str
    destination_key: str
