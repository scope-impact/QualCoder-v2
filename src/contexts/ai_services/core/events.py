"""
AI Services Context: Domain Events

Immutable records of AI-assisted coding operations.
These form the CONTRACT (Published Language) between contexts.
"""

from dataclasses import dataclass

from src.contexts.ai_services.core.entities import (
    DetectionId,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)
from src.contexts.coding.core.entities import Color
from src.contexts.shared.core.types import CodeId, DomainEvent, SourceId

# ============================================================
# Code Suggestion Events
# ============================================================


@dataclass(frozen=True)
class CodeSuggested(DomainEvent):
    """Agent proposed a new code based on text analysis."""

    suggestion_id: SuggestionId
    name: str
    color: Color
    rationale: str
    contexts: tuple[TextContext, ...]
    confidence: float
    source_id: SourceId

    @classmethod
    def create(
        cls,
        suggestion_id: SuggestionId,
        name: str,
        color: Color,
        rationale: str,
        contexts: tuple[TextContext, ...],
        confidence: float,
        source_id: SourceId,
    ) -> "CodeSuggested":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            suggestion_id=suggestion_id,
            name=name,
            color=color,
            rationale=rationale,
            contexts=contexts,
            confidence=confidence,
            source_id=source_id,
        )


@dataclass(frozen=True)
class CodeSuggestionApproved(DomainEvent):
    """Researcher accepted an AI code suggestion."""

    suggestion_id: SuggestionId
    created_code_id: CodeId
    original_name: str
    final_name: str
    modified: bool  # True if researcher changed name/color/memo

    @classmethod
    def create(
        cls,
        suggestion_id: SuggestionId,
        created_code_id: CodeId,
        original_name: str,
        final_name: str,
        modified: bool = False,
    ) -> "CodeSuggestionApproved":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            suggestion_id=suggestion_id,
            created_code_id=created_code_id,
            original_name=original_name,
            final_name=final_name,
            modified=modified,
        )


@dataclass(frozen=True)
class CodeSuggestionRejected(DomainEvent):
    """Researcher declined an AI code suggestion."""

    suggestion_id: SuggestionId
    name: str
    reason: str | None = None

    @classmethod
    def create(
        cls,
        suggestion_id: SuggestionId,
        name: str,
        reason: str | None = None,
    ) -> "CodeSuggestionRejected":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            suggestion_id=suggestion_id,
            name=name,
            reason=reason,
        )


# ============================================================
# Duplicate Detection Events
# ============================================================


@dataclass(frozen=True)
class DuplicatesDetected(DomainEvent):
    """Agent found potentially duplicate codes."""

    detection_id: DetectionId
    candidates: tuple[DuplicateCandidate, ...]
    threshold: float
    codes_analyzed: int

    @classmethod
    def create(
        cls,
        detection_id: DetectionId,
        candidates: tuple[DuplicateCandidate, ...],
        threshold: float,
        codes_analyzed: int,
    ) -> "DuplicatesDetected":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            detection_id=detection_id,
            candidates=candidates,
            threshold=threshold,
            codes_analyzed=codes_analyzed,
        )


@dataclass(frozen=True)
class MergeSuggested(DomainEvent):
    """Agent recommended merging two similar codes."""

    source_code_id: CodeId
    source_code_name: str
    target_code_id: CodeId
    target_code_name: str
    similarity: SimilarityScore
    rationale: str

    @classmethod
    def create(
        cls,
        source_code_id: CodeId,
        source_code_name: str,
        target_code_id: CodeId,
        target_code_name: str,
        similarity: SimilarityScore,
        rationale: str,
    ) -> "MergeSuggested":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_code_id=source_code_id,
            source_code_name=source_code_name,
            target_code_id=target_code_id,
            target_code_name=target_code_name,
            similarity=similarity,
            rationale=rationale,
        )


@dataclass(frozen=True)
class MergeSuggestionApproved(DomainEvent):
    """Researcher accepted a merge suggestion."""

    source_code_id: CodeId
    target_code_id: CodeId
    segments_moved: int

    @classmethod
    def create(
        cls,
        source_code_id: CodeId,
        target_code_id: CodeId,
        segments_moved: int,
    ) -> "MergeSuggestionApproved":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_code_id=source_code_id,
            target_code_id=target_code_id,
            segments_moved=segments_moved,
        )


@dataclass(frozen=True)
class MergeSuggestionDismissed(DomainEvent):
    """Researcher dismissed a merge suggestion (not duplicates)."""

    source_code_id: CodeId
    target_code_id: CodeId
    reason: str | None = None

    @classmethod
    def create(
        cls,
        source_code_id: CodeId,
        target_code_id: CodeId,
        reason: str | None = None,
    ) -> "MergeSuggestionDismissed":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_code_id=source_code_id,
            target_code_id=target_code_id,
            reason=reason,
        )


# ============================================================
# Type Aliases (Published Language)
# ============================================================

SuggestionEvent = CodeSuggested | CodeSuggestionApproved | CodeSuggestionRejected

DuplicateEvent = (
    DuplicatesDetected
    | MergeSuggested
    | MergeSuggestionApproved
    | MergeSuggestionDismissed
)

# All events from the AI Services context
AIServiceEvent = SuggestionEvent | DuplicateEvent
