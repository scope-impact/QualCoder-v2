"""
Auto-Coding Signal Payloads - UI-friendly DTOs for signal emission.

These immutable types carry data from the AutoCodingController
to UI components via the Signal Bridge. They use primitive types
only - no domain objects.

Following the fDDD architecture:
- Domain events → Payloads (converted by Signal Bridge)
- Payloads → UI widgets (via Qt signals)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class TextMatchPayload:
    """
    UI payload for a single text match.

    Carries match position data in primitive types.
    """

    start: int
    end: int

    @property
    def length(self) -> int:
        """Length of the match."""
        return self.end - self.start


@dataclass(frozen=True)
class MatchesFoundPayload:
    """
    UI payload for find matches operation result.

    Emitted when the controller completes a find_matches operation.
    """

    timestamp: datetime
    pattern: str
    match_type: str  # "exact", "contains", "regex"
    scope: str  # "all", "first", "last"
    matches: tuple[TextMatchPayload, ...]
    total_count: int

    @classmethod
    def from_matches(
        cls,
        pattern: str,
        match_type: str,
        scope: str,
        matches: list[tuple[int, int]],
    ) -> MatchesFoundPayload:
        """Create payload from match list."""
        return cls(
            timestamp=datetime.now(UTC),
            pattern=pattern,
            match_type=match_type,
            scope=scope,
            matches=tuple(TextMatchPayload(start=m[0], end=m[1]) for m in matches),
            total_count=len(matches),
        )


@dataclass(frozen=True)
class SpeakerPayload:
    """
    UI payload for a detected speaker.
    """

    name: str
    count: int


@dataclass(frozen=True)
class SpeakersDetectedPayload:
    """
    UI payload for speaker detection result.

    Emitted when the controller completes a detect_speakers operation.
    """

    timestamp: datetime
    speakers: tuple[SpeakerPayload, ...]
    total_count: int

    @classmethod
    def from_speakers(
        cls,
        speakers: list[dict[str, any]],
    ) -> SpeakersDetectedPayload:
        """Create payload from speaker list."""
        return cls(
            timestamp=datetime.now(UTC),
            speakers=tuple(
                SpeakerPayload(name=s["name"], count=s["count"]) for s in speakers
            ),
            total_count=len(speakers),
        )


@dataclass(frozen=True)
class SpeakerSegmentPayload:
    """
    UI payload for a speaker's text segment.
    """

    start: int
    end: int
    text: str


@dataclass(frozen=True)
class SpeakerSegmentsPayload:
    """
    UI payload for speaker segments result.

    Emitted when getting segments for a specific speaker.
    """

    timestamp: datetime
    speaker_name: str
    segments: tuple[SpeakerSegmentPayload, ...]
    total_count: int

    @classmethod
    def from_segments(
        cls,
        speaker_name: str,
        segments: list[dict[str, any]],
    ) -> SpeakerSegmentsPayload:
        """Create payload from segment list."""
        return cls(
            timestamp=datetime.now(UTC),
            speaker_name=speaker_name,
            segments=tuple(
                SpeakerSegmentPayload(
                    start=s["start"],
                    end=s["end"],
                    text=s["text"],
                )
                for s in segments
            ),
            total_count=len(segments),
        )


@dataclass(frozen=True)
class AutoCodeBatchAppliedPayload:
    """
    UI payload for auto-code batch application result.

    Emitted when a batch of auto-coding is applied.
    """

    timestamp: datetime
    batch_id: str
    code_id: int
    code_name: str
    pattern: str
    segment_count: int
    can_undo: bool

    @classmethod
    def from_result(
        cls,
        batch_id: str,
        code_id: int,
        code_name: str,
        pattern: str,
        segment_count: int,
    ) -> AutoCodeBatchAppliedPayload:
        """Create payload from batch result."""
        return cls(
            timestamp=datetime.now(UTC),
            batch_id=batch_id,
            code_id=code_id,
            code_name=code_name,
            pattern=pattern,
            segment_count=segment_count,
            can_undo=segment_count > 0,
        )


@dataclass(frozen=True)
class AutoCodeBatchUndonePayload:
    """
    UI payload for auto-code batch undo result.

    Emitted when a batch is undone.
    """

    timestamp: datetime
    batch_id: str
    segments_removed: int

    @classmethod
    def from_result(
        cls,
        batch_id: str,
        segments_removed: int,
    ) -> AutoCodeBatchUndonePayload:
        """Create payload from undo result."""
        return cls(
            timestamp=datetime.now(UTC),
            batch_id=batch_id,
            segments_removed=segments_removed,
        )


@dataclass(frozen=True)
class AutoCodeErrorPayload:
    """
    UI payload for auto-coding errors.

    Emitted when an operation fails.
    """

    timestamp: datetime
    operation: str  # "find_matches", "detect_speakers", "apply_batch", "undo"
    error_message: str
    error_code: str | None = None

    @classmethod
    def from_error(
        cls,
        operation: str,
        error_message: str,
        error_code: str | None = None,
    ) -> AutoCodeErrorPayload:
        """Create payload from error."""
        return cls(
            timestamp=datetime.now(UTC),
            operation=operation,
            error_message=error_message,
            error_code=error_code,
        )
