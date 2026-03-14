"""
Storage Context: E2E Tests (TDD RED phase)

Full workflow tests: configure → scan → pull → push.
Uses moto for S3 mock and a mock DVC gateway — no real AWS or DVC CLI.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.storage.infra.dvc_gateway import DvcResult

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


class SimpleStoreRepo:
    def __init__(self):
        self._store = None

    def get(self):
        return self._store

    def save(self, store):
        self._store = store


class SimpleEventBus:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)


class MockDvcGateway:
    """Mock DVC gateway for E2E tests — no real DVC CLI."""

    def __init__(self):
        self.calls: list[str] = []

    def _ok(self, op):
        self.calls.append(op)
        return DvcResult(success=True, message=f"{op} ok")

    def init(self):
        return self._ok("init")

    def remote_add(self, name, url):
        return self._ok("remote_add")

    def remote_modify(self, name, key, value):
        return self._ok("remote_modify")

    def remote_default(self, name):
        return self._ok("remote_default")

    def add(self, path):
        return self._ok("add")

    def push(self, remote=None):
        return self._ok("push")

    def pull(self, remote=None):
        return self._ok("pull")

    def status(self, remote=None):
        return self._ok("status")

    @staticmethod
    def s3_url(bucket, prefix=""):
        return f"s3://{bucket}/{prefix}" if prefix else f"s3://{bucket}"


@pytest.fixture
def mock_s3():
    """Create mock S3 environment with moto."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="research-data")

        # Seed realistic research data
        s3.put_object(
            Bucket="research-data",
            Key="raw/firebase_export.json",
            Body=b'{"events": [{"name": "session_start", "user": "u001"}]}',
        )
        s3.put_object(
            Bucket="research-data",
            Key="raw/transcripts/interview_001.txt",
            Body=b"Researcher: Tell me about your experience.\nParticipant: It was great.",
        )
        s3.put_object(
            Bucket="research-data",
            Key="processed/participant_profiles.csv",
            Body=b"participant_id,sessions,engagement_tier\nu001,12,power_user\nu002,3,casual",
        )

        yield s3


@allure.story("QC-047.10 E2E Storage Workflow")
class TestStorageFullWorkflow:
    """E2E test: configure → scan → pull → push."""

    @allure.title("AC #1-4: Full storage workflow with S3 + DVC")
    def test_full_configure_scan_pull_push_workflow(self, mock_s3, tmp_path):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commandHandlers.pull_file import pull_file
        from src.contexts.storage.core.commandHandlers.push_export import push_export
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commands import (
            ConfigureStoreCommand,
            PullFileCommand,
            PushExportCommand,
            ScanStoreCommand,
        )
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        # Setup
        scanner = S3Scanner(client=mock_s3)
        dvc = MockDvcGateway()
        store_repo = SimpleStoreRepo()
        event_bus = SimpleEventBus()

        # Step 1: Configure store (uses DVC gateway)
        with allure.step("Configure S3 data store with DVC remote"):
            configure_result = configure_store(
                command=ConfigureStoreCommand(
                    bucket_name="research-data",
                    region="us-east-1",
                    prefix="",
                    dvc_remote_name="origin",
                ),
                store_repo=store_repo,
                dvc_gateway=dvc,
                event_bus=event_bus,
            )
            assert configure_result.success is True
            assert store_repo.get() is not None
            assert "init" in dvc.calls

        # Step 2: Scan store (uses S3 scanner for discovery)
        with allure.step("Scan data store for available files"):
            scan_result = scan_store(
                command=ScanStoreCommand(prefix="raw/"),
                store_repo=store_repo,
                s3_scanner=scanner,
                event_bus=event_bus,
            )
            assert scan_result.success is True
            assert len(scan_result.data) == 2  # 2 files under raw/

        # Step 3: Pull file (uses DVC gateway)
        with allure.step("Pull firebase export via DVC"):
            local_file = tmp_path / "firebase_export.json"
            pull_result = pull_file(
                command=PullFileCommand(
                    key="raw/firebase_export.json",
                    local_path=str(local_file),
                ),
                store_repo=store_repo,
                dvc_gateway=dvc,
                event_bus=event_bus,
            )
            assert pull_result.success is True
            assert "pull" in dvc.calls

        # Step 4: Push export (uses DVC gateway)
        with allure.step("Push coded export via DVC"):
            export_file = tmp_path / "codebook.txt"
            export_file.write_text("Theme: User Engagement\nTheme: Frustration Points")

            push_result = push_export(
                command=PushExportCommand(
                    local_path=str(export_file),
                    destination_key="coded/codebook.txt",
                ),
                store_repo=store_repo,
                dvc_gateway=dvc,
                event_bus=event_bus,
            )
            assert push_result.success is True
            assert "add" in dvc.calls
            assert "push" in dvc.calls

        # Verify all events were published
        with allure.step("Verify domain events published"):
            event_types = [type(e).__name__ for e in event_bus.published]
            assert "StoreConfigured" in event_types
            assert "StoreScanned" in event_types
            assert "FilePulled" in event_types
            assert "ExportPushed" in event_types

    @allure.title("AC #8: Works offline — scan fails gracefully without config")
    def test_scan_without_config_fails_gracefully(self):
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commands import ScanStoreCommand
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        store_repo = SimpleStoreRepo()
        event_bus = SimpleEventBus()

        import boto3
        from moto import mock_aws

        with mock_aws():
            s3 = boto3.client("s3", region_name="us-east-1")
            scanner = S3Scanner(client=s3)

            result = scan_store(
                command=ScanStoreCommand(prefix=""),
                store_repo=store_repo,
                s3_scanner=scanner,
                event_bus=event_bus,
            )

            assert result.success is False
            assert "NOT_CONFIGURED" in (result.error_code or "")
