"""
AI Coding Signal Bridge - Domain Events to Qt Signals

Converts AI-related domain events from the Coding context into Qt signals
for reactive UI updates.

Usage:
    from src.application.coding.ai_signal_bridge import AICodingSignalBridge
    from src.application.event_bus import get_event_bus

    bridge = AICodingSignalBridge.instance(get_event_bus())
    bridge.codes_suggested.connect(on_codes_suggested)
    bridge.start()
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from src.application.coding.ai_coding_payloads import (
    CodeSuggestionPayload,
    DuplicateCandidatePayload,
    DuplicatesDetectedPayload,
    MergeApprovedPayload,
    MergeDismissedPayload,
    SuggestionApprovedPayload,
    SuggestionRejectedPayload,
)
from src.application.signal_bridge.base import BaseSignalBridge
from src.application.signal_bridge.protocols import EventConverter
from src.domain.ai_services.events import (
    CodeSuggested,
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicatesDetected,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
)

# =============================================================================
# Converters - Transform events to payloads
# =============================================================================


class CodeSuggestedConverter(EventConverter):
    """Convert CodeSuggested event to payload."""

    def convert(self, event: CodeSuggested) -> CodeSuggestionPayload:
        contexts = [
            {
                "text": ctx.text,
                "source_id": ctx.source_id.value,
                "start": ctx.position.start,
                "end": ctx.position.end,
            }
            for ctx in event.contexts
        ]

        return CodeSuggestionPayload.from_suggestion(
            suggestion_id=event.suggestion_id.value,
            name=event.name,
            color=event.color.to_hex(),
            rationale=event.rationale,
            contexts=contexts,
            confidence=event.confidence,
            source_id=event.source_id.value,
        )


class CodeSuggestionApprovedConverter(EventConverter):
    """Convert CodeSuggestionApproved event to payload."""

    def convert(self, event: CodeSuggestionApproved) -> SuggestionApprovedPayload:
        return SuggestionApprovedPayload.from_result(
            suggestion_id=event.suggestion_id.value,
            original_name=event.original_name,
            final_name=event.final_name,
            created_code_id=event.created_code_id.value,
            modified=event.modified,
        )


class CodeSuggestionRejectedConverter(EventConverter):
    """Convert CodeSuggestionRejected event to payload."""

    def convert(self, event: CodeSuggestionRejected) -> SuggestionRejectedPayload:
        return SuggestionRejectedPayload.from_result(
            suggestion_id=event.suggestion_id.value,
            name=event.name,
            reason=event.reason,
        )


class DuplicatesDetectedConverter(EventConverter):
    """Convert DuplicatesDetected event to payload."""

    def convert(self, event: DuplicatesDetected) -> DuplicatesDetectedPayload:
        candidates = [
            DuplicateCandidatePayload.from_candidate(
                code_a_id=c.code_a_id.value,
                code_a_name=c.code_a_name,
                code_b_id=c.code_b_id.value,
                code_b_name=c.code_b_name,
                similarity=c.similarity.value,
                rationale=c.rationale,
                code_a_segment_count=c.code_a_segment_count,
                code_b_segment_count=c.code_b_segment_count,
            )
            for c in event.candidates
        ]

        return DuplicatesDetectedPayload.from_results(
            candidates=candidates,
            threshold=event.threshold,
            codes_analyzed=event.codes_analyzed,
        )


class MergeSuggestionApprovedConverter(EventConverter):
    """Convert MergeSuggestionApproved event to payload."""

    def convert(self, event: MergeSuggestionApproved) -> MergeApprovedPayload:
        return MergeApprovedPayload.from_result(
            source_code_id=event.source_code_id.value,
            source_code_name="",  # Not in event
            target_code_id=event.target_code_id.value,
            target_code_name="",  # Not in event
            segments_moved=event.segments_moved,
        )


class MergeSuggestionDismissedConverter(EventConverter):
    """Convert MergeSuggestionDismissed event to payload."""

    def convert(self, event: MergeSuggestionDismissed) -> MergeDismissedPayload:
        return MergeDismissedPayload.from_result(
            code_a_id=event.source_code_id.value,
            code_b_id=event.target_code_id.value,
            reason=event.reason,
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class AICodingSignalBridge(BaseSignalBridge):
    """
    Signal bridge for AI coding features.

    Emits Qt signals when AI-related domain events occur,
    enabling reactive UI updates for code suggestions and
    duplicate detection.

    Signals:
        code_suggested: Emitted when AI suggests a new code
        suggestion_approved: Emitted when researcher approves a suggestion
        suggestion_rejected: Emitted when researcher rejects a suggestion
        duplicates_detected: Emitted when AI finds potential duplicates
        merge_approved: Emitted when researcher approves a merge
        merge_dismissed: Emitted when researcher dismisses a merge suggestion

    Usage:
        bridge = AICodingSignalBridge.instance(event_bus)
        bridge.code_suggested.connect(self._on_code_suggested)
        bridge.start()
    """

    # Code suggestion signals
    code_suggested = Signal(object)
    suggestion_approved = Signal(object)
    suggestion_rejected = Signal(object)

    # Duplicate detection signals
    duplicates_detected = Signal(object)
    merge_approved = Signal(object)
    merge_dismissed = Signal(object)

    def _get_context_name(self) -> str:
        """Return the bounded context name."""
        return "ai_coding"

    def _register_converters(self) -> None:
        """Register all event converters."""
        # Code suggestion events
        self.register_converter(
            "ai_services.code_suggested",
            CodeSuggestedConverter(),
            "code_suggested",
        )
        self.register_converter(
            "ai_services.code_suggestion_approved",
            CodeSuggestionApprovedConverter(),
            "suggestion_approved",
        )
        self.register_converter(
            "ai_services.code_suggestion_rejected",
            CodeSuggestionRejectedConverter(),
            "suggestion_rejected",
        )

        # Duplicate detection events
        self.register_converter(
            "ai_services.duplicates_detected",
            DuplicatesDetectedConverter(),
            "duplicates_detected",
        )
        self.register_converter(
            "ai_services.merge_suggestion_approved",
            MergeSuggestionApprovedConverter(),
            "merge_approved",
        )
        self.register_converter(
            "ai_services.merge_suggestion_dismissed",
            MergeSuggestionDismissedConverter(),
            "merge_dismissed",
        )
