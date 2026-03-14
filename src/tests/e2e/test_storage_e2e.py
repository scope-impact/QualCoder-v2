"""
Storage Context: E2E Tests

Full workflow tests: configure → scan → pull → push.
Tests MCP tool integration, signal bridge, repository persistence,
and AppContext wiring.
Uses moto for S3 mock and a mock DVC gateway — no real AWS or DVC CLI.
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtWidgets import QApplication

from src.contexts.storage.infra.dvc_gateway import DvcResult
from src.tests.e2e.helpers import attach_screenshot
from src.tests.e2e.utils import DocScreenshot

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


# =============================================================================
# MCP Tool E2E Tests
# =============================================================================


@allure.story("QC-047.06 MCP Storage Tools")
class TestStorageMCPTools:
    """E2E tests for storage MCP tool handlers."""

    @allure.title("AC #6.1: configure_datastore MCP tool")
    def test_configure_datastore_tool(self, mock_s3):
        from src.contexts.storage.interface.mcp_tools import StorageTools

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()

        # Create a context-like object for StorageTools
        ctx = _MockStorageToolsContext(store_repo, mock_s3, dvc, event_bus)
        tools = StorageTools(ctx=ctx)

        result = tools.execute(
            "configure_datastore",
            {"bucket_name": "research-data", "region": "us-east-1"},
        )

        from returns.result import Success

        assert isinstance(result, Success), f"Expected Success, got {result}"
        data = result.unwrap()
        assert data["bucket_name"] == "research-data"
        assert data["region"] == "us-east-1"
        assert store_repo.get() is not None

    @allure.title("AC #6.2: scan_datastore MCP tool")
    def test_scan_datastore_tool(self, mock_s3):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand
        from src.contexts.storage.interface.mcp_tools import StorageTools

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()

        # First configure store
        configure_store(
            command=ConfigureStoreCommand(
                bucket_name="research-data", region="us-east-1"
            ),
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        ctx = _MockStorageToolsContext(store_repo, mock_s3, dvc, event_bus)
        tools = StorageTools(ctx=ctx)

        result = tools.execute("scan_datastore", {"prefix": "raw/"})
        data = result.unwrap()
        assert data["file_count"] == 2

    @allure.title("AC #6.3: configure_datastore fails with invalid bucket")
    def test_configure_invalid_bucket_fails(self, mock_s3):
        from src.contexts.storage.interface.mcp_tools import StorageTools

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()

        ctx = _MockStorageToolsContext(store_repo, mock_s3, dvc, event_bus)
        tools = StorageTools(ctx=ctx)

        result = tools.execute(
            "configure_datastore",
            {"bucket_name": "AB", "region": "us-east-1"},  # Too short, uppercase
        )

        from returns.result import Failure

        assert isinstance(result, Failure)

    @allure.title("AC #6.4: tool returns error when no project open")
    def test_scan_no_project_returns_error(self):
        from src.contexts.storage.interface.mcp_tools import StorageTools

        ctx = _NullStorageToolsContext()
        tools = StorageTools(ctx=ctx)

        result = tools.execute("scan_datastore", {})

        from returns.result import Failure

        assert isinstance(result, Failure)
        assert "No project open" in result.failure()


# =============================================================================
# Repository Persistence E2E Tests
# =============================================================================


@allure.story("QC-047.01 Store Repository Persistence")
class TestStoreRepositoryPersistence:
    """E2E tests: real SQLite persistence for DataStore config."""

    @allure.title("AC #1.1: Save and retrieve store config from SQLite")
    def test_save_and_get_store_config(self, db_connection):
        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.infra.store_repository import SQLiteStoreRepository

        repo = SQLiteStoreRepository(db_connection)

        # Initially empty
        assert repo.get() is None
        assert repo.exists() is False

        # Save config
        store = DataStore(
            id=StoreId.new(),
            bucket_name="my-research-bucket",
            region="eu-west-1",
            prefix="project-alpha/",
            dvc_remote_name="s3remote",
        )
        repo.save(store)

        # Retrieve
        loaded = repo.get()
        assert loaded is not None
        assert loaded.bucket_name == "my-research-bucket"
        assert loaded.region == "eu-west-1"
        assert loaded.prefix == "project-alpha/"
        assert loaded.dvc_remote_name == "s3remote"
        assert repo.exists() is True

    @allure.title("AC #1.2: Save replaces existing config (singleton)")
    def test_save_replaces_existing(self, db_connection):
        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.infra.store_repository import SQLiteStoreRepository

        repo = SQLiteStoreRepository(db_connection)

        # Save first config
        store1 = DataStore(
            id=StoreId.new(), bucket_name="bucket-one", region="us-east-1"
        )
        repo.save(store1)
        assert repo.get().bucket_name == "bucket-one"

        # Save second config — should replace
        store2 = DataStore(
            id=StoreId.new(), bucket_name="bucket-two", region="eu-west-1"
        )
        repo.save(store2)
        loaded = repo.get()
        assert loaded.bucket_name == "bucket-two"
        assert loaded.region == "eu-west-1"


# =============================================================================
# AppContext Wiring E2E Tests
# =============================================================================


@allure.story("QC-047.11 AppContext Storage Wiring")
class TestStorageContextWiring:
    """E2E test: storage context is created when a project is opened."""

    @allure.title("AC #11.1: StorageContext created on project open")
    def test_storage_context_created_on_open(self, tmp_path):
        from src.shared.infra.app_context import create_app_context

        ctx = create_app_context()

        # Before project open, storage context should be None
        assert ctx.storage_context is None

        # Create and open project
        project_path = tmp_path / "test_storage.qda"
        create_result = ctx.create_project("Test", str(project_path))
        assert create_result.is_success

        open_result = ctx.open_project(str(project_path))
        assert open_result.is_success

        # After opening, storage context should be available
        assert ctx.storage_context is not None
        assert ctx.storage_context.store_repo is not None
        assert ctx.storage_context.s3_scanner is not None
        assert ctx.storage_context.dvc_gateway is not None

        # Close project — storage context should be cleared
        ctx.close_project()
        assert ctx.storage_context is None


# =============================================================================
# DataStoreViewModel E2E Tests
# =============================================================================


@allure.story("QC-047.08 Import from S3 Dialog")
class TestDataStoreViewModel:
    """E2E tests for DataStoreViewModel — configure, scan, cross-reference."""

    @allure.title("AC #8.1: ViewModel reports is_configured correctly")
    def test_is_configured_false_then_true(self, mock_s3):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand
        from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
            DataStoreViewModel,
        )

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=mock_s3)

        vm = DataStoreViewModel(
            store_repo=store_repo,
            source_repo=_MockSourceRepo([]),
            s3_scanner=scanner,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        with allure.step("Initially not configured"):
            assert vm.is_configured is False
            assert vm.get_config() is None

        with allure.step("Configure store"):
            configure_store(
                command=ConfigureStoreCommand(
                    bucket_name="research-data", region="us-east-1"
                ),
                store_repo=store_repo,
                dvc_gateway=dvc,
                event_bus=event_bus,
            )

        with allure.step("Now configured"):
            assert vm.is_configured is True
            config = vm.get_config()
            assert config["bucket_name"] == "research-data"

    @allure.title("AC #8.2: Scan returns remote files")
    def test_scan_returns_remote_files(self, mock_s3):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand
        from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
            DataStoreViewModel,
        )

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=mock_s3)

        configure_store(
            command=ConfigureStoreCommand(
                bucket_name="research-data", region="us-east-1"
            ),
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        vm = DataStoreViewModel(
            store_repo=store_repo,
            source_repo=_MockSourceRepo([]),
            s3_scanner=scanner,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        with allure.step("Scan returns files"):
            files = vm.scan()
            assert len(files) == 3  # 3 seeded files in mock_s3

    @allure.title("AC #8.3: Already-imported files are identified")
    def test_imported_filenames_cross_reference(self, mock_s3):
        from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
            DataStoreViewModel,
        )

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=mock_s3)

        # Simulate that interview_001.txt is already imported
        existing_sources = [_MockSource("interview_001.txt")]
        vm = DataStoreViewModel(
            store_repo=store_repo,
            source_repo=_MockSourceRepo(existing_sources),
            s3_scanner=scanner,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        with allure.step("Cross-reference identifies imported files"):
            imported = vm.get_imported_filenames()
            assert "interview_001.txt" in imported
            assert "firebase_export.json" not in imported


# =============================================================================
# Settings Data Store Tab E2E Tests
# =============================================================================


@allure.story("QC-047.07 Settings Data Store Configuration")
class TestSettingsDataStoreConfig:
    """E2E tests for SettingsViewModel data store methods."""

    @allure.title("AC #7.1: SettingsViewModel exposes data store config")
    def test_settings_viewmodel_data_store_config(self, mock_s3):
        from src.contexts.storage.core.commandHandlers.configure_store import (
            configure_store,
        )
        from src.contexts.storage.core.commands import ConfigureStoreCommand
        from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
            DataStoreViewModel,
        )

        store_repo = SimpleStoreRepo()
        dvc = MockDvcGateway()
        event_bus = SimpleEventBus()
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        scanner = S3Scanner(client=mock_s3)

        # Configure store first
        configure_store(
            command=ConfigureStoreCommand(
                bucket_name="research-data",
                region="us-east-1",
                prefix="project-alpha/",
            ),
            store_repo=store_repo,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        data_store_vm = DataStoreViewModel(
            store_repo=store_repo,
            source_repo=_MockSourceRepo([]),
            s3_scanner=scanner,
            dvc_gateway=dvc,
            event_bus=event_bus,
        )

        # Wire into SettingsViewModel
        from src.contexts.settings.infra.user_settings_repository import (
            UserSettingsRepository,
        )
        from src.contexts.settings.presentation.viewmodels.settings_viewmodel import (
            SettingsViewModel,
        )
        from src.shared.presentation.services.settings_service import SettingsService

        settings_repo = UserSettingsRepository()
        settings_service = SettingsService(settings_repo, event_bus=event_bus)
        settings_vm = SettingsViewModel(settings_provider=settings_service)
        settings_vm.set_data_store_viewmodel(data_store_vm)

        with allure.step("Settings VM returns data store config"):
            config = settings_vm.get_data_store_config()
            assert config is not None
            assert config["bucket_name"] == "research-data"
            assert config["prefix"] == "project-alpha/"

    @allure.title("AC #7.2: SettingsViewModel returns None when no data store")
    def test_settings_viewmodel_no_data_store(self):
        from src.contexts.settings.infra.user_settings_repository import (
            UserSettingsRepository,
        )
        from src.contexts.settings.presentation.viewmodels.settings_viewmodel import (
            SettingsViewModel,
        )
        from src.shared.presentation.services.settings_service import SettingsService

        event_bus = SimpleEventBus()
        settings_repo = UserSettingsRepository()
        settings_service = SettingsService(settings_repo, event_bus=event_bus)
        settings_vm = SettingsViewModel(settings_provider=settings_service)

        with allure.step("No data store VM wired"):
            assert settings_vm.get_data_store_config() is None


# =============================================================================
# Test Helpers
# =============================================================================


class _MockSource:
    """Minimal source stub for cross-referencing."""

    def __init__(self, name: str):
        self.name = name


class _MockSourceRepo:
    """Minimal source repository stub."""

    def __init__(self, sources: list):
        self._sources = sources

    def get_all(self) -> list:
        return self._sources


class _MockStorageContext:
    """Bundles repos/gateways for MCP tool tests."""

    def __init__(self, store_repo, s3_client, dvc_gateway):
        self.store_repo = store_repo
        self.dvc_gateway = dvc_gateway
        from src.contexts.storage.infra.s3_scanner import S3Scanner

        self.s3_scanner = S3Scanner(client=s3_client)


class _MockState:
    """Minimal project state stub."""

    project = True  # Non-None means project is open


class _MockStorageToolsContext:
    """Minimal context satisfying StorageToolsContext protocol."""

    def __init__(self, store_repo, s3_client, dvc_gateway, event_bus):
        self._storage = _MockStorageContext(store_repo, s3_client, dvc_gateway)
        self._event_bus = event_bus

    @property
    def state(self):
        return _MockState()

    @property
    def event_bus(self):
        return self._event_bus

    @property
    def storage_context(self):
        return self._storage


class _NullStorageToolsContext:
    """Context with no project open."""

    @property
    def state(self):
        return _MockState()

    @property
    def event_bus(self):
        return SimpleEventBus()

    @property
    def storage_context(self):
        return None


# =============================================================================
# Screenshot E2E Tests — Full Wiring with Moto S3
# =============================================================================


@pytest.fixture
def screenshot_s3():
    """Create mock S3 with realistic research files for screenshot capture."""
    import boto3
    from moto import mock_aws

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="qualcoder-research")

        # Seed realistic research files
        s3.put_object(
            Bucket="qualcoder-research",
            Key="project-alpha/raw/interview_001.txt",
            Body=b"Researcher: Tell me about your experience.\nParticipant: ...",
        )
        s3.put_object(
            Bucket="qualcoder-research",
            Key="project-alpha/raw/interview_002.txt",
            Body=b"Researcher: How did you feel?\nParticipant: ...",
        )
        s3.put_object(
            Bucket="qualcoder-research",
            Key="project-alpha/raw/focus_group.mp3",
            Body=b"\x00" * 15_000,  # simulated audio
        )
        s3.put_object(
            Bucket="qualcoder-research",
            Key="project-alpha/processed/profiles.csv",
            Body=b"participant_id,sessions\nu001,12\nu002,3",
        )

        yield s3


@allure.story("QC-047.08 Import from S3 Dialog")
class TestImportFromS3DialogScreenshot:
    """Open Import from S3 dialog through the real wired app flow with moto S3."""

    @allure.title("DOC: Import from S3 triggered from FileManager toolbar")
    def test_import_from_s3_via_toolbar(self, wired_app, screenshot_s3):
        """Full wired flow: configure store → swap scanner to moto S3
        → click Import from S3 → dialog scans real (mocked) S3 bucket
        → renders file table with status indicators.

        Verifies:
        - DataStoreViewModel is wired to FileManager
        - S3Scanner.list_files goes through real code path with moto
        - ImportFromS3Dialog renders files correctly
        """
        from unittest.mock import patch

        from src.contexts.storage.core.entities import DataStore, StoreId
        from src.contexts.storage.infra.s3_scanner import S3Scanner
        from src.contexts.storage.presentation.dialogs.import_from_s3_dialog import (
            ImportFromS3Dialog,
        )

        file_manager = wired_app["screens"]["files"]
        storage_ctx = wired_app["ctx"].storage_context

        with allure.step("Verify DataStoreViewModel is wired to FileManager"):
            assert file_manager._data_store_vm is not None, (
                "DataStoreViewModel not wired — check main.py _wire_viewmodels()"
            )

        with allure.step("Configure store and swap S3 client to moto"):
            # Configure a store via the real store_repo
            store = DataStore(
                id=StoreId.new(),
                bucket_name="qualcoder-research",
                region="us-east-1",
                prefix="project-alpha/",
                dvc_remote_name="origin",
            )
            storage_ctx.store_repo.save(store)

            # Swap the _client on the existing S3Scanner that the ViewModel holds
            # This keeps the real S3Scanner.list_files code path intact
            file_manager._data_store_vm._s3_scanner = S3Scanner(
                client=screenshot_s3
            )

            # Re-enable the menu item now that store is configured
            file_manager._page.set_import_from_s3_enabled(True)

        with allure.step("Click Import from S3 — dialog scans moto S3"):
            # Intercept exec() so the dialog doesn't block
            dialogs_captured = []

            def capture_exec(dialog_self):
                dialog_self.resize(650, 400)
                dialog_self.show()
                QApplication.processEvents()
                dialogs_captured.append(dialog_self)

            with patch.object(ImportFromS3Dialog, "exec", capture_exec):
                file_manager._on_import_from_s3_clicked()
                QApplication.processEvents()

            assert len(dialogs_captured) == 1, (
                "ImportFromS3Dialog was not opened — wiring broken"
            )

        with allure.step("Verify dialog shows files from moto S3"):
            dialog = dialogs_captured[0]
            row_count = dialog._table.rowCount()
            assert row_count == 4, f"Expected 4 S3 files, got {row_count}"

            # Verify status column shows "remote" for unchecked files
            status_item = dialog._table.item(1, 2)
            assert status_item is not None
            assert status_item.text() in ("remote", "imported")

        with allure.step("Capture screenshot for documentation"):
            attach_screenshot(dialog, "ImportFromS3Dialog - via Toolbar")
            DocScreenshot.capture(
                dialog, "import-from-s3-dialog", max_width=800
            )
            dialog.close()


@allure.story("QC-047.07 Settings Data Store Configuration")
class TestSettingsDataStoreScreenshot:
    """Open Settings, navigate to Data Store tab through the real wired app."""

    @allure.title("DOC: Settings > Data Store tab via real app wiring")
    def test_settings_data_store_via_app(self, wired_app):
        """Open Settings dialog through the real app flow and navigate to Data Store.

        Verifies the full wiring:
        _on_settings_clicked → DialogService.show_settings_dialog(data_store_vm=...)
        → SettingsDialog has Data Store section wired.
        """
        app = wired_app["app"]

        with allure.step("Open Settings dialog through real app flow"):
            dialogs_captured = []
            original_show = app._dialog_service.show_settings_dialog

            def capture_show(*args, **kwargs):
                kwargs["blocking"] = False
                dialog = original_show(*args, **kwargs)
                dialogs_captured.append(dialog)
                return dialog

            app._dialog_service.show_settings_dialog = capture_show
            app._on_settings_clicked()
            QApplication.processEvents()

            assert len(dialogs_captured) == 1, (
                "Settings dialog was not opened — wiring broken"
            )
            dialog = dialogs_captured[0]

        with allure.step("Navigate to Data Store tab"):
            # Find tab by text rather than hardcoding index
            sidebar = dialog._sidebar
            ds_row = None
            for i in range(sidebar.count()):
                if sidebar.item(i).text() == "Data Store":
                    ds_row = i
                    break
            assert ds_row is not None, "Data Store tab not found in sidebar"

            sidebar.setCurrentRow(ds_row)
            QApplication.processEvents()
            assert dialog._content_stack.currentIndex() == ds_row

        with allure.step("Fill sample config and capture screenshot"):
            dialog._ds_bucket.setText("qualcoder-research")
            dialog._ds_region.setCurrentText("us-east-1")
            dialog._ds_prefix.setText("project-alpha/")
            dialog._ds_remote.setText("origin")
            dialog._ds_status.setText("Connected")
            dialog._ds_status.setStyleSheet("color: green; font-size: 11px;")
            QApplication.processEvents()

            attach_screenshot(dialog, "SettingsDialog - Data Store Tab")
            DocScreenshot.capture(dialog, "settings-data-store", max_width=800)

        dialog.close()
