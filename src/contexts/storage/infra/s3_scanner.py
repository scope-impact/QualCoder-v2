"""
Storage Infrastructure: S3 Scanner

Direct boto3 wrapper for S3 object discovery, download, and upload.
"""

from __future__ import annotations

import logging
from typing import Any

from src.contexts.storage.core.entities import RemoteFile

logger = logging.getLogger("qualcoder.storage.infra")


class S3Scanner:
    """
    Wraps boto3 S3 client for file discovery and transfer.

    Injected with a boto3 S3 client — can be real or moto-mocked.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def list_files(self, bucket: str, prefix: str = "") -> list[RemoteFile]:
        """
        List files in an S3 bucket, optionally filtered by prefix.

        Returns:
            List of RemoteFile value objects.
        """
        logger.debug("list_files: bucket=%s, prefix=%s", bucket, prefix)

        kwargs: dict[str, str] = {"Bucket": bucket}
        if prefix:
            kwargs["Prefix"] = prefix

        response = self._client.list_objects_v2(**kwargs)
        contents = response.get("Contents", [])

        files = [
            RemoteFile(
                key=obj["Key"],
                size_bytes=obj["Size"],
                last_modified=obj["LastModified"],
                etag=obj.get("ETag"),
            )
            for obj in contents
        ]

        logger.debug("list_files: found %d files", len(files))
        return files

    def download_file(self, bucket: str, key: str, local_path: str) -> None:
        """
        Download a file from S3 to a local path.
        """
        logger.debug("download_file: %s/%s -> %s", bucket, key, local_path)
        self._client.download_file(Bucket=bucket, Key=key, Filename=local_path)

    def upload_file(self, bucket: str, key: str, local_path: str) -> None:
        """
        Upload a local file to S3.
        """
        logger.debug("upload_file: %s -> %s/%s", local_path, bucket, key)
        self._client.upload_file(Filename=local_path, Bucket=bucket, Key=key)
