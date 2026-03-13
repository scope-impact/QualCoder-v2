"""
Storage Context: E2E Tests (TDD RED phase)

Full workflow tests: configure → scan → pull → push.
Uses moto for S3 mock — no real AWS.
"""

from __future__ import annotations

import pytest
import allure

from datetime import UTC, datetime
from pathlib import Path


pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


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

    @allure.title("AC #1-4: Full storage workflow with S3")
    def test_full_configure_scan_pull_push_workflow(self, mock_s3, tmp_path):
        from src.contexts.storage.core.commands import (
            ConfigureStoreCommand,
            ScanStoreCommand,
            PullFileCommand,
            PushExportCommand,
        )
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.core.commandHandlers.pull_file import pull_file
        from src.contexts.storage.core.commandHandlers.push_export import push_export
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        # Setup
        scanner = S3Scanner(client=mock_s3)

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

        store_repo = SimpleStoreRepo()
        event_bus = SimpleEventBus()

        # Step 1: Configure store
        with allure.step("Configure S3 data store"):
            configure_result = configure_store(
                command=ConfigureStoreCommand(
                    bucket_name="research-data",
                    region="us-east-1",
                    prefix="",
                    dvc_remote_name="origin",
                ),
                store_repo=store_repo,
                event_bus=event_bus,
            )
            assert configure_result.success is True
            assert store_repo.get() is not None

        # Step 2: Scan store
        with allure.step("Scan data store for available files"):
            scan_result = scan_store(
                command=ScanStoreCommand(prefix="raw/"),
                store_repo=store_repo,
                s3_scanner=scanner,
                event_bus=event_bus,
            )
            assert scan_result.success is True
            assert len(scan_result.data) == 2  # 2 files under raw/

        # Step 3: Pull file
        with allure.step("Pull firebase export from S3"):
            local_file = tmp_path / "firebase_export.json"
            pull_result = pull_file(
                command=PullFileCommand(
                    key="raw/firebase_export.json",
                    local_path=str(local_file),
                ),
                store_repo=store_repo,
                s3_scanner=scanner,
                event_bus=event_bus,
            )
            assert pull_result.success is True
            assert local_file.exists()
            assert "session_start" in local_file.read_text()

        # Step 4: Push export
        with allure.step("Push coded export back to S3"):
            export_file = tmp_path / "codebook.txt"
            export_file.write_text("Theme: User Engagement\nTheme: Frustration Points")

            push_result = push_export(
                command=PushExportCommand(
                    local_path=str(export_file),
                    destination_key="coded/codebook.txt",
                ),
                store_repo=store_repo,
                s3_scanner=scanner,
                event_bus=event_bus,
            )
            assert push_result.success is True

        # Verify the push landed in S3
        with allure.step("Verify export exists in S3"):
            obj = mock_s3.get_object(
                Bucket="research-data", Key="coded/codebook.txt"
            )
            body = obj["Body"].read().decode()
            assert "User Engagement" in body

        # Verify all events were published
        with allure.step("Verify domain events published"):
            event_types = [type(e).__name__ for e in event_bus.published]
            assert "StoreConfigured" in event_types
            assert "StoreScanned" in event_types
            assert "FilePulled" in event_types
            assert "ExportPushed" in event_types

    @allure.title("AC #8: Works offline — scan fails gracefully without config")
    def test_scan_without_config_fails_gracefully(self):
        from src.contexts.storage.core.commands import ScanStoreCommand
        from src.contexts.storage.core.commandHandlers.scan_store import scan_store
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        class SimpleStoreRepo:
            def get(self):
                return None

            def save(self, store):
                pass

        class SimpleEventBus:
            def __init__(self):
                self.published = []

            def publish(self, event):
                self.published.append(event)

        store_repo = SimpleStoreRepo()
        event_bus = SimpleEventBus()

        # Scanner won't be called since store is not configured
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
