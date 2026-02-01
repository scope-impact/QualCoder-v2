"""
Speaker Detector Domain Service

Pure domain service for detecting speakers in transcript text.
Extracted from presentation layer to maintain proper DDD boundaries.

This service provides speaker detection for:
- Interview transcripts
- Focus group discussions
- Meeting notes

Supported patterns:
- UPPERCASE NAME: format (e.g., "INTERVIEWER: Hello")
- Title Case Name: format (e.g., "John Smith: Hello")
- [Speaker] format (e.g., "[Moderator] Hello")

Usage:
    detector = SpeakerDetector(transcript_text)
    speakers = detector.detect_speakers()
    for speaker in speakers:
        print(f"{speaker.name}: {speaker.count} segments")

    segments = detector.get_speaker_segments("INTERVIEWER")
    for seg in segments:
        print(f"At {seg.start}-{seg.end}: {seg.text}")

ConfigurableSpeakerDetector:
    detector = ConfigurableSpeakerDetector(
        text=transcript,
        custom_patterns=[r"^(P\\d{2}):\\s"],
        include_defaults=True,
    )
    speakers = detector.detect_speakers()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Pattern


@dataclass(frozen=True)
class Speaker:
    """
    Immutable value object representing a detected speaker.

    Attributes:
        name: The speaker's name/identifier
        count: Number of times this speaker appears
    """

    name: str
    count: int


@dataclass(frozen=True)
class SpeakerSegment:
    """
    Immutable value object representing a speaker's text segment.

    Attributes:
        start: Start position in the text (0-indexed)
        end: End position in the text (exclusive)
        text: The text content spoken by the speaker
    """

    start: int
    end: int
    text: str

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end < self.start:
            raise ValueError(f"end ({self.end}) must be >= start ({self.start})")


class SpeakerDetector:
    """
    Pure domain service for detecting speakers in transcript text.

    This is a stateless service that performs speaker detection operations.
    All methods are pure functions that don't modify any state.

    Example:
        detector = SpeakerDetector(transcript)
        speakers = detector.detect_speakers()
        # Returns [Speaker(name="JOHN", count=3), ...]
    """

    # Speaker detection patterns (compiled for performance)
    # Order matters - more specific patterns first
    PATTERNS = [
        # UPPERCASE NAME: (with space after colon)
        re.compile(r"^([A-Z][A-Z\s]+):\s", re.MULTILINE),
        # Title Case Name: (with space after colon)
        re.compile(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s", re.MULTILINE),
        # [Speaker Name] format
        re.compile(r"^\[([^\]]+)\]\s", re.MULTILINE),
    ]

    def __init__(self, text: str) -> None:
        """
        Initialize the detector with text to analyze.

        Args:
            text: The transcript text to analyze
        """
        self._text = text
        self._lines = text.split("\n") if text else []

    def detect_speakers(self) -> list[Speaker]:
        """
        Detect all speakers in the text.

        Returns:
            List of Speaker objects with name and occurrence count.
            Empty list if no speakers found.
        """
        if not self._text:
            return []

        speakers: dict[str, int] = {}

        for line in self._lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            for pattern in self.PATTERNS:
                match = pattern.match(stripped_line)
                if match:
                    name = match.group(1).strip()
                    speakers[name] = speakers.get(name, 0) + 1
                    break  # Only match first pattern per line

        return [Speaker(name=name, count=count) for name, count in speakers.items()]

    def get_speaker_segments(self, speaker_name: str) -> list[SpeakerSegment]:
        """
        Get all segments for a specific speaker.

        Args:
            speaker_name: Name of the speaker to find

        Returns:
            List of SpeakerSegment objects for this speaker.
            Empty list if speaker not found.
        """
        if not self._text or not speaker_name:
            return []

        segments: list[SpeakerSegment] = []
        current_pos = 0

        for line in self._lines:
            stripped_line = line.strip()
            if not stripped_line:
                current_pos += len(line) + 1  # +1 for newline
                continue

            # Find the actual position of the stripped line in the original text
            line_start = self._text.find(stripped_line, current_pos)
            if line_start == -1:
                current_pos += len(line) + 1
                continue

            for pattern in self.PATTERNS:
                match = pattern.match(stripped_line)
                if match and match.group(1).strip() == speaker_name:
                    # Found a segment for this speaker
                    text_after_speaker = stripped_line[match.end() :].strip()
                    text_start = line_start + match.end()
                    text_end = line_start + len(stripped_line)

                    segments.append(
                        SpeakerSegment(
                            start=text_start,
                            end=text_end,
                            text=text_after_speaker,
                        )
                    )
                    break

            current_pos = line_start + len(stripped_line)

        return segments


# =============================================================================
# Configurable Speaker Detection (QC-040.03)
# =============================================================================


class InvalidPatternError(ValueError):
    """Raised when a speaker pattern regex is invalid."""

    def __init__(self, pattern: str, reason: str) -> None:
        self.pattern = pattern
        self.reason = reason
        super().__init__(f"Invalid pattern '{pattern}': {reason}")


@dataclass(frozen=True)
class SpeakerPattern:
    """
    Value object representing a speaker detection pattern.

    Attributes:
        regex: The regex pattern string (must have one capture group for name)
        description: Human-readable description of what this pattern matches
        is_default: Whether this is a built-in default pattern
    """

    regex: str
    description: str
    is_default: bool = False

    def is_valid(self) -> bool:
        """Check if the pattern is valid regex with a capture group."""
        try:
            compiled = re.compile(self.regex, re.MULTILINE)
            # Check for at least one capture group
            return compiled.groups >= 1
        except re.error:
            return False

    def compile(self) -> Pattern:
        """Compile the regex pattern."""
        return re.compile(self.regex, re.MULTILINE)


@dataclass(frozen=True)
class DetectedSpeakerInfo:
    """
    Extended speaker info including segment details.

    Used for speaker-to-code conversion (QC-040.04).
    """

    name: str
    segment_count: int
    segments: tuple[SpeakerSegment, ...]
    suggested_code_color: str | None = None


class ConfigurableSpeakerDetector:
    """
    Extended speaker detector with configurable patterns.

    Supports custom regex patterns in addition to or instead of defaults.
    Used for QC-040.03 (Detect Speakers with configurable format).

    Example:
        detector = ConfigurableSpeakerDetector(
            text=transcript,
            custom_patterns=[r"^(P\\d{2}):\\s"],
            include_defaults=True,
        )
        speakers = detector.detect_speakers()
    """

    # Default patterns (same as SpeakerDetector)
    DEFAULT_PATTERNS = [
        SpeakerPattern(
            regex=r"^([A-Z][A-Z\s]+):\s",
            description="UPPERCASE NAME: format",
            is_default=True,
        ),
        SpeakerPattern(
            regex=r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s",
            description="Title Case Name: format",
            is_default=True,
        ),
        SpeakerPattern(
            regex=r"^\[([^\]]+)\]\s",
            description="[Speaker Name] format",
            is_default=True,
        ),
    ]

    def __init__(
        self,
        text: str,
        custom_patterns: list[str] | None = None,
        include_defaults: bool = True,
    ) -> None:
        """
        Initialize the configurable detector.

        Args:
            text: The transcript text to analyze
            custom_patterns: List of custom regex patterns (must have capture group)
            include_defaults: Whether to include default patterns

        Raises:
            InvalidPatternError: If any custom pattern is invalid
        """
        self._text = text
        self._lines = text.split("\n") if text else []

        # Build pattern list
        self._patterns: list[Pattern] = []

        # Add custom patterns first (higher priority)
        if custom_patterns:
            for pattern_str in custom_patterns:
                self._validate_and_add_pattern(pattern_str)

        # Add defaults if requested
        if include_defaults:
            for sp in self.DEFAULT_PATTERNS:
                self._patterns.append(sp.compile())

    def _validate_and_add_pattern(self, pattern_str: str) -> None:
        """Validate and add a custom pattern."""
        try:
            compiled = re.compile(pattern_str, re.MULTILINE)
        except re.error as e:
            raise InvalidPatternError(pattern_str, f"Invalid regex: {e}")

        if compiled.groups < 1:
            raise InvalidPatternError(
                pattern_str, "Pattern must have at least one capture group for speaker name"
            )

        self._patterns.append(compiled)

    def detect_speakers(self) -> list[Speaker]:
        """
        Detect all speakers in the text.

        Returns:
            List of Speaker objects with name and occurrence count.
        """
        if not self._text:
            return []

        speakers: dict[str, int] = {}

        for line in self._lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            for pattern in self._patterns:
                match = pattern.match(stripped_line)
                if match:
                    name = match.group(1).strip()
                    speakers[name] = speakers.get(name, 0) + 1
                    break

        return [Speaker(name=name, count=count) for name, count in speakers.items()]

    def get_speaker_segments(self, speaker_name: str) -> list[SpeakerSegment]:
        """
        Get all segments for a specific speaker.

        Args:
            speaker_name: Name of the speaker to find

        Returns:
            List of SpeakerSegment objects for this speaker.
        """
        if not self._text or not speaker_name:
            return []

        segments: list[SpeakerSegment] = []
        current_pos = 0

        for line in self._lines:
            stripped_line = line.strip()
            if not stripped_line:
                current_pos += len(line) + 1
                continue

            line_start = self._text.find(stripped_line, current_pos)
            if line_start == -1:
                current_pos += len(line) + 1
                continue

            for pattern in self._patterns:
                match = pattern.match(stripped_line)
                if match and match.group(1).strip() == speaker_name:
                    text_after_speaker = stripped_line[match.end():].strip()
                    text_start = line_start + match.end()
                    text_end = line_start + len(stripped_line)

                    segments.append(
                        SpeakerSegment(
                            start=text_start,
                            end=text_end,
                            text=text_after_speaker,
                        )
                    )
                    break

            current_pos = line_start + len(stripped_line)

        return segments

    def detect_speakers_with_segments(self) -> list[DetectedSpeakerInfo]:
        """
        Detect speakers and include their segment details.

        Returns:
            List of DetectedSpeakerInfo with segments included.
        """
        speakers = self.detect_speakers()
        result = []

        for speaker in speakers:
            segments = self.get_speaker_segments(speaker.name)
            result.append(
                DetectedSpeakerInfo(
                    name=speaker.name,
                    segment_count=speaker.count,
                    segments=tuple(segments),
                    suggested_code_color=None,
                )
            )

        return result
