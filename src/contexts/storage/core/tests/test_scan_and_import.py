"""
Storage Context: Scan-and-Import Command Handler Tests (TDD RED)

Tests for scanning S3, pulling files, and auto-routing to the right importer.
"""

from __future__ import annotations

import pytest
import allure

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 S3 Data Store"),
]


# ============================================================
# Test Helpers
# ============================================================


class MockEventBus:
    def __init__(self):
        self.published: list = []

    def publish(self, event):
        self.published.append(event)


class MockStoreRepository:
    def __init__(self, store=None):
        self._store = store

    def get(self):
        return self._store

    def save(self, store):
        self._store = store


class MockS3Scanner:
    def __init__(self, files=None, file_contents=None):
        from src.contexts.storage.core.entities import RemoteFile

        self._files = files or []
        self._file_contents = file_contents or {}

    def list_files(self, bucket, prefix=""):
        return [f for f in self._files if f.key.startswith(prefix)]

    def download_file(self, bucket, key, local_path):
        content = self._file_contents.get(key, f"content of {key}")
        Path(local_path).write_text(content)


class MockImporter:
    """Simulates an import handler."""

    def __init__(self, success=True):
        self._success = success
        self.called_with: list[str] = []

    def __call__(self, source_path: str) -> dict:
        from src.shared.common.operation_result import OperationResult

        self.called_with.append(source_path)
        if self._success:
            return OperationResult.ok(data={"source_path": source_path, "imported": True})
        return OperationResult.fail(error="Import failed", error_code="IMPORT_FAILED")


def _make_store():
    from src.contexts.storage.core.entities import DataStore, StoreId

    return DataStore(
        id=StoreId(value="store_001"),
        bucket_name="research-data",
        region="us-east-1",
    )


def _make_remote_file(key, size=1024):
    from src.contexts.storage.core.entities import RemoteFile

    return RemoteFile(
        key=key,
        size_bytes=size,
        last_modified=datetime(2026, 3, 14, tzinfo=UTC),
    )


# ============================================================
# Tests: Format Detection
# ============================================================


