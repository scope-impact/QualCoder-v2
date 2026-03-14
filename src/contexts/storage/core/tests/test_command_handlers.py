"""
Storage Context: Command Handler Unit Tests (TDD RED phase)

Tests for configure_store, scan_store, pull_file, push_export handlers.
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


class MockEventBus:
    """Simple event bus for testing."""

    def __init__(self):
        self.published: list = []

    def publish(self, event):
        self.published.append(event)


class MockStoreRepository:
    """Mock store repository for testing."""

    def __init__(self):
        self._store = None

    def get(self):
        return self._store

    def save(self, store):
        self._store = store


class MockDvcGateway:
    """Mock DVC gateway for testing."""

    def __init__(self, *, fail_on: str | None = None):
        self.calls: list[str] = []
        self._fail_on = fail_on

    def _result(self, op: str):
        from src.contexts.storage.infra.dvc_gateway import DvcResult

        self.calls.append(op)
        if self._fail_on == op:
            return DvcResult(success=False, message=f"{op} failed")
        return DvcResult(success=True, message=f"{op} ok")

    def init(self):
        return self._result("init")

    def remote_add(self, name, url):
        return self._result("remote_add")

    def remote_modify(self, name, key, value):
        return self._result("remote_modify")

    def remote_default(self, name):
        return self._result("remote_default")

    def add(self, path):
        return self._result("add")

    def push(self, remote=None):
        return self._result("push")

    def pull(self, remote=None):
        return self._result("pull")

    def status(self, remote=None):
        return self._result("status")

    @staticmethod
    def s3_url(bucket, prefix=""):
        if prefix:
            prefix = prefix.strip("/")
            return f"s3://{bucket}/{prefix}"
        return f"s3://{bucket}"


class MockS3Scanner:
    """Mock S3 scanner for testing (used only by scan_store)."""

    def __init__(self, files=None):
        self._files = files or []

    def list_files(self, bucket, prefix=""):
        return [f for f in self._files if f.key.startswith(prefix)]

    def download_file(self, bucket, key, local_path):
        pass  # No-op for testing

    def sync_file(self, bucket, key, local_path):
        return True  # Simulate download occurred

    def upload_file(self, bucket, key, local_path):
        pass  # No-op for testing


@allure.story("QC-047.05 Command Handlers")
class TestConfigureStoreHandler:
    """Tests for configure_store command handler."""

    @allure.title("Configure store with valid config succeeds")
    def test_configure_store_success(self):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand

        command = ConfigureStoreCommand(
            bucket_name="research-data",
            region="us-east-1",
            prefix="study/",
            dvc_remote_name="origin",
        )
        event_bus = MockEventBus()
        store_repo = MockStoreRepository()
        dvc = MockDvcGateway()

        result = configure_store(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.bucket_name == "research-data"
        assert len(event_bus.published) == 1
        # Verify DVC was configured
        assert "init" in dvc.calls
        assert "remote_add" in dvc.calls
        assert "remote_modify" in dvc.calls
        assert "remote_default" in dvc.calls

    @allure.title("Configure store with empty bucket fails")
    def test_configure_store_empty_bucket_fails(self):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand

        command = ConfigureStoreCommand(
            bucket_name="",
            region="us-east-1",
        )
        event_bus = MockEventBus()
        store_repo = MockStoreRepository()
        dvc = MockDvcGateway()

        result = configure_store(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "INVALID_BUCKET" in (result.error_code or "")


@allure.story("QC-047.05 Command Handlers")
class TestScanStoreHandler:
    """Tests for scan_store command handler."""

    @allure.title("Scan store returns discovered files")
    def test_scan_store_success(self):
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commands import ScanStoreCommand
        from src.contexts.storage.core.entities import DataStore, RemoteFile, StoreId

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
        scanner = MockS3Scanner(files=files)
        store_repo = MockStoreRepository()
        store_repo.save(store)
        event_bus = MockEventBus()

        command = ScanStoreCommand(prefix="raw/")

        result = scan_store(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            event_bus=event_bus,
        )

        assert result.success is True
        assert len(result.data) == 1
        assert len(event_bus.published) == 1

    @allure.title("Scan store without configured store fails")
    def test_scan_store_not_configured_fails(self):
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commands import ScanStoreCommand

        scanner = MockS3Scanner()
        store_repo = MockStoreRepository()  # no store configured
        event_bus = MockEventBus()

        command = ScanStoreCommand(prefix="")

        result = scan_store(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_CONFIGURED" in (result.error_code or "")


@allure.story("QC-047.05 Command Handlers")
class TestPullFileHandler:
    """Tests for pull_file command handler."""

    @allure.title("Pull file via DVC succeeds")
    def test_pull_file_success(self):
        from src.contexts.storage.core.commandHandlers.pull_file import pull_file
        from src.contexts.storage.core.commands import PullFileCommand
        from src.contexts.storage.core.entities import DataStore, StoreId

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        dvc = MockDvcGateway()
        store_repo = MockStoreRepository()
        store_repo.save(store)
        event_bus = MockEventBus()

        command = PullFileCommand(
            key="raw/firebase_export.json",
            local_path="/tmp/firebase_export.json",
        )

        result = pull_file(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        assert result.success is True
        assert len(event_bus.published) == 1
        assert "pull" in dvc.calls


@allure.story("QC-047.05 Command Handlers")
class TestPushExportHandler:
    """Tests for push_export command handler."""

    @allure.title("Push export via DVC succeeds")
    def test_push_export_success(self):
        from src.contexts.storage.core.commandHandlers.push_export import push_export
        from src.contexts.storage.core.commands import PushExportCommand
        from src.contexts.storage.core.entities import DataStore, StoreId

        store = DataStore(
            id=StoreId(value="store_001"),
            bucket_name="research-data",
            region="us-east-1",
        )
        dvc = MockDvcGateway()
        store_repo = MockStoreRepository()
        store_repo.save(store)
        event_bus = MockEventBus()

        command = PushExportCommand(
            local_path="/project/coded/codebook.txt",
            destination_key="coded/codebook.txt",
        )

        result = push_export(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        assert result.success is True
        assert len(event_bus.published) == 1
        assert "add" in dvc.calls
        assert "push" in dvc.calls
