"""
Tests for Sources Context Invariants

Tests for pure predicate functions that validate business rules for source operations.
"""

from __future__ import annotations

from pathlib import Path

import allure
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

pytestmark = [
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


def _make_source(source_id: str, name: str) -> Source:
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


@allure.story("QC-027.01 Import Text Document")
class TestIsValidSourceName:
    """Tests for is_valid_source_name invariant."""

    @allure.title("Validates source name format and length")
    @pytest.mark.parametrize(
        "name, expected",
        [
            ("interview.txt", True),
            ("field interview 2024.txt", True),
            ("a" * 255, True),
            ("", False),
            ("   ", False),
            ("\t\n", False),
            ("a" * 256, False),
        ],
    )
    def test_valid_and_invalid_names(self, name: str, expected: bool) -> None:
        """Valid names pass, empty/whitespace/too-long names fail."""
        assert is_valid_source_name(name) is expected


@allure.story("QC-027.01 Import Text Document")
class TestIsSourceNameUnique:
    """Tests for is_source_name_unique invariant."""

    @allure.title("Detects unique names in empty and populated lists")
    @pytest.mark.parametrize(
        "candidate, existing_names, expected",
        [
            ("new_file.txt", [], True),
            ("file3.txt", ["file1.txt", "file2.txt"], True),
            ("interview.txt", ["Interview.txt"], False),
            ("INTERVIEW.TXT", ["Interview.txt"], False),
        ],
    )
    def test_uniqueness_checks(
        self, candidate: str, existing_names: list[str], expected: bool
    ) -> None:
        """Any name is unique in empty list; case-insensitive duplicate detection."""
        existing = [_make_source(str(i), n) for i, n in enumerate(existing_names)]
        assert is_source_name_unique(candidate, existing) is expected

    @allure.title("Exclude-ID allows rename but still rejects conflicts")
    def test_unique_with_exclude_id(self) -> None:
        """Excluding source's own ID allows same name; still rejects other conflicts."""
        existing = [
            _make_source("1", "interview.txt"),
            _make_source("2", "target_name.txt"),
        ]
        # Own ID excluded - same name allowed
        assert (
            is_source_name_unique(
                "interview.txt", existing, exclude_source_id=SourceId(value="1")
            )
            is True
        )
        # Own ID excluded - but conflicts with another source
        assert (
            is_source_name_unique(
                "target_name.txt", existing, exclude_source_id=SourceId(value="1")
            )
            is False
        )


@allure.story("QC-027.01 Import Text Document")
class TestDetectSourceType:
    """Tests for detect_source_type invariant."""

    @allure.title("Detects correct source type for all supported extensions")
    @pytest.mark.parametrize(
        "ext, expected_type",
        [(ext, SourceType.TEXT) for ext in sorted(TEXT_EXTENSIONS)]
        + [(ext, SourceType.AUDIO) for ext in sorted(AUDIO_EXTENSIONS)]
        + [(ext, SourceType.VIDEO) for ext in sorted(VIDEO_EXTENSIONS)]
        + [(ext, SourceType.IMAGE) for ext in sorted(IMAGE_EXTENSIONS)]
        + [(ext, SourceType.PDF) for ext in sorted(PDF_EXTENSIONS)],
    )
    def test_known_extensions(self, ext: str, expected_type: SourceType) -> None:
        """Known file extensions should return correct source type."""
        assert detect_source_type(Path(f"file{ext}")) == expected_type

    @allure.title("Unknown extension returns UNKNOWN and detection is case-insensitive")
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("file.xyz", SourceType.UNKNOWN),
            ("doc.TXT", SourceType.TEXT),
            ("doc.Txt", SourceType.TEXT),
            ("photo.JPG", SourceType.IMAGE),
        ],
    )
    def test_unknown_and_case_insensitive(self, filename: str, expected: SourceType) -> None:
        """Unknown extensions return UNKNOWN; detection is case-insensitive."""
        assert detect_source_type(Path(filename)) == expected


@allure.story("QC-027.01 Import Text Document")
class TestIsSupportedSourceType:
    """Tests for is_supported_source_type invariant."""

    @allure.title("Supported and unsupported file types: {filename}")
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("doc.txt", True),
            ("audio.mp3", True),
            ("video.mp4", True),
            ("photo.jpg", True),
            ("doc.pdf", True),
            ("file.xyz", False),
            ("file.exe", False),
            ("file.dll", False),
        ],
    )
    def test_supported_and_unsupported(self, filename: str, expected: bool) -> None:
        """Known file types are supported; unknown types are not."""
        assert is_supported_source_type(Path(filename)) is expected


@allure.story("QC-027.01 Import Text Document")
class TestCanImportSource:
    """Tests for can_import_source invariant."""

    @allure.title("Import allowed/rejected based on file existence and name uniqueness")
    @pytest.mark.parametrize(
        "file_exists, existing_names, expected",
        [
            (True, [], True),
            (False, [], False),
            (True, ["interview.txt"], False),
        ],
    )
    def test_can_import_scenarios(
        self, file_exists: bool, existing_names: list[str], expected: bool
    ) -> None:
        """Can import when file exists and name is unique; cannot otherwise."""
        existing = [_make_source(str(i), n) for i, n in enumerate(existing_names)]
        assert (
            can_import_source(
                Path("/data/interview.txt"), lambda _: file_exists, existing
            )
            is expected
        )
