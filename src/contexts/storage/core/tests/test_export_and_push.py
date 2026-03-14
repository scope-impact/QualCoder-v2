"""
Storage Context: Export-and-Push Command Handler Tests (TDD RED)

Tests for exporting project data (QDPX/codebook/SQLite) and pushing via DVC.
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest

from src.contexts.storage.infra.dvc_gateway import DvcResult

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


class MockDvcGateway:
    """Mock DVC gateway for export-and-push tests."""

    def __init__(self, *, fail_on: str | None = None):
        self.calls: list[str] = []
        self._fail_on = fail_on

    def _result(self, op: str):
        self.calls.append(op)
        if self._fail_on == op:
            return DvcResult(success=False, message=f"{op} failed")
        return DvcResult(success=True, message=f"{op} ok")

    def add(self, path):
        return self._result("add")

    def push(self, remote=None):
        return self._result("push")

    def pull(self, remote=None):
        return self._result("pull")

    @staticmethod
    def s3_url(bucket, prefix=""):
        return f"s3://{bucket}/{prefix}" if prefix else f"s3://{bucket}"


class MockExporter:
    """Simulates an exchange export handler that produces a file."""

    def __init__(self, output_content: str = "exported data"):
        self._content = output_content
        self.called_with: dict | None = None

    def __call__(self, command, **kwargs):
        from src.shared.common.operation_result import OperationResult

        # Write the file to simulate export
        Path(command.output_path).write_text(self._content)
        self.called_with = {"command": command, **kwargs}
        return OperationResult.ok(data={"output_path": command.output_path})


def _make_store():
    from src.contexts.storage.core.entities import DataStore, StoreId

    return DataStore(
        id=StoreId(value="store_001"),
        bucket_name="research-data",
        region="us-east-1",
        prefix="",
    )


# ============================================================
# Tests
# ============================================================


@allure.story("QC-047.04 Export and Push to S3")
class TestExportAndPush:
    """Tests for export_and_push composite command handler."""

    @allure.title("Export QDPX and push via DVC succeeds")
    def test_export_qdpx_and_push(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        store_repo = MockStoreRepository(store=_make_store())
        dvc = MockDvcGateway()
        event_bus = MockEventBus()
        exporter = MockExporter(output_content="<qdpx>project</qdpx>")

        command = ExportAndPushCommand(
            export_format="qdpx",
            destination_key="exports/project.qdpx",
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=exporter,
            event_bus=event_bus,
        )

        assert result.success is True
        assert "add" in dvc.calls
        assert "push" in dvc.calls
        assert len(event_bus.published) >= 1

    @allure.title("Export codebook and push via DVC succeeds")
    def test_export_codebook_and_push(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        store_repo = MockStoreRepository(store=_make_store())
        dvc = MockDvcGateway()
        event_bus = MockEventBus()
        exporter = MockExporter(output_content="Theme: Engagement")

        command = ExportAndPushCommand(
            export_format="codebook",
            destination_key="exports/codebook.txt",
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=exporter,
            event_bus=event_bus,
        )

        assert result.success is True
        assert "add" in dvc.calls

    @allure.title("Export SQLite snapshot and push via DVC succeeds")
    def test_export_sqlite_and_push(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        store_repo = MockStoreRepository(store=_make_store())
        dvc = MockDvcGateway()
        event_bus = MockEventBus()
        exporter = MockExporter(output_content="SQLITE_BINARY_DATA")

        command = ExportAndPushCommand(
            export_format="sqlite",
            destination_key="backups/project_2026-03-14.db",
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=exporter,
            event_bus=event_bus,
        )

        assert result.success is True
        assert "push" in dvc.calls

    @allure.title("Export and push without configured store fails")
    def test_export_and_push_no_store_fails(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        store_repo = MockStoreRepository()  # no store
        dvc = MockDvcGateway()
        event_bus = MockEventBus()
        exporter = MockExporter()

        command = ExportAndPushCommand(
            export_format="qdpx",
            destination_key="exports/project.qdpx",
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=exporter,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_CONFIGURED" in (result.error_code or "")
        assert len(dvc.calls) == 0

    @allure.title("Export and push with invalid destination key fails")
    def test_export_and_push_invalid_key_fails(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand

        store_repo = MockStoreRepository(store=_make_store())
        dvc = MockDvcGateway()
        event_bus = MockEventBus()
        exporter = MockExporter()

        command = ExportAndPushCommand(
            export_format="qdpx",
            destination_key="",  # invalid
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=exporter,
            event_bus=event_bus,
        )

        assert result.success is False
        assert len(dvc.calls) == 0

    @allure.title("Export failure prevents push")
    def test_export_failure_prevents_push(self, tmp_path):
        from src.contexts.storage.core.commandHandlers.export_and_push import (
            export_and_push,
        )
        from src.contexts.storage.core.commands import ExportAndPushCommand
        from src.shared.common.operation_result import OperationResult

        store_repo = MockStoreRepository(store=_make_store())
        dvc = MockDvcGateway()
        event_bus = MockEventBus()

        def failing_exporter(command, **kwargs):
            return OperationResult.fail(
                error="Export failed", error_code="EXPORT_FAILED"
            )

        command = ExportAndPushCommand(
            export_format="qdpx",
            destination_key="exports/project.qdpx",
            local_staging_dir=str(tmp_path),
        )

        result = export_and_push(
            command=command,
            store_repo=store_repo,
            dvc_gateway=dvc,
            exporter=failing_exporter,
            event_bus=event_bus,
        )

        assert result.success is False
        assert len(dvc.calls) == 0
