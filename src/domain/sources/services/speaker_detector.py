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
"""

from __future__ import annotations

import re
from dataclasses import dataclass


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
