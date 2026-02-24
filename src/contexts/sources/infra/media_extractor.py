"""
Media Extractor Service - Infrastructure Layer.

Extracts metadata from audio and video files including duration, format, codec, and bitrate.

Usage:
    extractor = MediaExtractor()
    result = extractor.extract(Path("interview.mp3"))
    if isinstance(result, Success):
        metadata = result.unwrap()
        print(f"Duration: {metadata.duration_seconds}s")
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from returns.result import Failure, Result, Success


@dataclass(frozen=True)
class MediaExtractionResult:
    """Result of media metadata extraction."""

    duration_seconds: float
    format: str
    file_size: int
    codec: str | None
    bitrate: int | None
    sample_rate: int | None
    width: int | None
    height: int | None
    metadata: dict[str, Any]


AUDIO_EXTENSIONS = frozenset(
    {
        ".mp3",
        ".wav",
        ".m4a",
        ".ogg",
        ".flac",
        ".aac",
        ".wma",
    }
)

VIDEO_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".wmv",
        ".webm",
        ".m4v",
    }
)

MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


class MediaExtractor:
    """
    Service for extracting metadata from audio and video files.

    Supports:
    - Audio: MP3, WAV, M4A, OGG, FLAC, AAC, WMA
    - Video: MP4, MOV, AVI, MKV, WMV, WEBM, M4V

    Uses the mutagen library for metadata extraction.

    Example:
        extractor = MediaExtractor()
        result = extractor.extract(Path("interview.mp3"))
        if isinstance(result, Success):
            data = result.unwrap()
            print(f"{data.duration_seconds}s {data.format}")
    """

    def supports(self, path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return path.suffix.lower() in MEDIA_EXTENSIONS

    def extract(self, path: Path) -> Result[MediaExtractionResult, str]:
        """
        Extract metadata from an audio or video file.

        Args:
            path: Path to the media file

        Returns:
            Success with MediaExtractionResult, or Failure with error message
        """
        if not path.exists():
            return Failure(f"File not found: {path}")

        try:
            import mutagen
        except ImportError:
            return Failure(
                "mutagen library not installed. Install with: pip install mutagen"
            )

        try:
            # Load the media file
            media = mutagen.File(path)

            if media is None:
                return Failure(f"Cannot identify media file: {path}")

            # Extract basic metadata
            file_size = path.stat().st_size
            duration = getattr(media.info, "length", 0.0)

            # Extract format information
            format_name = self._get_format_name(media, path)

            # Extract codec information
            codec = self._extract_codec(media)

            # Extract bitrate
            bitrate = self._extract_bitrate(media)

            # Extract sample rate (for audio)
            sample_rate = self._extract_sample_rate(media)

            # Extract video dimensions (for video)
            width, height = self._extract_dimensions(media)

            # Extract additional metadata
            metadata = self._extract_metadata_dict(media)

            return Success(
                MediaExtractionResult(
                    duration_seconds=duration,
                    format=format_name,
                    file_size=file_size,
                    codec=codec,
                    bitrate=bitrate,
                    sample_rate=sample_rate,
                    width=width,
                    height=height,
                    metadata=metadata,
                )
            )

        except Exception as e:
            return Failure(f"Error extracting media metadata: {e}")

    def _get_format_name(self, media: Any, path: Path) -> str:
        """
        Extract format name from media file.

        Returns uppercase extension as fallback.
        """
        # Try to get format from mutagen
        if hasattr(media, "mime"):
            mime_type = media.mime[0] if media.mime else ""
            if "mp3" in mime_type.lower():
                return "MP3"
            elif "mp4" in mime_type.lower():
                return "MP4"
            elif "ogg" in mime_type.lower():
                return "OGG"
            elif "flac" in mime_type.lower():
                return "FLAC"

        # Fallback to extension
        ext = path.suffix.upper().lstrip(".")
        return ext

    def _get_info_int(self, media: Any, attr: str) -> int | None:
        """Get an integer attribute from media.info, or None if unavailable."""
        info = getattr(media, "info", None)
        if info is None:
            return None
        value = getattr(info, attr, None)
        return int(value) if value is not None else None

    def _extract_codec(self, media: Any) -> str | None:
        """Extract codec information from media file."""
        info = getattr(media, "info", None)
        if info is None:
            return None

        for attr in ("codec", "codec_name", "format"):
            codec = getattr(info, attr, None)
            if codec:
                return str(codec)

        return None

    def _extract_bitrate(self, media: Any) -> int | None:
        """Extract bitrate in bits per second."""
        return self._get_info_int(media, "bitrate")

    def _extract_sample_rate(self, media: Any) -> int | None:
        """Extract sample rate in Hz (for audio files)."""
        return self._get_info_int(media, "sample_rate")

    def _extract_dimensions(self, media: Any) -> tuple[int | None, int | None]:
        """Extract video dimensions (width, height)."""
        return self._get_info_int(media, "width"), self._get_info_int(media, "height")

    def _extract_metadata_dict(self, media: Any) -> dict[str, Any]:
        """Extract metadata dictionary from media tags (ID3, Vorbis, etc.)."""
        tags = getattr(media, "tags", None)
        if tags is None:
            return {}

        metadata: dict[str, Any] = {}
        for key, value in tags.items():
            if isinstance(value, list):
                metadata[str(key)] = [self._to_str(item) for item in value]
            else:
                metadata[str(key)] = self._to_str(value)
        return metadata

    @staticmethod
    def _to_str(value: Any) -> str:
        """Convert a tag value to string, decoding bytes as UTF-8."""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        return str(value)
