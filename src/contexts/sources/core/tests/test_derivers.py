"""
Tests for Sources Context Derivers

Tests for pure functions that derive domain events from commands and state.
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest

from src.contexts.sources.core.derivers import (
    ProjectState,
    derive_add_source,
    derive_open_source,
    derive_remove_source,
    derive_update_source,
)
from src.contexts.sources.core.entities import Source, SourceStatus, SourceType
from src.contexts.sources.core.events import (
    SourceAdded,
    SourceOpened,
    SourceRemoved,
    SourceUpdated,
)
from src.contexts.sources.core.failure_events import (
    SourceNotAdded,
    SourceNotOpened,
    SourceNotRemoved,
    SourceNotUpdated,
)
from src.shared.common.types import SourceId

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


@allure.story("QC-027.01 Add Source")
class TestDeriveAddSource:
    """Tests for derive_add_source deriver."""

    @allure.title("Successfully adds source and detects correct type from extension")
    @pytest.mark.parametrize(
        "filename, expected_type",
        [
            pytest.param("interview.txt", SourceType.TEXT, id="text"),
            pytest.param("recording.mp3", SourceType.AUDIO, id="audio"),
            pytest.param("video.mp4", SourceType.VIDEO, id="video"),
            pytest.param("photo.jpg", SourceType.IMAGE, id="image"),
        ],
    )
    def test_add_source_success_with_type_detection(self, filename, expected_type):
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )
        result = derive_add_source(
            source_path=Path(f"/data/{filename}"),
            origin="Field Interview" if filename == "interview.txt" else None,
            memo="Initial interview" if filename == "interview.txt" else None,
            owner="researcher@example.com" if filename == "interview.txt" else None,
            state=state,
        )
        assert isinstance(result, SourceAdded)
        assert result.name == filename
        assert result.source_type == expected_type
        assert result.file_path == Path(f"/data/{filename}")

    @allure.title("Fails when file not found or duplicate name")
    @pytest.mark.parametrize(
        "path_exists, has_existing, expected_reason",
        [
            pytest.param(False, False, "FILE_NOT_FOUND", id="file-not-found"),
            pytest.param(True, True, "DUPLICATE_NAME", id="duplicate-name"),
        ],
    )
    def test_add_source_failures(self, path_exists, has_existing, expected_reason):
        existing_sources = ()
        if has_existing:
            existing_sources = (
                Source(
                    id=SourceId(value="1"),
                    name="interview.txt",
                    source_type=SourceType.TEXT,
                    status=SourceStatus.IMPORTED,
                    code_count=0,
                    memo=None,
                    origin=None,
                    folder_id=None,
                ),
            )
        state = ProjectState(
            path_exists=lambda _: path_exists,
            existing_sources=existing_sources,
        )
        result = derive_add_source(
            source_path=Path("/data/interview.txt"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(result, SourceNotAdded)
        assert result.reason == expected_reason


def _make_source(
    source_id: str,
    name: str,
    source_type: SourceType = SourceType.TEXT,
    code_count: int = 0,
    memo: str | None = None,
    origin: str | None = None,
) -> Source:
    """Create a source for testing."""
    return Source(
        id=SourceId(value=source_id),
        name=name,
        source_type=source_type,
        status=SourceStatus.IMPORTED,
        code_count=code_count,
        memo=memo,
        origin=origin,
        folder_id=None,
    )


@allure.story("QC-027.02 Remove Source")
class TestDeriveRemoveSource:
    """Tests for derive_remove_source deriver."""

    @allure.title("Removes existing source or fails when not found")
    @pytest.mark.parametrize(
        "source_id, has_source, success",
        [
            pytest.param("1", True, True, id="existing"),
            pytest.param("999", False, False, id="not-found"),
        ],
    )
    def test_remove_source(self, source_id, has_source, success):
        existing = (_make_source("1", "interview.txt", code_count=5),) if has_source else ()
        state = ProjectState(path_exists=lambda _: True, existing_sources=existing)

        result = derive_remove_source(source_id=SourceId(value=source_id), state=state)

        if success:
            assert isinstance(result, SourceRemoved)
            assert result.source_id == SourceId(value=source_id)
            assert result.name == "interview.txt"
            assert result.segments_removed == 5
        else:
            assert isinstance(result, SourceNotRemoved)
            assert result.reason == "NOT_FOUND"


@allure.story("QC-027.03 Open Source")
class TestDeriveOpenSource:
    """Tests for derive_open_source deriver."""

    @allure.title("Opens existing source or fails when not found")
    @pytest.mark.parametrize(
        "source_id, has_source, success",
        [
            pytest.param("1", True, True, id="existing"),
            pytest.param("999", False, False, id="not-found"),
        ],
    )
    def test_open_source(self, source_id, has_source, success):
        existing = (_make_source("1", "interview.txt", SourceType.TEXT),) if has_source else ()
        state = ProjectState(path_exists=lambda _: True, existing_sources=existing)

        result = derive_open_source(source_id=SourceId(value=source_id), state=state)

        if success:
            assert isinstance(result, SourceOpened)
            assert result.source_id == SourceId(value=source_id)
            assert result.name == "interview.txt"
            assert result.source_type == SourceType.TEXT
        else:
            assert isinstance(result, SourceNotOpened)
            assert result.reason == "NOT_FOUND"


@allure.story("QC-027.04 Update Source")
class TestDeriveUpdateSource:
    """Tests for derive_update_source deriver."""

    @allure.title("Updates source memo/status or fails with invalid input")
    @pytest.mark.parametrize(
        "source_id, has_source, memo, status, expect_success, expected_reason",
        [
            pytest.param("1", True, "New memo", None, True, None, id="update-memo"),
            pytest.param("1", True, None, "coded", True, None, id="update-status"),
            pytest.param("999", False, "New memo", None, False, "NOT_FOUND", id="not-found"),
            pytest.param("1", True, None, "invalid_status", False, "INVALID_STATUS", id="invalid-status"),
        ],
    )
    def test_update_source(self, source_id, has_source, memo, status, expect_success, expected_reason):
        existing = (
            _make_source("1", "interview.txt", memo="Old memo", origin="Old origin"),
        ) if has_source else ()
        state = ProjectState(path_exists=lambda _: True, existing_sources=existing)

        result = derive_update_source(
            source_id=SourceId(value=source_id),
            memo=memo,
            origin=None,
            status=status,
            state=state,
        )

        if expect_success:
            assert isinstance(result, SourceUpdated)
            assert result.source_id == SourceId(value=source_id)
            if memo:
                assert result.memo == memo
            if status:
                assert result.status == status
        else:
            assert isinstance(result, SourceNotUpdated)
            assert result.reason == expected_reason
