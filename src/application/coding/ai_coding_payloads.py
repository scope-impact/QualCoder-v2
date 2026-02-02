"""
AI Coding Signal Payloads - UI-friendly DTOs for signal emission.

These immutable types carry data from AI use cases
to UI components via the Signal Bridge. They use primitive types
only - no domain objects.

Following the fDDD architecture:
- Domain events → Payloads (converted by Signal Bridge)
- Payloads → UI widgets (via Qt signals)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# ============================================================
# Code Suggestion Payloads
# ============================================================


@dataclass(frozen=True)
class TextContextPayload:
    """
    UI payload for a text context that led to a suggestion.

    Carries context data in primitive types.
    """

    text: str
    source_id: int
    start: int
    end: int

    @property
    def preview(self) -> str:
        """Return truncated preview (max 100 chars)."""
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."


@dataclass(frozen=True)
class CodeSuggestionPayload:
    """
    UI payload for a code suggestion.

    Emitted when the AI suggests a new code.
    """

    suggestion_id: str
    name: str
    color: str  # Hex string
    rationale: str
    contexts: tuple[TextContextPayload, ...]
    confidence: float  # 0.0-1.0
    confidence_percent: int  # 0-100
    status: str  # "pending", "approved", "rejected"
    timestamp: datetime
    source_id: int
    is_ai_action: bool = True

    @classmethod
    def from_suggestion(
        cls,
        suggestion_id: str,
        name: str,
        color: str,
        rationale: str,
        contexts: list[dict],
        confidence: float,
        source_id: int,
    ) -> CodeSuggestionPayload:
        """Create payload from suggestion data."""
        return cls(
            suggestion_id=suggestion_id,
            name=name,
            color=color,
            rationale=rationale,
            contexts=tuple(
                TextContextPayload(
                    text=c["text"],
                    source_id=c["source_id"],
                    start=c["start"],
                    end=c["end"],
                )
                for c in contexts
            ),
            confidence=confidence,
            confidence_percent=int(confidence * 100),
            status="pending",
            timestamp=datetime.now(UTC),
            source_id=source_id,
        )


@dataclass(frozen=True)
class CodesSuggestedPayload:
    """
    UI payload for code suggestion results.

    Emitted when the AI completes analysis and suggests codes.
    """

    timestamp: datetime
    suggestions: tuple[CodeSuggestionPayload, ...]
    source_id: int
    text_preview: str
    total_count: int
    is_ai_action: bool = True

    @classmethod
    def from_results(
        cls,
        suggestions: list[CodeSuggestionPayload],
        source_id: int,
        text_preview: str,
    ) -> CodesSuggestedPayload:
        """Create payload from suggestion results."""
        return cls(
            timestamp=datetime.now(UTC),
            suggestions=tuple(suggestions),
            source_id=source_id,
            text_preview=text_preview[:200]
            if len(text_preview) > 200
            else text_preview,
            total_count=len(suggestions),
        )


@dataclass(frozen=True)
class SuggestionApprovedPayload:
    """
    UI payload for approved code suggestion.

    Emitted when the researcher approves a suggestion.
    """

    timestamp: datetime
    suggestion_id: str
    original_name: str
    final_name: str
    created_code_id: int
    modified: bool
    is_ai_action: bool = True

    @classmethod
    def from_result(
        cls,
        suggestion_id: str,
        original_name: str,
        final_name: str,
        created_code_id: int,
        modified: bool,
    ) -> SuggestionApprovedPayload:
        """Create payload from approval result."""
        return cls(
            timestamp=datetime.now(UTC),
            suggestion_id=suggestion_id,
            original_name=original_name,
            final_name=final_name,
            created_code_id=created_code_id,
            modified=modified,
        )


@dataclass(frozen=True)
class SuggestionRejectedPayload:
    """
    UI payload for rejected code suggestion.

    Emitted when the researcher rejects a suggestion.
    """

    timestamp: datetime
    suggestion_id: str
    name: str
    reason: str | None
    is_ai_action: bool = True

    @classmethod
    def from_result(
        cls,
        suggestion_id: str,
        name: str,
        reason: str | None,
    ) -> SuggestionRejectedPayload:
        """Create payload from rejection result."""
        return cls(
            timestamp=datetime.now(UTC),
            suggestion_id=suggestion_id,
            name=name,
            reason=reason,
        )


# ============================================================
# Duplicate Detection Payloads
# ============================================================


@dataclass(frozen=True)
class DuplicateCandidatePayload:
    """
    UI payload for a duplicate code candidate.

    Carries duplicate pair data in primitive types.
    """

    code_a_id: int
    code_a_name: str
    code_b_id: int
    code_b_name: str
    similarity: float  # 0.0-1.0
    similarity_percent: int  # 0-100
    rationale: str
    code_a_segment_count: int
    code_b_segment_count: int
    total_segments: int
    status: str  # "pending", "merged", "dismissed"
    timestamp: datetime
    is_ai_action: bool = True

    @classmethod
    def from_candidate(
        cls,
        code_a_id: int,
        code_a_name: str,
        code_b_id: int,
        code_b_name: str,
        similarity: float,
        rationale: str,
        code_a_segment_count: int = 0,
        code_b_segment_count: int = 0,
    ) -> DuplicateCandidatePayload:
        """Create payload from candidate data."""
        return cls(
            code_a_id=code_a_id,
            code_a_name=code_a_name,
            code_b_id=code_b_id,
            code_b_name=code_b_name,
            similarity=similarity,
            similarity_percent=int(similarity * 100),
            rationale=rationale,
            code_a_segment_count=code_a_segment_count,
            code_b_segment_count=code_b_segment_count,
            total_segments=code_a_segment_count + code_b_segment_count,
            status="pending",
            timestamp=datetime.now(UTC),
        )


@dataclass(frozen=True)
class DuplicatesDetectedPayload:
    """
    UI payload for duplicate detection results.

    Emitted when the AI completes duplicate analysis.
    """

    timestamp: datetime
    candidates: tuple[DuplicateCandidatePayload, ...]
    threshold: float
    threshold_percent: int
    codes_analyzed: int
    total_count: int
    is_ai_action: bool = True

    @classmethod
    def from_results(
        cls,
        candidates: list[DuplicateCandidatePayload],
        threshold: float,
        codes_analyzed: int,
    ) -> DuplicatesDetectedPayload:
        """Create payload from detection results."""
        return cls(
            timestamp=datetime.now(UTC),
            candidates=tuple(candidates),
            threshold=threshold,
            threshold_percent=int(threshold * 100),
            codes_analyzed=codes_analyzed,
            total_count=len(candidates),
        )


@dataclass(frozen=True)
class MergeApprovedPayload:
    """
    UI payload for approved merge.

    Emitted when the researcher approves merging two codes.
    """

    timestamp: datetime
    source_code_id: int
    source_code_name: str
    target_code_id: int
    target_code_name: str
    segments_moved: int
    is_ai_action: bool = True

    @classmethod
    def from_result(
        cls,
        source_code_id: int,
        source_code_name: str,
        target_code_id: int,
        target_code_name: str,
        segments_moved: int,
    ) -> MergeApprovedPayload:
        """Create payload from merge result."""
        return cls(
            timestamp=datetime.now(UTC),
            source_code_id=source_code_id,
            source_code_name=source_code_name,
            target_code_id=target_code_id,
            target_code_name=target_code_name,
            segments_moved=segments_moved,
        )


@dataclass(frozen=True)
class MergeDismissedPayload:
    """
    UI payload for dismissed merge suggestion.

    Emitted when the researcher dismisses a merge suggestion.
    """

    timestamp: datetime
    code_a_id: int
    code_b_id: int
    reason: str | None
    is_ai_action: bool = True

    @classmethod
    def from_result(
        cls,
        code_a_id: int,
        code_b_id: int,
        reason: str | None,
    ) -> MergeDismissedPayload:
        """Create payload from dismissal result."""
        return cls(
            timestamp=datetime.now(UTC),
            code_a_id=code_a_id,
            code_b_id=code_b_id,
            reason=reason,
        )


# ============================================================
# Error Payloads
# ============================================================


@dataclass(frozen=True)
class AICodingErrorPayload:
    """
    UI payload for AI coding errors.

    Emitted when an AI operation fails.
    """

    timestamp: datetime
    operation: str  # "suggest_codes", "detect_duplicates", "approve", "reject", "merge"
    error_message: str
    error_code: str | None = None
    is_ai_action: bool = True

    @classmethod
    def from_error(
        cls,
        operation: str,
        error_message: str,
        error_code: str | None = None,
    ) -> AICodingErrorPayload:
        """Create payload from error."""
        return cls(
            timestamp=datetime.now(UTC),
            operation=operation,
            error_message=error_message,
            error_code=error_code,
        )
