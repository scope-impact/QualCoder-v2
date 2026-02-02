"""
Tests for MediaExtractor - Infrastructure Layer.

TDD tests written BEFORE implementation.
Tests extraction of audio/video metadata including duration, format, codec, and bitrate.
"""

from pathlib import Path

import pytest
from returns.result import Failure, Success

from src.infrastructure.sources.media_extractor import (
    MediaExtractionResult,
    MediaExtractor,
)


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


class TestMediaExtraction:
    """Tests for extracting media metadata."""

    def test_extracts_mp3_metadata(self, extractor: MediaExtractor, sample_mp3: Path):
        """Extracts duration, format, and bitrate from MP3 file."""
        result = extractor.extract(sample_mp3)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.format == "MP3"
        assert data.file_size > 0
        assert data.duration_seconds >= 0

    def test_extracts_wav_metadata(self, extractor: MediaExtractor, sample_wav: Path):
        """Extracts duration, format, and sample rate from WAV file."""
        result = extractor.extract(sample_wav)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.format == "WAV"
        assert data.file_size > 0
        assert data.duration_seconds >= 0
        assert data.sample_rate == 44100

    def test_returns_accurate_file_size(
        self, extractor: MediaExtractor, sample_mp3: Path
    ):
        """Returns correct file size in bytes."""
        result = extractor.extract(sample_mp3)

        assert isinstance(result, Success)
        data = result.unwrap()
        actual_size = sample_mp3.stat().st_size
        assert data.file_size == actual_size

    def test_extracts_metadata_dict(self, extractor: MediaExtractor, sample_mp3: Path):
        """Returns metadata dictionary with media info."""
        result = extractor.extract(sample_mp3)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert isinstance(data.metadata, dict)

    def test_fails_for_nonexistent_file(
        self, extractor: MediaExtractor, tmp_path: Path
    ):
        """Returns failure for non-existent file."""
        missing = tmp_path / "missing.mp3"

        result = extractor.extract(missing)

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_fails_for_non_media_file(self, extractor: MediaExtractor, tmp_path: Path):
        """Returns failure for non-media file."""
        text_file = tmp_path / "not_media.txt"
        text_file.write_text("This is not a media file")

        result = extractor.extract(text_file)

        assert isinstance(result, Failure)
        error_msg = result.failure().lower()
        assert "cannot identify" in error_msg or "error" in error_msg

    def test_fails_for_corrupted_media(self, extractor: MediaExtractor, tmp_path: Path):
        """Returns failure for corrupted media file."""
        corrupted = tmp_path / "corrupted.mp3"
        # Write invalid MP3 data
        corrupted.write_bytes(b"MP3\x00\x00\x00corrupted")

        result = extractor.extract(corrupted)

        assert isinstance(result, Failure)

    def test_handles_missing_mutagen_library(
        self,
        extractor: MediaExtractor,
        sample_mp3: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Returns graceful error when mutagen is not installed."""

        def mock_import(name, *args, **kwargs):
            if name == "mutagen":
                raise ImportError("No module named 'mutagen'")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Create a new extractor to trigger the import error
        new_extractor = MediaExtractor()
        result = new_extractor.extract(sample_mp3)

        assert isinstance(result, Failure)
        assert "mutagen" in result.failure().lower()


class TestMediaExtractionResult:
    """Tests for MediaExtractionResult data class."""

    def test_has_required_fields(self):
        """MediaExtractionResult has all required fields."""
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

    def test_optional_fields_can_be_none(self):
        """Optional fields can be None."""
        result = MediaExtractionResult(
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

        assert result.codec is None
        assert result.bitrate is None
        assert result.sample_rate is None
        assert result.width is None
        assert result.height is None
        assert result.metadata == {}

    def test_metadata_can_be_empty(self):
        """Metadata dictionary can be empty."""
        result = MediaExtractionResult(
            duration_seconds=0.0,
            format="MP3",
            file_size=512,
            codec=None,
            bitrate=None,
            sample_rate=None,
            width=None,
            height=None,
            metadata={},
        )

        assert result.metadata == {}


class TestSupportedFormats:
    """Tests for format support checking."""

    # Audio formats
    def test_supports_mp3(self, extractor: MediaExtractor):
        """Supports .mp3 extension."""
        assert extractor.supports(Path("audio.mp3"))

    def test_supports_wav(self, extractor: MediaExtractor):
        """Supports .wav extension."""
        assert extractor.supports(Path("audio.wav"))

    def test_supports_m4a(self, extractor: MediaExtractor):
        """Supports .m4a extension."""
        assert extractor.supports(Path("audio.m4a"))

    def test_supports_ogg(self, extractor: MediaExtractor):
        """Supports .ogg extension."""
        assert extractor.supports(Path("audio.ogg"))

    def test_supports_flac(self, extractor: MediaExtractor):
        """Supports .flac extension."""
        assert extractor.supports(Path("audio.flac"))

    def test_supports_aac(self, extractor: MediaExtractor):
        """Supports .aac extension."""
        assert extractor.supports(Path("audio.aac"))

    def test_supports_wma(self, extractor: MediaExtractor):
        """Supports .wma extension."""
        assert extractor.supports(Path("audio.wma"))

    # Video formats
    def test_supports_mp4(self, extractor: MediaExtractor):
        """Supports .mp4 extension."""
        assert extractor.supports(Path("video.mp4"))

    def test_supports_mov(self, extractor: MediaExtractor):
        """Supports .mov extension."""
        assert extractor.supports(Path("video.mov"))

    def test_supports_avi(self, extractor: MediaExtractor):
        """Supports .avi extension."""
        assert extractor.supports(Path("video.avi"))

    def test_supports_mkv(self, extractor: MediaExtractor):
        """Supports .mkv extension."""
        assert extractor.supports(Path("video.mkv"))

    def test_supports_wmv(self, extractor: MediaExtractor):
        """Supports .wmv extension."""
        assert extractor.supports(Path("video.wmv"))

    def test_supports_webm(self, extractor: MediaExtractor):
        """Supports .webm extension."""
        assert extractor.supports(Path("video.webm"))

    def test_supports_m4v(self, extractor: MediaExtractor):
        """Supports .m4v extension."""
        assert extractor.supports(Path("video.m4v"))

    def test_does_not_support_pdf(self, extractor: MediaExtractor):
        """Does not support .pdf extension."""
        assert not extractor.supports(Path("doc.pdf"))

    def test_does_not_support_text(self, extractor: MediaExtractor):
        """Does not support text files."""
        assert not extractor.supports(Path("doc.txt"))

    def test_does_not_support_images(self, extractor: MediaExtractor):
        """Does not support image files."""
        assert not extractor.supports(Path("image.jpg"))
        assert not extractor.supports(Path("image.png"))

    def test_case_insensitive_extension(self, extractor: MediaExtractor):
        """Extension checking is case-insensitive."""
        assert extractor.supports(Path("audio.MP3"))
        assert extractor.supports(Path("video.Mp4"))
        assert extractor.supports(Path("audio.WaV"))


class TestAudioMetadata:
    """Tests for audio-specific metadata extraction."""

    def test_extracts_sample_rate_for_wav(
        self, extractor: MediaExtractor, sample_wav: Path
    ):
        """Extracts sample rate from WAV file."""
        result = extractor.extract(sample_wav)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.sample_rate == 44100

    def test_video_fields_are_none_for_audio(
        self, extractor: MediaExtractor, sample_mp3: Path
    ):
        """Video-specific fields are None for audio files."""
        result = extractor.extract(sample_mp3)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.width is None
        assert data.height is None
