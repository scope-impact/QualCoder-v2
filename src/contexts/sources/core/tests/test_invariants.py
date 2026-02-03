"""
Tests for Sources Context Invariants

Tests for pure predicate functions that validate business rules for source operations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.contexts.sources.core.entities import Source, SourceStatus, SourceType
from src.contexts.sources.core.invariants import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
    can_import_source,
    detect_source_type,
    is_source_name_unique,
    is_supported_source_type,
    is_valid_source_name,
)
from src.shared.common.types import SourceId


class TestIsValidSourceName:
    """Tests for is_valid_source_name invariant."""

    def test_valid_name(self) -> None:
        """Valid source name should pass."""
        assert is_valid_source_name("interview.txt") is True

    def test_valid_name_with_spaces(self) -> None:
        """Source name with spaces should be valid."""
        assert is_valid_source_name("field interview 2024.txt") is True

    def test_empty_name(self) -> None:
        """Empty name should fail."""
        assert is_valid_source_name("") is False

    def test_whitespace_only(self) -> None:
        """Whitespace-only name should fail."""
        assert is_valid_source_name("   ") is False
        assert is_valid_source_name("\t\n") is False

    def test_name_at_max_length(self) -> None:
        """Name at max length (255) should pass."""
        name = "a" * 255
        assert is_valid_source_name(name) is True

    def test_name_exceeds_max_length(self) -> None:
        """Name exceeding 255 chars should fail."""
        name = "a" * 256
        assert is_valid_source_name(name) is False


class TestIsSourceNameUnique:
    """Tests for is_source_name_unique invariant."""

    def _make_source(self, source_id: int, name: str) -> Source:
        """Create a source for testing."""
        return Source(
            id=SourceId(value=source_id),
            name=name,
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            code_count=0,
            memo=None,
            origin=None,
            folder_id=None,
        )

    def test_unique_name_in_empty_list(self) -> None:
        """Any name should be unique in empty list."""
        assert is_source_name_unique("new_file.txt", []) is True

    def test_unique_name_among_existing(self) -> None:
        """Different name should be unique."""
        existing = [
            self._make_source(1, "file1.txt"),
            self._make_source(2, "file2.txt"),
        ]
        assert is_source_name_unique("file3.txt", existing) is True

    def test_duplicate_name_exact_match(self) -> None:
        """Exact duplicate should fail."""
        existing = [self._make_source(1, "interview.txt")]
        assert is_source_name_unique("interview.txt", existing) is False

    def test_duplicate_name_case_insensitive(self) -> None:
        """Duplicate with different case should fail (case-insensitive)."""
        existing = [self._make_source(1, "Interview.txt")]
        assert is_source_name_unique("interview.txt", existing) is False
        assert is_source_name_unique("INTERVIEW.TXT", existing) is False

    def test_unique_with_exclude_id(self) -> None:
        """Excluding source's own ID should allow same name (for rename)."""
        source_id = SourceId(value=1)
        existing = [self._make_source(1, "interview.txt")]
        # When renaming to same name (excluding self), should pass
        assert (
            is_source_name_unique(
                "interview.txt", existing, exclude_source_id=source_id
            )
            is True
        )

    def test_duplicate_with_exclude_id(self) -> None:
        """Excluding source ID should still fail if another source has the name."""
        source_id_to_rename = SourceId(value=1)
        existing = [
            self._make_source(1, "file1.txt"),
            self._make_source(2, "target_name.txt"),  # Another source has this name
        ]
        # Renaming file1.txt to target_name.txt should fail
        assert (
            is_source_name_unique(
                "target_name.txt", existing, exclude_source_id=source_id_to_rename
            )
            is False
        )


