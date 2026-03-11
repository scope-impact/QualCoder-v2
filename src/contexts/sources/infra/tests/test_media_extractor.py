"""
Tests for MediaExtractor - Infrastructure Layer.

TDD tests written BEFORE implementation.
Tests extraction of audio/video metadata including duration, format, codec, and bitrate.
"""

from pathlib import Path

import allure
import pytest
from returns.result import Failure, Success

from src.contexts.sources.infra.media_extractor import (
    MediaExtractionResult,
    MediaExtractor,
)

pytestmark = [
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


@pytest.fixture
def extractor() -> MediaExtractor:
    """Create a media extractor instance."""
    return MediaExtractor()


@pytest.fixture
def sample_mp3(tmp_path: Path) -> Path:
    """Create a minimal valid MP3 file using mutagen."""

    mp3_path = tmp_path / "sample.mp3"

    # Create a basic MP3 file structure that mutagen can handle
    # We'll use a very short silent MP3 frame
    mp3_data = bytearray()

    # ID3v2.3 header (10 bytes)
    mp3_data.extend(b"ID3\x03\x00\x00")  # ID3v2.3
    mp3_data.extend((20).to_bytes(4, "big"))  # Size (synchsafe)

    # Add a simple text frame (TIT2 - Title)
    frame = b"TIT2\x00\x00\x00\x0b\x00\x00\x00Test"
    mp3_data.extend(frame)

    # Add multiple valid MPEG frames to ensure proper duration calculation
    # Each frame is 417 bytes for MPEG1 Layer3 at 128kbps 44.1kHz
    for _ in range(10):  # 10 frames for ~0.26 seconds
        mp3_data.extend(
            b"\xff\xfb\x90\x00"  # MPEG1 Layer3, 128kbps, 44.1kHz, no padding
            + b"\x00" * 413  # Data to make 417 bytes total per frame
        )

    mp3_path.write_bytes(bytes(mp3_data))
    return mp3_path


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    """Create a minimal valid WAV file."""
    # Minimal WAV header for a 1-second 44.1kHz 16-bit stereo file
    wav_data = (
        b"RIFF"
        + (44100 * 2 * 2 + 36).to_bytes(4, "little")  # File size - 8
        + b"WAVE"
        + b"fmt "
        + (16).to_bytes(4, "little")  # fmt chunk size
        + (1).to_bytes(2, "little")  # Audio format (PCM)
        + (2).to_bytes(2, "little")  # Channels (stereo)
        + (44100).to_bytes(4, "little")  # Sample rate
        + (44100 * 2 * 2).to_bytes(4, "little")  # Byte rate
        + (4).to_bytes(2, "little")  # Block align
        + (16).to_bytes(2, "little")  # Bits per sample
        + b"data"
        + (44100 * 2 * 2).to_bytes(4, "little")  # Data chunk size
        + b"\x00" * (44100 * 2 * 2)  # Audio data (silence)
    )
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(wav_data)
    return wav_path


@allure.story("QC-027.04 Import Audio/Video Files")
class TestMediaExtraction:
    """Tests for extracting media metadata."""

    @allure.title("Extracts metadata from MP3 and WAV files")
    def test_extracts_audio_metadata(self, extractor: MediaExtractor, sample_mp3: Path, sample_wav: Path):
        """Extracts duration, format, and metadata from audio files."""
        # MP3
        result = extractor.extract(sample_mp3)
        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.format == "MP3"
        assert data.file_size == sample_mp3.stat().st_size
        assert data.duration_seconds >= 0
        assert isinstance(data.metadata, dict)
        assert data.width is None
        assert data.height is None

        # WAV
        result = extractor.extract(sample_wav)
        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.format == "WAV"
        assert data.file_size > 0
        assert data.duration_seconds >= 0
        assert data.sample_rate == 44100

    @allure.title("Fails for nonexistent, non-media, and corrupted files")
    @pytest.mark.parametrize(
        "setup, error_check",
        [
            pytest.param("nonexistent", "not found", id="nonexistent"),
            pytest.param("non_media", "cannot identify|error", id="non-media"),
            pytest.param("corrupted", None, id="corrupted"),
        ],
    )
    def test_fails_for_invalid_files(self, extractor: MediaExtractor, tmp_path: Path, setup, error_check):
        import re

        if setup == "nonexistent":
            path = tmp_path / "missing.mp3"
        elif setup == "non_media":
            path = tmp_path / "not_media.txt"
            path.write_text("This is not a media file")
        else:
            path = tmp_path / "corrupted.mp3"
            path.write_bytes(b"MP3\x00\x00\x00corrupted")

        result = extractor.extract(path)
        assert isinstance(result, Failure)
        if error_check:
            assert re.search(error_check, result.failure().lower())

    @allure.title("Returns graceful error when mutagen is missing")
    def test_handles_missing_mutagen_library(
        self,
        extractor: MediaExtractor,
        sample_mp3: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        def mock_import(name, *args, **kwargs):
            if name == "mutagen":
                raise ImportError("No module named 'mutagen'")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        new_extractor = MediaExtractor()
        result = new_extractor.extract(sample_mp3)

        assert isinstance(result, Failure)
        assert "mutagen" in result.failure().lower()


@allure.story("QC-027.04 Import Audio/Video Files")
class TestMediaExtractionResult:
    """Tests for MediaExtractionResult data class."""

    @allure.title("Has all required fields with correct values and optional defaults")
    def test_fields_and_optional_defaults(self):
        # Full result with all fields
        result = MediaExtractionResult(
            duration_seconds=180.5,
            format="MP4",
            file_size=1048576,
            codec="H.264",
            bitrate=128000,
            sample_rate=48000,
            width=1920,
            height=1080,
            metadata={"title": "Sample Video"},
        )

        assert result.duration_seconds == 180.5
        assert result.format == "MP4"
        assert result.file_size == 1048576
        assert result.codec == "H.264"
        assert result.bitrate == 128000
        assert result.sample_rate == 48000
        assert result.width == 1920
        assert result.height == 1080
        assert result.metadata == {"title": "Sample Video"}

        # Optional fields default to None, metadata can be empty
        result_minimal = MediaExtractionResult(
            duration_seconds=60.0,
            format="MP3",
            file_size=1024,
            codec=None,
            bitrate=None,
            sample_rate=None,
            width=None,
            height=None,
            metadata={},
        )

        assert result_minimal.codec is None
        assert result_minimal.bitrate is None
        assert result_minimal.sample_rate is None
        assert result_minimal.width is None
        assert result_minimal.height is None
        assert result_minimal.metadata == {}


@allure.story("QC-027.04 Import Audio/Video Files")
class TestSupportedFormats:
    """Tests for format support checking."""

    @allure.title("Supports audio/video formats and rejects non-media (case-insensitive)")
    @pytest.mark.parametrize(
        "filename, expected",
        [
            pytest.param("audio.mp3", True, id="mp3"),
            pytest.param("audio.wav", True, id="wav"),
            pytest.param("audio.m4a", True, id="m4a"),
            pytest.param("audio.ogg", True, id="ogg"),
            pytest.param("audio.flac", True, id="flac"),
            pytest.param("audio.aac", True, id="aac"),
            pytest.param("audio.wma", True, id="wma"),
            pytest.param("video.mp4", True, id="mp4"),
            pytest.param("video.mov", True, id="mov"),
            pytest.param("video.avi", True, id="avi"),
            pytest.param("video.mkv", True, id="mkv"),
            pytest.param("video.wmv", True, id="wmv"),
            pytest.param("video.webm", True, id="webm"),
            pytest.param("video.m4v", True, id="m4v"),
            pytest.param("doc.pdf", False, id="pdf"),
            pytest.param("doc.txt", False, id="txt"),
            pytest.param("image.jpg", False, id="jpg"),
            pytest.param("image.png", False, id="png"),
            pytest.param("audio.MP3", True, id="MP3-upper"),
            pytest.param("video.Mp4", True, id="Mp4-mixed"),
            pytest.param("audio.WaV", True, id="WaV-mixed"),
        ],
    )
    def test_format_support(self, extractor: MediaExtractor, filename: str, expected: bool):
        assert extractor.supports(Path(filename)) == expected
