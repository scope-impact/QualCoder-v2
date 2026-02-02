"""
Auto-Coding Controller - Application Service

Orchestrates auto-coding operations following fDDD architecture:
- Receives commands from presentation layer
- Calls domain services (TextMatcher, SpeakerDetector)
- Uses BatchManager for batch operations
- Publishes domain events

This is the "Imperative Shell" that coordinates the "Functional Core".
Presentation layer should NEVER call domain services directly.

Usage:
    # In presentation setup
    controller = AutoCodingController(
        segment_repo=segment_repo,
        event_bus=event_bus,
    )

    # In UI event handler
    result = controller.find_matches(text, pattern, match_type, scope)
    if result.is_success:
        matches = result.value
        # Update UI with matches
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.application.coding.services.batch_manager import BatchManager
from src.contexts.coding.core.events import BatchCreated, BatchUndone
from src.contexts.coding.core.services.text_matcher import (
    MatchScope,
    MatchType,
    TextMatch,
    TextMatcher,
)
from src.contexts.shared.core.types import CodeId, SegmentId, SourceId
from src.contexts.sources.core.services.speaker_detector import (
    Speaker,
    SpeakerDetector,
    SpeakerSegment,
)

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


@dataclass(frozen=True)
class AutoCodeBatchResult:
    """Result of applying auto-code batch."""

    batch_id: str
    code_id: int
    pattern: str
    segment_count: int
    segment_ids: tuple[int, ...]


@dataclass(frozen=True)
class NothingToUndo:
    """Failure type when no batch to undo."""

    message: str = "No batch to undo"


class AutoCodingController:
    """
    Application service for auto-coding operations.

    Coordinates between:
    - Domain services (TextMatcher, SpeakerDetector)
    - BatchManager for batch tracking
    - Repositories for persistence
    - Event bus for event publishing

    This controller ensures presentation layer never directly
    accesses domain services.
    """

    def __init__(
        self,
        segment_repo: Any | None = None,
        event_bus: EventBus | None = None,
        batch_manager: BatchManager | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            segment_repo: Repository for Segment entities
            event_bus: Event bus for publishing domain events
            batch_manager: Manager for batch operations (optional, creates default)
        """
        self._segment_repo = segment_repo
        self._event_bus = event_bus
        self._batch_manager = batch_manager or BatchManager()

    # =========================================================================
    # Query Operations (Pure - no side effects)
    # =========================================================================

    def find_matches(
        self,
        text: str,
        pattern: str,
        match_type: MatchType = MatchType.EXACT,
        scope: MatchScope = MatchScope.ALL,
        case_sensitive: bool = False,
    ) -> Result[list[TextMatch], str]:
        """
        Find text matches using domain TextMatcher service.

        This is a pure query operation - no state changes.

        Args:
            text: The text to search in
            pattern: The pattern to search for
            match_type: Type of matching (EXACT, CONTAINS, REGEX)
            scope: Scope of results (ALL, FIRST, LAST)
            case_sensitive: Whether matching is case-sensitive

        Returns:
            Result containing list of TextMatch objects on success
        """
        matcher = TextMatcher(text)
        matches = matcher.find_matches(
            pattern=pattern,
            match_type=match_type,
            scope=scope,
            case_sensitive=case_sensitive,
        )
        return Success(matches)

    def detect_speakers(
        self,
        text: str,
    ) -> Result[list[Speaker], str]:
        """
        Detect speakers in text using domain SpeakerDetector service.

        This is a pure query operation - no state changes.

        Args:
            text: The text to analyze for speaker patterns

        Returns:
            Result containing list of Speaker objects on success
        """
        detector = SpeakerDetector(text)
        speakers = detector.detect_speakers()
        return Success(speakers)

    def get_speaker_segments(
        self,
        text: str,
        speaker_name: str,
    ) -> Result[list[SpeakerSegment], str]:
        """
        Get text segments for a specific speaker.

        This is a pure query operation - no state changes.

        Args:
            text: The text to analyze
            speaker_name: Name of the speaker to get segments for

        Returns:
            Result containing list of SpeakerSegment objects on success
        """
        detector = SpeakerDetector(text)
        segments = detector.get_speaker_segments(speaker_name)
        return Success(segments)

    # =========================================================================
    # Command Operations (Side effects - persist and publish)
    # =========================================================================

    def apply_auto_code_batch(
        self,
        source_id: SourceId,
        code_id: CodeId,
        pattern: str,
        matches: list[TextMatch],
        owner: str | None = None,
    ) -> Result[AutoCodeBatchResult, str]:
        """
        Apply a code to multiple text matches as a batch.

        Creates segments for each match and records the batch
        for potential undo.

        Args:
            source_id: ID of the source document
            code_id: ID of the code to apply
            pattern: The search pattern used
            matches: List of TextMatch objects to code
            owner: Optional owner/coder identifier

        Returns:
            Result containing AutoCodeBatchResult on success
        """
        segment_ids: list[SegmentId] = []

        # Create segments for each match
        for match in matches:
            segment_id = SegmentId.new()
            segment_ids.append(segment_id)

            # Persist segment if repo is available
            if self._segment_repo:
                # Create segment entity and save
                # (simplified - actual implementation would create full entity)
                self._segment_repo.save(
                    {
                        "id": segment_id.value,
                        "source_id": source_id.value,
                        "code_id": code_id.value,
                        "start": match.start,
                        "end": match.end,
                    }
                )

        # Create batch record for undo
        batch_id = self._batch_manager.create_batch(
            code_id=code_id,
            pattern=pattern,
            segment_ids=segment_ids,
        )

        # Create and publish event
        event = BatchCreated.create(
            batch_id=batch_id,
            code_id=code_id,
            pattern=pattern,
            segment_ids=tuple(segment_ids),
            owner=owner,
        )

        if self._event_bus:
            self._event_bus.publish(event)

        # Return result
        return Success(
            AutoCodeBatchResult(
                batch_id=batch_id.value,
                code_id=code_id.value,
                pattern=pattern,
                segment_count=len(segment_ids),
                segment_ids=tuple(sid.value for sid in segment_ids),
            )
        )

    def undo_last_batch(self) -> Result[AutoCodeBatchResult, NothingToUndo]:
        """
        Undo the last auto-code batch.

        Removes segments created by the last batch and removes
        the batch from history.

        Returns:
            Result containing undone batch info on success,
            Failure with NothingToUndo if no batch to undo
        """
        # Get last batch from manager
        batch = self._batch_manager.undo_last_batch()

        if batch is None:
            return Failure(NothingToUndo())

        # Delete segments if repo available
        if self._segment_repo:
            for segment_id in batch.segment_ids:
                self._segment_repo.delete(segment_id)

        # Publish undo event
        event = BatchUndone.create(
            batch_id=batch.id,
            segments_removed=len(batch.segment_ids),
        )

        if self._event_bus:
            self._event_bus.publish(event)

        # Return result
        return Success(
            AutoCodeBatchResult(
                batch_id=batch.id.value,
                code_id=batch.code_id.value,
                pattern=batch.pattern,
                segment_count=len(batch.segment_ids),
                segment_ids=tuple(sid.value for sid in batch.segment_ids),
            )
        )

    # =========================================================================
    # Batch Query Methods
    # =========================================================================

    def get_batch_count(self) -> int:
        """Get number of batches in undo history."""
        return self._batch_manager.batch_count

    def can_undo(self) -> bool:
        """Check if there's a batch that can be undone."""
        return self._batch_manager.batch_count > 0