class TestDetectSourceType:
    """Tests for detect_source_type invariant."""

    @pytest.mark.parametrize("ext", TEXT_EXTENSIONS)
    def test_text_extensions(self, ext: str) -> None:
        """Text file extensions should return TEXT type."""
        path = Path(f"document{ext}")
        assert detect_source_type(path) == SourceType.TEXT

    @pytest.mark.parametrize("ext", AUDIO_EXTENSIONS)
    def test_audio_extensions(self, ext: str) -> None:
        """Audio file extensions should return AUDIO type."""
        path = Path(f"recording{ext}")
        assert detect_source_type(path) == SourceType.AUDIO

    @pytest.mark.parametrize("ext", VIDEO_EXTENSIONS)
    def test_video_extensions(self, ext: str) -> None:
        """Video file extensions should return VIDEO type."""
        path = Path(f"video{ext}")
        assert detect_source_type(path) == SourceType.VIDEO

    @pytest.mark.parametrize("ext", IMAGE_EXTENSIONS)
    def test_image_extensions(self, ext: str) -> None:
        """Image file extensions should return IMAGE type."""
        path = Path(f"photo{ext}")
        assert detect_source_type(path) == SourceType.IMAGE

    @pytest.mark.parametrize("ext", PDF_EXTENSIONS)
    def test_pdf_extensions(self, ext: str) -> None:
        """PDF file extensions should return PDF type."""
        path = Path(f"document{ext}")
        assert detect_source_type(path) == SourceType.PDF

    def test_unknown_extension(self) -> None:
        """Unknown extension should return UNKNOWN type."""
        path = Path("file.xyz")
        assert detect_source_type(path) == SourceType.UNKNOWN

    def test_case_insensitive(self) -> None:
        """Extension detection should be case-insensitive."""
        assert detect_source_type(Path("doc.TXT")) == SourceType.TEXT
        assert detect_source_type(Path("doc.Txt")) == SourceType.TEXT
        assert detect_source_type(Path("photo.JPG")) == SourceType.IMAGE


class TestIsSupportedSourceType:
    """Tests for is_supported_source_type invariant."""

    def test_supported_text(self) -> None:
        """Text files should be supported."""
        assert is_supported_source_type(Path("doc.txt")) is True

    def test_supported_audio(self) -> None:
        """Audio files should be supported."""
        assert is_supported_source_type(Path("audio.mp3")) is True

    def test_supported_video(self) -> None:
        """Video files should be supported."""
        assert is_supported_source_type(Path("video.mp4")) is True

    def test_supported_image(self) -> None:
        """Image files should be supported."""
        assert is_supported_source_type(Path("photo.jpg")) is True

    def test_supported_pdf(self) -> None:
        """PDF files should be supported."""
        assert is_supported_source_type(Path("doc.pdf")) is True

    def test_unsupported_type(self) -> None:
        """Unknown file types should not be supported."""
        assert is_supported_source_type(Path("file.xyz")) is False
        assert is_supported_source_type(Path("file.exe")) is False
        assert is_supported_source_type(Path("file.dll")) is False


class TestCanImportSource:
    """Tests for can_import_source invariant."""

    def _make_source(self, source_id: int, name: str) -> Source:
        """Create a source for testing."""
        return Source(
            id=SourceId(value=source_id),
            name=name,
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            code_count=0,
            memo=None,
            origin=None,
            folder_id=None,
        )

    def test_can_import_existing_file(self) -> None:
        """Can import when file exists and name is unique."""
        path = Path("/data/interview.txt")
        existing: list[Source] = []
        assert can_import_source(path, lambda _: True, existing) is True

    def test_cannot_import_nonexistent_file(self) -> None:
        """Cannot import when file doesn't exist."""
        path = Path("/data/missing.txt")
        existing: list[Source] = []
        assert can_import_source(path, lambda _: False, existing) is False

    def test_cannot_import_duplicate_name(self) -> None:
        """Cannot import when name already exists."""
        path = Path("/data/interview.txt")
        existing = [self._make_source(1, "interview.txt")]
        assert can_import_source(path, lambda _: True, existing) is False
