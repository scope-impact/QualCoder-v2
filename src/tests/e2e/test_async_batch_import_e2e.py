"""
E2E tests for async batch import refactoring.

Tests that FileManagerViewModel.import_sources_batch() uses asyncio
(run_in_executor) instead of QThread, while preserving identical
external behaviour: progress signals, cancellation, and persistence.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_text_files(directory: Path, count: int) -> list[str]:
    """Create N small text files and return absolute paths as strings."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(count):
        p = directory / f"doc_{i:03d}.txt"
        p.write_text(f"Content of document {i}.\nLine two.\n", encoding="utf-8")
        paths.append(str(p))
    return paths


def _run_batch_import(viewmodel, paths, **kwargs):
    """Schedule batch import and run the async task to completion."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        viewmodel.import_sources_batch(paths, **kwargs)
        if viewmodel._import_task is not None:
            loop.run_until_complete(viewmodel._import_task)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def viewmodel(source_repo, folder_repo, case_repo, project_state, event_bus):
    """Create FileManagerViewModel with real repos."""
    from src.contexts.sources.presentation.viewmodels.file_manager_viewmodel import (
        FileManagerViewModel,
    )

    return FileManagerViewModel(
        source_repo=source_repo,
        folder_repo=folder_repo,
        case_repo=case_repo,
        state=project_state,
        event_bus=event_bus,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@allure.story("QC-027.16 Async Batch Import")
@allure.severity(allure.severity_level.CRITICAL)
class TestAsyncBatchImport:
    """Verify the async batch import replaces QThread ImportWorker."""

    @allure.title("AC #1+2: batch import persists files with correct progress signals")
    def test_batch_import_persists_with_progress(self, viewmodel, source_repo, tmp_path):
        """Import 5 text files, verify persistence, finished signal, and progress signals."""
        paths = _create_text_files(tmp_path / "batch", 5)

        finished_args = []
        viewmodel.batch_import_finished.connect(
            lambda imp, fail, ps: finished_args.append((imp, fail, ps))
        )

        progress_args = []
        viewmodel.batch_import_progress.connect(
            lambda cur, tot, name: progress_args.append((cur, tot, name))
        )

        _run_batch_import(viewmodel, paths)

        # All 5 files persisted
        sources = source_repo.get_all()
        assert len(sources) == 5

        # Finished signal emitted with correct counts
        assert len(finished_args) == 1
        imported, failed, imported_paths = finished_args[0]
        assert imported == 5
        assert failed == 0
        assert len(imported_paths) == 5

        # Progress emitted for each file with correct counts
        assert len(progress_args) == 5
        for _cur, tot, _name in progress_args:
            assert tot == 5
        currents = [p[0] for p in progress_args]
        assert currents == [1, 2, 3, 4, 5]

    @allure.title("AC #3+4: duplicate filenames and unsupported types counted as failures")
    def test_duplicate_and_unsupported_fail(self, viewmodel, source_repo, tmp_path):
        """Duplicate filenames and unsupported file types are counted as failures."""
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        # Test duplicates
        existing = Source(
            id=SourceId.new(),
            name="doc_000.txt",
            source_type=SourceType.TEXT,
            fulltext="existing",
        )
        source_repo.save(existing)

        paths = _create_text_files(tmp_path / "dup", 3)

        finished_args = []
        viewmodel.batch_import_finished.connect(
            lambda imp, fail, ps: finished_args.append((imp, fail, ps))
        )

        _run_batch_import(viewmodel, paths)

        imported, failed, _ = finished_args[0]
        assert imported == 2  # doc_001, doc_002
        assert failed == 1  # doc_000 duplicate

        # Test unsupported types (need new viewmodel-like state, use same one)
        d = tmp_path / "unsupported"
        d.mkdir()
        bad = d / "data.xyz"
        bad.write_text("nope")
        good = d / "note.txt"
        good.write_text("hello")

        finished_args.clear()
        _run_batch_import(viewmodel, [str(bad), str(good)])

        imported, failed, _ = finished_args[0]
        assert imported == 1
        assert failed == 1

    @allure.title("AC #5+6: cancellation stops processing and events published per file")
    def test_cancellation_and_events(self, viewmodel, source_repo, event_bus, tmp_path):
        """Cancellation stops remaining files; events published for each imported file."""
        # Test events first (clean state)
        paths = _create_text_files(tmp_path / "events", 3)
        events = []
        event_bus.subscribe("projects.source_added", lambda e: events.append(e))
        _run_batch_import(viewmodel, paths)
        assert len(events) == 3

        # Test cancellation
        paths = _create_text_files(tmp_path / "cancel", 10)

        progress_count = {"n": 0}

        def _on_progress(cur, tot, name):
            progress_count["n"] += 1
            if progress_count["n"] >= 1:
                viewmodel.cancel_import()

        viewmodel.batch_import_progress.connect(_on_progress)
        _run_batch_import(viewmodel, paths)

        # Should have imported fewer than 10 (plus 3 from events test)
        sources = source_repo.get_all()
        assert len(sources) < 13

    @allure.title("AC #7+8: suppress_reloads active during import and ImportWorker removed")
    def test_suppress_reloads_and_worker_removed(self, viewmodel, tmp_path):
        """Single reload at end of batch import; old ImportWorker QThread deleted."""
        paths = _create_text_files(tmp_path / "suppress", 3)

        sources_changed_calls = []
        viewmodel.sources_changed.connect(lambda: sources_changed_calls.append(1))

        _run_batch_import(viewmodel, paths)

        # Only 1 sources_changed emission (the batch-end reload), not 3
        assert len(sources_changed_calls) == 1

        # Old QThread-based ImportWorker should be deleted
        with pytest.raises((ImportError, ModuleNotFoundError)):
            from src.contexts.sources.infra.import_worker import (
                ImportWorker,  # noqa: F401
            )

    @allure.title("AC #9+10: is_importing property and concurrent call rejection")
    def test_is_importing_and_rejects_concurrent(self, viewmodel, source_repo, tmp_path):
        """is_importing reflects task state; concurrent imports are rejected."""
        # Test is_importing property
        paths = _create_text_files(tmp_path / "importing", 2)

        was_importing = []

        def _check_on_progress(cur, tot, name):
            was_importing.append(viewmodel.is_importing)

        viewmodel.batch_import_progress.connect(_check_on_progress)
        _run_batch_import(viewmodel, paths)

        assert any(was_importing)
        assert not viewmodel.is_importing

        # Test concurrent rejection (need fresh viewmodel state)
        paths1 = _create_text_files(tmp_path / "batch1", 3)
        paths2 = _create_text_files(tmp_path / "batch2", 3)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            viewmodel.import_sources_batch(paths1)
            assert viewmodel.is_importing
            viewmodel.import_sources_batch(paths2)  # rejected
            if viewmodel._import_task is not None:
                loop.run_until_complete(viewmodel._import_task)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        # 2 from first test + 3 from batch1 = 5 (batch2 rejected)
        sources = source_repo.get_all()
        assert len(sources) == 5
