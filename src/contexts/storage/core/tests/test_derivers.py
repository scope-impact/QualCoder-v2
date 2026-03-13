"""
Storage Context: Deriver Unit Tests (TDD RED phase)

Tests for pure event derivation functions.
"""

from __future__ import annotations

import pytest
import allure

from datetime import UTC, datetime


pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


@allure.story("QC-047.01 Domain Derivers")
class TestDeriveConfigureStore:
    """Tests for derive_configure_store deriver."""

    @allure.title("Valid config produces StoreConfigured event")
    def test_valid_config_produces_success_event(self):
        from src.contexts.storage.core.derivers import derive_configure_store, StorageState
        from src.contexts.storage.core.events import StoreConfigured

        state = StorageState()
        result = derive_configure_store(
            bucket_name="research-data",
            region="us-east-1",
            prefix="study/",
            dvc_remote_name="origin",
            state=state,
        )

        assert isinstance(result, StoreConfigured)
        assert result.bucket_name == "research-data"
        assert result.region == "us-east-1"

    @allure.title("Empty bucket name produces failure event")
    def test_empty_bucket_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_configure_store, StorageState
        from src.contexts.storage.core.failure_events import StoreNotConfigured

        state = StorageState()
        result = derive_configure_store(
            bucket_name="",
            region="us-east-1",
            prefix="",
            dvc_remote_name="origin",
            state=state,
        )

        assert isinstance(result, StoreNotConfigured)
        assert result.reason == "INVALID_BUCKET"

    @allure.title("Empty region produces failure event")
    def test_empty_region_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_configure_store, StorageState
        from src.contexts.storage.core.failure_events import StoreNotConfigured

        state = StorageState()
        result = derive_configure_store(
            bucket_name="research-data",
            region="",
            prefix="",
            dvc_remote_name="origin",
            state=state,
        )

        assert isinstance(result, StoreNotConfigured)
        assert result.reason == "INVALID_REGION"


@allure.story("QC-047.01 Domain Derivers")
class TestDeriveScanStore:
    """Tests for derive_scan_store deriver."""

    @allure.title("Scan with configured store produces StoreScanned event")
    def test_scan_with_configured_store(self):
        from src.contexts.storage.core.derivers import derive_scan_store, StorageState
        from src.contexts.storage.core.entities import DataStore, RemoteFile, StoreId
        from src.contexts.storage.core.events import StoreScanned

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        files = [
            RemoteFile(
                key="raw/data.json",
                size_bytes=1024,
                last_modified=datetime(2026, 3, 1, tzinfo=UTC),
            ),
        ]
        state = StorageState(configured_store=store)

        result = derive_scan_store(
            discovered_files=tuple(files),
            prefix="raw/",
            state=state,
        )

        assert isinstance(result, StoreScanned)
        assert len(result.files) == 1

    @allure.title("Scan without configured store produces failure")
    def test_scan_without_store_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_scan_store, StorageState
        from src.contexts.storage.core.failure_events import StoreNotScanned

        state = StorageState()  # no store configured

        result = derive_scan_store(
            discovered_files=(),
            prefix="",
            state=state,
        )

        assert isinstance(result, StoreNotScanned)
        assert result.reason == "NOT_CONFIGURED"


@allure.story("QC-047.01 Domain Derivers")
class TestDerivePullFile:
    """Tests for derive_pull_file deriver."""

    @allure.title("Pull valid key produces FilePulled event")
    def test_pull_valid_key(self):
        from src.contexts.storage.core.derivers import derive_pull_file, StorageState
        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.core.events import FilePulled

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        state = StorageState(configured_store=store)

        result = derive_pull_file(
            key="raw/firebase_export.json",
            local_path="/tmp/firebase_export.json",
            state=state,
        )

        assert isinstance(result, FilePulled)
        assert result.key == "raw/firebase_export.json"

    @allure.title("Pull with empty key produces failure")
    def test_pull_empty_key_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_pull_file, StorageState
        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.core.failure_events import FileNotPulled

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        state = StorageState(configured_store=store)

        result = derive_pull_file(
            key="",
            local_path="/tmp/file.json",
            state=state,
        )

        assert isinstance(result, FileNotPulled)
        assert result.reason == "INVALID_KEY"

    @allure.title("Pull without configured store produces failure")
    def test_pull_without_store_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_pull_file, StorageState
        from src.contexts.storage.core.failure_events import FileNotPulled

        state = StorageState()

        result = derive_pull_file(
            key="raw/data.json",
            local_path="/tmp/data.json",
            state=state,
        )

        assert isinstance(result, FileNotPulled)
        assert result.reason == "NOT_CONFIGURED"


@allure.story("QC-047.01 Domain Derivers")
class TestDerivePushExport:
    """Tests for derive_push_export deriver."""

    @allure.title("Push valid export produces ExportPushed event")
    def test_push_valid_export(self):
        from src.contexts.storage.core.derivers import derive_push_export, StorageState
        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.core.events import ExportPushed

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        state = StorageState(configured_store=store)

        result = derive_push_export(
            local_path="/project/coded/codebook.txt",
            destination_key="coded/codebook.txt",
            state=state,
        )

        assert isinstance(result, ExportPushed)
        assert result.destination_key == "coded/codebook.txt"

    @allure.title("Push without store produces failure")
    def test_push_without_store_produces_failure(self):
        from src.contexts.storage.core.derivers import derive_push_export, StorageState
        from src.contexts.storage.core.failure_events import ExportNotPushed

        state = StorageState()

        result = derive_push_export(
            local_path="/project/coded/codebook.txt",
            destination_key="coded/codebook.txt",
            state=state,
        )

        assert isinstance(result, ExportNotPushed)
        assert result.reason == "NOT_CONFIGURED"
