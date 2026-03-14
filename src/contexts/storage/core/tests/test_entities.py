"""
Storage Context: Entity Unit Tests (TDD RED phase)

Tests for DataStore and RemoteFile entities.
"""

from __future__ import annotations

from datetime import UTC, datetime

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


@allure.story("QC-047.01 Domain Entities")
class TestDataStoreEntity:
    """Unit tests for DataStore entity."""

    @allure.title("DataStore can be created with valid S3 config")
    def test_create_data_store_with_valid_config(self):
        from src.contexts.storage.core.entities import DataStore, StoreId

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
            prefix="study-2026/",
            dvc_remote_name="origin",
        )

        assert store.bucket_name == "research-data"
        assert store.region == "us-east-1"
        assert store.prefix == "study-2026/"
        assert store.dvc_remote_name == "origin"

    @allure.title("DataStore is immutable")
    def test_data_store_is_immutable(self):
        from src.contexts.storage.core.entities import DataStore, StoreId

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )

        with pytest.raises(AttributeError):
            store.bucket_name = "other-bucket"


@allure.story("QC-047.01 Domain Entities")
class TestRemoteFileEntity:
    """Unit tests for RemoteFile value object."""

    @allure.title("RemoteFile captures S3 object metadata")
    def test_create_remote_file(self):
        from src.contexts.storage.core.entities import RemoteFile

        rf = RemoteFile(
            key="raw/firebase_export.json",
            size_bytes=1024,
            last_modified=datetime(2026, 3, 1, tzinfo=UTC),
            etag="abc123",
        )

        assert rf.key == "raw/firebase_export.json"
        assert rf.size_bytes == 1024
        assert rf.filename == "firebase_export.json"

    @allure.title("RemoteFile.filename extracts name from key")
    def test_remote_file_filename(self):
        from src.contexts.storage.core.entities import RemoteFile

        rf = RemoteFile(
            key="deeply/nested/path/report.csv",
            size_bytes=512,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert rf.filename == "report.csv"

    @allure.title("RemoteFile.extension extracts file extension")
    def test_remote_file_extension(self):
        from src.contexts.storage.core.entities import RemoteFile

        rf = RemoteFile(
            key="data/export.json",
            size_bytes=100,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert rf.extension == ".json"