@allure.story("QC-047.02 Scan and Import from S3")
class TestDetectImportFormat:
    """Tests for auto-detecting import format from file extension."""

    @allure.title("Detects QDPX format from .qdpx extension")
    def test_detect_qdpx(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("project.qdpx") == "qdpx"

    @allure.title("Detects RQDA format from .rqda extension")
    def test_detect_rqda(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("analysis.rqda") == "rqda"

    @allure.title("Detects CSV format from .csv extension")
    def test_detect_csv(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("participants.csv") == "csv"

    @allure.title("Detects text format from .txt extension")
    def test_detect_txt(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("code_list.txt") == "txt"

    @allure.title("Detects SQLite format from .db extension")
    def test_detect_sqlite(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("backup.db") == "sqlite"

    @allure.title("Returns None for unknown extensions")
    def test_unknown_extension(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("file.xyz") is None

    @allure.title("Handles nested S3 keys with directories")
    def test_nested_key(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            detect_import_format,
        )

        assert detect_import_format("raw/exports/project.qdpx") == "qdpx"
        assert detect_import_format("processed/data.csv") == "csv"


# ============================================================
# Tests: Scan and Import
# ============================================================


@allure.story("QC-047.02 Scan and Import from S3")
class TestScanAndImport:
    """Tests for the scan_and_import composite command handler."""

    @allure.title("Scan and import pulls file and routes to importer")
    def test_scan_and_import_routes_correctly(self, tmp_path):
        from src.contexts.storage.core.commands import ScanAndImportCommand
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )

        store_repo = MockStoreRepository(store=_make_store())
        scanner = MockS3Scanner(
            file_contents={"raw/profiles.csv": "name,age\nAlice,30"}
        )
        event_bus = MockEventBus()
        importers = {"csv": MockImporter()}

        command = ScanAndImportCommand(
            key="raw/profiles.csv",
            local_staging_dir=str(tmp_path),
        )

        result = scan_and_import(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            importers=importers,
            event_bus=event_bus,
        )

        assert result.success is True
        assert len(importers["csv"].called_with) == 1

    @allure.title("Scan and import with QDPX file routes to qdpx importer")
    def test_scan_and_import_qdpx(self, tmp_path):
        from src.contexts.storage.core.commands import ScanAndImportCommand
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )

        store_repo = MockStoreRepository(store=_make_store())
        scanner = MockS3Scanner(
            file_contents={"exports/analysis.qdpx": "<qdpx>data</qdpx>"}
        )
        event_bus = MockEventBus()
        importers = {"qdpx": MockImporter()}

        command = ScanAndImportCommand(
            key="exports/analysis.qdpx",
            local_staging_dir=str(tmp_path),
        )

        result = scan_and_import(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            importers=importers,
            event_bus=event_bus,
        )

        assert result.success is True
        assert len(importers["qdpx"].called_with) == 1

    @allure.title("Scan and import without store fails")
    def test_scan_and_import_no_store_fails(self, tmp_path):
        from src.contexts.storage.core.commands import ScanAndImportCommand
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )

        store_repo = MockStoreRepository()  # no store
        scanner = MockS3Scanner()
        event_bus = MockEventBus()

        command = ScanAndImportCommand(
            key="raw/data.csv",
            local_staging_dir=str(tmp_path),
        )

        result = scan_and_import(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            importers={},
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_CONFIGURED" in (result.error_code or "")

    @allure.title("Scan and import with unsupported format fails")
    def test_scan_and_import_unsupported_format_fails(self, tmp_path):
        from src.contexts.storage.core.commands import ScanAndImportCommand
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )

        store_repo = MockStoreRepository(store=_make_store())
        scanner = MockS3Scanner(
            file_contents={"raw/data.xyz": "unknown format"}
        )
        event_bus = MockEventBus()

        command = ScanAndImportCommand(
            key="raw/data.xyz",
            local_staging_dir=str(tmp_path),
        )

        result = scan_and_import(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            importers={},
            event_bus=event_bus,
        )

        assert result.success is False
        assert "UNSUPPORTED_FORMAT" in (result.error_code or "")

    @allure.title("Scan and import with no importer registered for format fails")
    def test_scan_and_import_no_importer_fails(self, tmp_path):
        from src.contexts.storage.core.commands import ScanAndImportCommand
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            scan_and_import,
        )

        store_repo = MockStoreRepository(store=_make_store())
        scanner = MockS3Scanner(
            file_contents={"raw/data.csv": "name\nAlice"}
        )
        event_bus = MockEventBus()
        importers = {}  # no csv importer registered

        command = ScanAndImportCommand(
            key="raw/data.csv",
            local_staging_dir=str(tmp_path),
        )

        result = scan_and_import(
            command=command,
            store_repo=store_repo,
            s3_scanner=scanner,
            importers=importers,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NO_IMPORTER" in (result.error_code or "")


# ============================================================
# Tests: List Importable Files
# ============================================================


@allure.story("QC-047.02 Scan and Import from S3")
class TestListImportableFiles:
    """Tests for listing importable files from S3 scan results."""

    @allure.title("Filters scan results to only importable formats")
    def test_list_importable_files(self):
        from src.contexts.storage.core.commandHandlers.scan_and_import import (
            list_importable_files,
        )

        files = [
            _make_remote_file("raw/project.qdpx"),
            _make_remote_file("raw/data.csv"),
            _make_remote_file("raw/image.png"),  # not importable
            _make_remote_file("raw/analysis.rqda"),
            _make_remote_file("raw/readme.md"),  # not importable
            _make_remote_file("backups/snapshot.db"),
        ]

        importable = list_importable_files(files)

        keys = [f.key for f in importable]
        assert "raw/project.qdpx" in keys
        assert "raw/data.csv" in keys
        assert "raw/analysis.rqda" in keys
        assert "backups/snapshot.db" in keys
        assert "raw/image.png" not in keys
        assert "raw/readme.md" not in keys
