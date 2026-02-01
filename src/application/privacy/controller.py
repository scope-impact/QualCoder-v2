"""
Privacy Controller - Application Service.

Orchestrates privacy domain operations following the 5-step pattern:
1. Validate (Pydantic does automatically)
2. Build current state
3. Derive event (call pure domain function)
4. Persist on success
5. Publish event

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.privacy.commands import (
    ApplyPseudonymsCommand,
    ConvertSpeakersToCodesCommand,
    CreatePseudonymCommand,
    DeletePseudonymCommand,
    DetectSpeakersCommand,
    PreviewSpeakerConversionCommand,
    RevertAnonymizationCommand,
    UpdatePseudonymCommand,
)
from src.domain.coding.entities import Code, Color, TextPosition, TextSegment
from src.domain.privacy.derivers import (
    PrivacyState,
    derive_create_pseudonym,
    derive_delete_pseudonym,
    derive_update_pseudonym,
)
from src.domain.privacy.entities import (
    AnonymizationSession,
    AnonymizationSessionId,
    Pseudonym,
    PseudonymCategory,
    PseudonymId,
)
from src.domain.privacy.events import (
    AnonymizationReverted,
    PseudonymCreated,
    PseudonymDeleted,
    PseudonymUpdated,
    PseudonymsApplied,
)
from src.domain.privacy.services.anonymizer import TextAnonymizer
from src.domain.shared.types import CodeId, SegmentId, SourceId
from src.domain.sources.services.speaker_detector import (
    ConfigurableSpeakerDetector,
    DetectedSpeakerInfo,
)

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.coding.repositories import (
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )
    from src.infrastructure.privacy.repositories import (
        SQLiteAnonymizationSessionRepository,
        SQLitePseudonymRepository,
    )


@dataclass(frozen=True)
class ApplyPseudonymsResult:
    """Result of applying pseudonyms to text."""

    anonymized_text: str
    session_id: AnonymizationSessionId
    replacement_count: int


@dataclass(frozen=True)
class RevertResult:
    """Result of reverting anonymization."""

    original_text: str
    session_id: AnonymizationSessionId


@dataclass(frozen=True)
class ConvertSpeakersResult:
    """Result of converting speakers to codes."""

    code_count: int
    segment_count: int
    codes_created: tuple[str, ...]
    segments_created: int


@dataclass(frozen=True)
class PreviewConversionResult:
    """Preview of speaker-to-code conversion."""

    speakers: tuple[DetectedSpeakerInfo, ...]
    total_segments: int


# Color palette for speaker codes (distinct, visually appealing)
SPEAKER_COLORS = [
    Color(66, 133, 244),   # Blue
    Color(219, 68, 55),    # Red
    Color(244, 180, 0),    # Yellow
    Color(15, 157, 88),    # Green
    Color(171, 71, 188),   # Purple
    Color(255, 112, 67),   # Orange
    Color(0, 172, 193),    # Cyan
    Color(124, 77, 255),   # Violet
    Color(255, 167, 38),   # Amber
    Color(0, 150, 136),    # Teal
]


class PrivacyController:
    """
    Application service for privacy operations.

    Orchestrates domain services, repositories, and event publishing.
    Follows the 5-step controller pattern.
    """

    def __init__(
        self,
        pseudonym_repo: SQLitePseudonymRepository,
        session_repo: SQLiteAnonymizationSessionRepository,
        event_bus: EventBus,
        code_repo: SQLiteCodeRepository | None = None,
        segment_repo: SQLiteSegmentRepository | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            pseudonym_repo: Repository for Pseudonym entities
            session_repo: Repository for AnonymizationSession entities
            event_bus: Event bus for publishing domain events
            code_repo: Optional repository for Code entities (for speaker-to-code)
            segment_repo: Optional repository for Segment entities (for speaker-to-code)
        """
        self._pseudonym_repo = pseudonym_repo
        self._session_repo = session_repo
        self._event_bus = event_bus
        self._code_repo = code_repo
        self._segment_repo = segment_repo

    # =========================================================================
    # Pseudonym Commands
    # =========================================================================

    def create_pseudonym(
        self, command: CreatePseudonymCommand
    ) -> Result[Pseudonym, str]:
        """
        Create a new pseudonym mapping.

        Args:
            command: Create command with real_name, alias, category

        Returns:
            Success with Pseudonym on success, Failure with reason on error
        """
        # Step 2: Build current state
        state = self._build_privacy_state()

        # Step 3: Derive event (pure function)
        result = derive_create_pseudonym(
            real_name=command.real_name,
            alias=command.alias,
            category=command.category,
            notes=command.notes,
            state=state,
        )

        # Step 4: Handle failure or persist
        if isinstance(result, Failure):
            return result

        event: PseudonymCreated = result

        # Create entity from event
        pseudonym = Pseudonym(
            id=event.pseudonym_id,
            real_name=event.real_name,
            alias=event.alias,
            category=PseudonymCategory(event.category),
            notes=command.notes,
        )

        self._pseudonym_repo.save(pseudonym)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(pseudonym)

    def update_pseudonym(
        self, command: UpdatePseudonymCommand
    ) -> Result[Pseudonym, str]:
        """
        Update an existing pseudonym.

        Args:
            command: Update command with pseudonym_id and new values

        Returns:
            Success with updated Pseudonym on success, Failure on error
        """
        # Step 2: Build state
        state = self._build_privacy_state()

        # Step 3: Derive event
        result = derive_update_pseudonym(
            pseudonym_id=PseudonymId(value=command.pseudonym_id),
            new_alias=command.new_alias,
            new_notes=command.new_notes,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: PseudonymUpdated = result

        # Step 4: Get existing and update
        existing = self._pseudonym_repo.get_by_id(
            PseudonymId(value=command.pseudonym_id)
        )
        if existing is None:
            return Failure("Pseudonym not found")

        updated = existing
        if command.new_alias:
            updated = updated.with_alias(command.new_alias)
        if command.new_notes is not None:
            updated = updated.with_notes(command.new_notes)

        self._pseudonym_repo.save(updated)

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(updated)

    def delete_pseudonym(
        self, command: DeletePseudonymCommand
    ) -> Result[None, str]:
        """
        Delete a pseudonym.

        Args:
            command: Delete command with pseudonym_id

        Returns:
            Success on success, Failure on error
        """
        # Step 2: Build state
        state = self._build_privacy_state()

        # Step 3: Derive event
        result = derive_delete_pseudonym(
            pseudonym_id=PseudonymId(value=command.pseudonym_id),
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: PseudonymDeleted = result

        # Step 4: Delete from repository
        self._pseudonym_repo.delete(PseudonymId(value=command.pseudonym_id))

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(None)

    # =========================================================================
    # Pseudonym Queries
    # =========================================================================

    def get_all_pseudonyms(self) -> list[Pseudonym]:
        """Get all pseudonyms."""
        return self._pseudonym_repo.get_all()

    def get_pseudonyms_by_category(
        self, category: PseudonymCategory
    ) -> list[Pseudonym]:
        """Get pseudonyms filtered by category."""
        return self._pseudonym_repo.get_by_category(category)

    # =========================================================================
    # Apply Pseudonyms
    # =========================================================================

    def apply_pseudonyms(
        self, command: ApplyPseudonymsCommand
    ) -> Result[ApplyPseudonymsResult, str]:
        """
        Apply pseudonyms to source text.

        Args:
            command: Apply command with source_id, source_text, options

        Returns:
            Success with ApplyPseudonymsResult on success, Failure on error
        """
        # Get pseudonyms to apply
        if command.pseudonym_ids:
            pseudonyms = [
                self._pseudonym_repo.get_by_id(PseudonymId(value=pid))
                for pid in command.pseudonym_ids
            ]
            pseudonyms = [p for p in pseudonyms if p is not None]
        else:
            pseudonyms = self._pseudonym_repo.get_all()

        if not pseudonyms:
            return Failure("No pseudonyms to apply")

        # Apply anonymization using domain service
        anonymizer = TextAnonymizer(command.source_text)
        anon_result = anonymizer.apply_pseudonyms(
            pseudonyms=pseudonyms,
            match_case=command.match_case,
            whole_word=command.whole_word,
        )

        # Create session for reversal
        session_id = AnonymizationSessionId.new()
        session = AnonymizationSession(
            id=session_id,
            source_id=SourceId(value=command.source_id),
            original_text=command.source_text,
            pseudonym_ids=tuple(p.id for p in pseudonyms),
            replacements=anon_result.replacements,
        )

        self._session_repo.save(session)

        # Publish event
        event = PseudonymsApplied.create(
            session_id=session_id,
            source_id=SourceId(value=command.source_id),
            pseudonym_count=len(pseudonyms),
            replacement_count=len(anon_result.replacements),
        )
        self._event_bus.publish(event)

        return Success(
            ApplyPseudonymsResult(
                anonymized_text=anon_result.anonymized_text,
                session_id=session_id,
                replacement_count=len(anon_result.replacements),
            )
        )

    # =========================================================================
    # Revert Anonymization
    # =========================================================================

    def revert_anonymization(
        self, command: RevertAnonymizationCommand
    ) -> Result[RevertResult, str]:
        """
        Revert anonymization to original text.

        Args:
            command: Revert command with source_id, session_id

        Returns:
            Success with RevertResult on success, Failure on error
        """
        # Get session
        if command.session_id:
            session = self._session_repo.get_by_id(
                AnonymizationSessionId(value=command.session_id)
            )
        else:
            session = self._session_repo.get_active_session(
                SourceId(value=command.source_id)
            )

        if session is None:
            return Failure("Anonymization session not found")

        if not session.is_reversible():
            return Failure("Session has already been reverted")

        # Mark as reverted
        self._session_repo.mark_reverted(session.id)

        # Publish event
        event = AnonymizationReverted.create(
            session_id=session.id,
            source_id=session.source_id,
        )
        self._event_bus.publish(event)

        return Success(
            RevertResult(
                original_text=session.original_text,
                session_id=session.id,
            )
        )

    # =========================================================================
    # Speaker Detection and Conversion (QC-040.04)
    # =========================================================================

    def detect_speakers(
        self, command: DetectSpeakersCommand
    ) -> Result[list[DetectedSpeakerInfo], str]:
        """
        Detect speakers in source text.

        Args:
            command: Detect command with source_id, source_text, patterns

        Returns:
            Success with list of DetectedSpeakerInfo on success, Failure on error
        """
        # Create detector with configured patterns
        custom_patterns = list(command.custom_patterns) if command.custom_patterns else None
        detector = ConfigurableSpeakerDetector(
            text=command.source_text,
            custom_patterns=custom_patterns,
            include_defaults=command.include_defaults,
        )

        # Detect speakers with segments
        speakers = detector.detect_speakers_with_segments()

        return Success(speakers)

    def convert_speakers_to_codes(
        self, command: ConvertSpeakersToCodesCommand
    ) -> Result[ConvertSpeakersResult, str]:
        """
        Convert detected speakers to codes and auto-code their segments.

        Args:
            command: Convert command with source_id, source_text, speakers

        Returns:
            Success with ConvertSpeakersResult on success, Failure on error
        """
        if self._code_repo is None or self._segment_repo is None:
            return Failure("Code and segment repositories required for speaker conversion")

        if not command.speakers:
            return Failure("No speakers to convert")

        # Detect speaker segments
        custom_patterns = list(command.custom_patterns) if command.custom_patterns else None
        detector = ConfigurableSpeakerDetector(
            text=command.source_text,
            custom_patterns=custom_patterns,
            include_defaults=True,
        )

        source_id = SourceId(value=command.source_id)
        codes_created: list[str] = []
        segments_created = 0
        color_index = 0

        for speaker_name in command.speakers:
            # Get segments for this speaker
            speaker_segments = detector.get_speaker_segments(speaker_name)

            # Check if code already exists
            existing_code = self._code_repo.get_by_name(speaker_name)
            if existing_code:
                code = existing_code
            else:
                # Create new code with unique color
                color = SPEAKER_COLORS[color_index % len(SPEAKER_COLORS)]
                color_index += 1

                code = Code(
                    id=CodeId.new(),
                    name=speaker_name,
                    color=color,
                    memo=f"Auto-generated speaker code for {speaker_name}",
                    category_id=None,
                    owner=None,
                )
                self._code_repo.save(code)
                codes_created.append(speaker_name)

            # Create segments for speaker text
            for seg in speaker_segments:
                segment = TextSegment(
                    id=SegmentId.new(),
                    source_id=source_id,
                    code_id=code.id,
                    position=TextPosition(start=seg.start, end=seg.end),
                    selected_text=seg.text,
                    memo=None,
                    importance=0,
                    owner=None,
                )
                self._segment_repo.save(segment)
                segments_created += 1

        # Publish events for codes created
        for code_name in codes_created:
            # Simple event for code creation
            self._event_bus.publish(
                PseudonymCreated(
                    event_id=f"code_{code_name}",
                    occurred_at=datetime.now(UTC),
                    pseudonym_id=PseudonymId(value=0),
                    real_name=code_name,
                    alias=code_name,
                    category="speaker",
                )
            )

        return Success(
            ConvertSpeakersResult(
                code_count=len(command.speakers),
                segment_count=segments_created,
                codes_created=tuple(codes_created),
                segments_created=segments_created,
            )
        )

    def preview_speaker_conversion(
        self, command: PreviewSpeakerConversionCommand
    ) -> Result[PreviewConversionResult, str]:
        """
        Preview speaker-to-code conversion without persisting.

        Args:
            command: Preview command with source_id, source_text, speakers

        Returns:
            Success with PreviewConversionResult on success, Failure on error
        """
        # Create detector
        detector = ConfigurableSpeakerDetector(
            text=command.source_text,
            custom_patterns=None,
            include_defaults=True,
        )

        # Detect speakers with segments
        all_speakers = detector.detect_speakers_with_segments()

        # Filter to requested speakers
        speaker_set = set(command.speakers)
        filtered_speakers = [s for s in all_speakers if s.name in speaker_set]

        total_segments = sum(s.segment_count for s in filtered_speakers)

        return Success(
            PreviewConversionResult(
                speakers=tuple(filtered_speakers),
                total_segments=total_segments,
            )
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _build_privacy_state(self) -> PrivacyState:
        """Build current privacy state from repositories."""
        pseudonyms = self._pseudonym_repo.get_all()
        # Sessions not needed for pseudonym operations
        return PrivacyState(
            existing_pseudonyms=tuple(pseudonyms),
            existing_sessions=(),
        )
