"""
Tests for Sources Context Derivers

Tests for pure functions that derive domain events from commands and state.
"""

from __future__ import annotations

from pathlib import Path

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


class TestDeriveAddSource:
    """Tests for derive_add_source deriver."""

    def test_add_source_success(self) -> None:
        """Successfully add a source when file exists and name is unique."""
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )
        result = derive_add_source(
            source_path=Path("/data/interview.txt"),
            origin="Field Interview",
            memo="Initial interview",
            owner="researcher@example.com",
            state=state,
        )
        assert isinstance(result, SourceAdded)
        assert result.name == "interview.txt"
        assert result.source_type == SourceType.TEXT
        assert result.file_path == Path("/data/interview.txt")
        assert result.origin == "Field Interview"
        assert result.memo == "Initial interview"

    def test_add_source_file_not_found(self) -> None:
        """Fail to add source when file doesn't exist."""
        state = ProjectState(
            path_exists=lambda _: False,
            existing_sources=(),
        )
        result = derive_add_source(
            source_path=Path("/data/missing.txt"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(result, SourceNotAdded)
        assert result.reason == "FILE_NOT_FOUND"
        assert result.path == Path("/data/missing.txt")

    def test_add_source_duplicate_name(self) -> None:
        """Fail to add source when name already exists."""
        existing_source = Source(
            id=SourceId(value=1),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            code_count=0,
            memo=None,
            origin=None,
            folder_id=None,
        )
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(existing_source,),
        )
        result = derive_add_source(
            source_path=Path("/data/interview.txt"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(result, SourceNotAdded)
        assert result.reason == "DUPLICATE_NAME"
        assert result.name == "interview.txt"

    def test_add_source_detects_correct_type(self) -> None:
        """Source type should be detected from file extension."""
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )

        # Test different file types
        audio_result = derive_add_source(
            source_path=Path("/data/recording.mp3"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(audio_result, SourceAdded)
        assert audio_result.source_type == SourceType.AUDIO

        video_result = derive_add_source(
            source_path=Path("/data/video.mp4"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(video_result, SourceAdded)
        assert video_result.source_type == SourceType.VIDEO

        image_result = derive_add_source(
            source_path=Path("/data/photo.jpg"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )
        assert isinstance(image_result, SourceAdded)
        assert image_result.source_type == SourceType.IMAGE


class TestDeriveRemoveSource:
    """Tests for derive_remove_source deriver."""

    def _make_source(self, source_id: int, name: str, code_count: int = 0) -> Source:
        """Create a source for testing."""
        return Source(
            id=SourceId(value=source_id),
            name=name,
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            code_count=code_count,
            memo=None,
            origin=None,
            folder_id=None,
        )

    def test_remove_source_success(self) -> None:
        """Successfully remove an existing source."""
        source = self._make_source(1, "interview.txt", code_count=5)
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(source,),
        )
        result = derive_remove_source(
            source_id=SourceId(value=1),
            state=state,
        )
        assert isinstance(result, SourceRemoved)
        assert result.source_id == SourceId(value=1)
        assert result.name == "interview.txt"
        assert result.segments_removed == 5

    def test_remove_source_not_found(self) -> None:
        """Fail to remove a non-existent source."""
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )
        result = derive_remove_source(
            source_id=SourceId(value=999),
            state=state,
        )
        assert isinstance(result, SourceNotRemoved)
        assert result.reason == "NOT_FOUND"
        assert result.source_id == SourceId(value=999)


class TestDeriveOpenSource:
    """Tests for derive_open_source deriver."""

    def _make_source(
        self, source_id: int, name: str, source_type: SourceType = SourceType.TEXT
    ) -> Source:
        """Create a source for testing."""
        return Source(
            id=SourceId(value=source_id),
            name=name,
            source_type=source_type,
            status=SourceStatus.IMPORTED,
            code_count=0,
            memo=None,
            origin=None,
            folder_id=None,
        )

    def test_open_source_success(self) -> None:
        """Successfully open an existing source."""
        source = self._make_source(1, "interview.txt", SourceType.TEXT)
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(source,),
        )
        result = derive_open_source(
            source_id=SourceId(value=1),
            state=state,
        )
        assert isinstance(result, SourceOpened)
        assert result.source_id == SourceId(value=1)
        assert result.name == "interview.txt"
        assert result.source_type == SourceType.TEXT

    def test_open_source_not_found(self) -> None:
        """Fail to open a non-existent source."""
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )
        result = derive_open_source(
            source_id=SourceId(value=999),
            state=state,
        )
        assert isinstance(result, SourceNotOpened)
        assert result.reason == "NOT_FOUND"
        assert result.source_id == SourceId(value=999)


class TestDeriveUpdateSource:
    """Tests for derive_update_source deriver."""

    def _make_source(self, source_id: int, name: str) -> Source:
        """Create a source for testing."""
        return Source(
            id=SourceId(value=source_id),
            name=name,
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            code_count=0,
            memo="Old memo",
            origin="Old origin",
            folder_id=None,
        )

    def test_update_source_memo(self) -> None:
        """Successfully update source memo."""
        source = self._make_source(1, "interview.txt")
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(source,),
        )
        result = derive_update_source(
            source_id=SourceId(value=1),
            memo="New memo",
            origin=None,
            status=None,
            state=state,
        )
        assert isinstance(result, SourceUpdated)
        assert result.source_id == SourceId(value=1)
        assert result.memo == "New memo"
        assert result.origin is None  # Not updated

    def test_update_source_status(self) -> None:
        """Successfully update source status."""
        source = self._make_source(1, "interview.txt")
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(source,),
        )
        result = derive_update_source(
            source_id=SourceId(value=1),
            memo=None,
            origin=None,
            status="coded",
            state=state,
        )
        assert isinstance(result, SourceUpdated)
        assert result.source_id == SourceId(value=1)
        assert result.status == "coded"

    def test_update_source_not_found(self) -> None:
        """Fail to update a non-existent source."""
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(),
        )
        result = derive_update_source(
            source_id=SourceId(value=999),
            memo="New memo",
            origin=None,
            status=None,
            state=state,
        )
        assert isinstance(result, SourceNotUpdated)
        assert result.reason == "NOT_FOUND"
        assert result.source_id == SourceId(value=999)

    def test_update_source_invalid_status(self) -> None:
        """Fail to update source with invalid status."""
        source = self._make_source(1, "interview.txt")
        state = ProjectState(
            path_exists=lambda _: True,
            existing_sources=(source,),
        )
        result = derive_update_source(
            source_id=SourceId(value=1),
            memo=None,
            origin=None,
            status="invalid_status",
            state=state,
        )
        assert isinstance(result, SourceNotUpdated)
        assert result.reason == "INVALID_STATUS"
        assert result.status == "invalid_status"
