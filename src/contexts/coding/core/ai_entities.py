"""
Coding Context: AI-Assisted Coding Entities

Immutable data types for AI-assisted coding features:
- Code suggestions based on text analysis
- Duplicate code detection and merging

These are part of the Coding context, not a separate AI context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from src.contexts.coding.core.entities import Color, TextPosition
from src.shared.common.types import CodeId, SourceId

# ============================================================
# Typed Identifiers
# ============================================================


@dataclass(frozen=True)
class SuggestionId:
    """Unique identifier for a code suggestion."""

    value: str

    @classmethod
    def new(cls) -> SuggestionId:
        """Generate a new unique suggestion ID."""
        return cls(value=f"sug_{uuid4().hex[:12]}")


@dataclass(frozen=True)
class DetectionId:
    """Unique identifier for a duplicate detection run."""

    value: str

    @classmethod
    def new(cls) -> DetectionId:
        """Generate a new unique detection ID."""
        return cls(value=f"det_{uuid4().hex[:12]}")


# ============================================================
# Value Objects
# ============================================================


@dataclass(frozen=True)
class SimilarityScore:
    """
    Semantic similarity score between two codes.

    Value between 0.0 (completely different) and 1.0 (identical).
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"Similarity must be between 0.0 and 1.0, got {self.value}"
            )

    @property
    def is_high(self) -> bool:
        """Check if similarity is above typical duplicate threshold (0.8)."""
        return self.value >= 0.8

    @property
    def percentage(self) -> int:
        """Return similarity as percentage (0-100)."""
        return int(self.value * 100)


@dataclass(frozen=True)
class TextContext:
    """
    Context snippet from source text that led to a suggestion.

    Includes the text and its position for reference.
    """

    text: str
    source_id: SourceId
    position: TextPosition

    @property
    def preview(self) -> str:
        """Return truncated preview of text (max 100 chars)."""
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."


# ============================================================
# Entities
# ============================================================


@dataclass(frozen=True)
class CodeSuggestion:
    """
    An AI-suggested code with rationale.

    Represents a proposed new code that the AI believes
    would be useful based on analysis of uncoded text.
    """

    id: SuggestionId
    name: str
    color: Color
    rationale: str
    contexts: tuple[TextContext, ...] = ()
    confidence: float = 0.0  # 0.0 to 1.0
    memo: str | None = None
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        if self.status not in ("pending", "approved", "rejected"):
            raise ValueError(f"Invalid status: {self.status}")

    def with_status(self, new_status: str) -> CodeSuggestion:
        """Return new CodeSuggestion with updated status."""
        return CodeSuggestion(
            id=self.id,
            name=self.name,
            color=self.color,
            rationale=self.rationale,
            contexts=self.contexts,
            confidence=self.confidence,
            memo=self.memo,
            status=new_status,
            created_at=self.created_at,
        )

    def with_name(self, new_name: str) -> CodeSuggestion:
        """Return new CodeSuggestion with updated name."""
        return CodeSuggestion(
            id=self.id,
            name=new_name,
            color=self.color,
            rationale=self.rationale,
            contexts=self.contexts,
            confidence=self.confidence,
            memo=self.memo,
            status=self.status,
            created_at=self.created_at,
        )

    def with_color(self, new_color: Color) -> CodeSuggestion:
        """Return new CodeSuggestion with updated color."""
        return CodeSuggestion(
            id=self.id,
            name=self.name,
            color=new_color,
            rationale=self.rationale,
            contexts=self.contexts,
            confidence=self.confidence,
            memo=self.memo,
            status=self.status,
            created_at=self.created_at,
        )

    @property
    def is_pending(self) -> bool:
        """Check if suggestion is awaiting review."""
        return self.status == "pending"

    @property
    def confidence_percentage(self) -> int:
        """Return confidence as percentage (0-100)."""
        return int(self.confidence * 100)


@dataclass(frozen=True)
class DuplicateCandidate:
    """
    A pair of codes identified as potential duplicates.

    The AI suggests these codes may be semantically similar
    and could be merged.
    """

    code_a_id: CodeId
    code_a_name: str
    code_b_id: CodeId
    code_b_name: str
    similarity: SimilarityScore
    rationale: str
    code_a_segment_count: int = 0
    code_b_segment_count: int = 0
    status: str = "pending"  # pending, merged, dismissed
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.status not in ("pending", "merged", "dismissed"):
            raise ValueError(f"Invalid status: {self.status}")

    def with_status(self, new_status: str) -> DuplicateCandidate:
        """Return new DuplicateCandidate with updated status."""
        return DuplicateCandidate(
            code_a_id=self.code_a_id,
            code_a_name=self.code_a_name,
            code_b_id=self.code_b_id,
            code_b_name=self.code_b_name,
            similarity=self.similarity,
            rationale=self.rationale,
            code_a_segment_count=self.code_a_segment_count,
            code_b_segment_count=self.code_b_segment_count,
            status=new_status,
            created_at=self.created_at,
        )

    @property
    def is_pending(self) -> bool:
        """Check if candidate is awaiting review."""
        return self.status == "pending"

    @property
    def total_segments(self) -> int:
        """Total segments affected if merged."""
        return self.code_a_segment_count + self.code_b_segment_count


@dataclass(frozen=True)
class DuplicateDetectionResult:
    """
    Result of a duplicate detection run.

    Contains all candidates found above the similarity threshold.
    """

    id: DetectionId
    candidates: tuple[DuplicateCandidate, ...]
    threshold: float
    codes_analyzed: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def candidate_count(self) -> int:
        """Number of duplicate candidates found."""
        return len(self.candidates)

    @property
    def pending_candidates(self) -> tuple[DuplicateCandidate, ...]:
        """Return only pending candidates."""
        return tuple(c for c in self.candidates if c.is_pending)


@dataclass(frozen=True)
class SuggestionBatch:
    """
    A batch of code suggestions from a single analysis.

    Groups related suggestions for efficient review.
    """

    suggestions: tuple[CodeSuggestion, ...]
    source_id: SourceId
    text_analyzed: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def count(self) -> int:
        """Number of suggestions in batch."""
        return len(self.suggestions)

    @property
    def pending_count(self) -> int:
        """Number of pending suggestions."""
        return sum(1 for s in self.suggestions if s.is_pending)

    @property
    def text_preview(self) -> str:
        """Return truncated preview of analyzed text."""
        if len(self.text_analyzed) <= 200:
            return self.text_analyzed
        return self.text_analyzed[:197] + "..."


# ============================================================
# Coding Suggestions (QC-029.07)
# ============================================================


@dataclass(frozen=True)
class CodingSuggestionId:
    """Unique identifier for a coding suggestion."""

    value: str

    @classmethod
    def new(cls) -> CodingSuggestionId:
        """Generate a new unique coding suggestion ID."""
        return cls(value=f"csug_{uuid4().hex[:12]}")


@dataclass(frozen=True)
class CodingSuggestion:
    """
    An AI-suggested code application to a text range.

    Represents a proposed application of an existing code
    to a specific text segment, awaiting researcher approval.
    """

    id: CodingSuggestionId
    source_id: SourceId
    code_id: CodeId
    start_pos: int
    end_pos: int
    rationale: str
    confidence: float = 0.0  # 0.0 to 1.0
    text_excerpt: str | None = None
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        if self.status not in ("pending", "approved", "rejected"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.start_pos < 0:
            raise ValueError(f"start_pos must be >= 0, got {self.start_pos}")
        if self.end_pos <= self.start_pos:
            raise ValueError(
                f"end_pos must be > start_pos, got {self.end_pos} <= {self.start_pos}"
            )

    def with_status(self, new_status: str) -> CodingSuggestion:
        """Return new CodingSuggestion with updated status."""
        return CodingSuggestion(
            id=self.id,
            source_id=self.source_id,
            code_id=self.code_id,
            start_pos=self.start_pos,
            end_pos=self.end_pos,
            rationale=self.rationale,
            confidence=self.confidence,
            text_excerpt=self.text_excerpt,
            status=new_status,
            created_at=self.created_at,
        )

    @property
    def is_pending(self) -> bool:
        """Check if suggestion is awaiting review."""
        return self.status == "pending"

    @property
    def confidence_percentage(self) -> int:
        """Return confidence as percentage (0-100)."""
        return int(self.confidence * 100)


@dataclass(frozen=True)
class CodingSuggestionBatchId:
    """Unique identifier for a batch of coding suggestions."""

    value: str

    @classmethod
    def new(cls) -> CodingSuggestionBatchId:
        """Generate a new unique batch ID."""
        return cls(value=f"cbatch_{uuid4().hex[:12]}")


@dataclass(frozen=True)
class CodingSuggestionBatch:
    """
    A batch of coding suggestions from auto-suggest.

    Groups related coding suggestions for efficient review.
    """

    id: CodingSuggestionBatchId
    source_id: SourceId
    suggestions: tuple[CodingSuggestion, ...]
    status: str = "pending_review"  # pending_review, reviewed, applied
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def count(self) -> int:
        """Number of suggestions in batch."""
        return len(self.suggestions)

    @property
    def pending_count(self) -> int:
        """Number of pending suggestions."""
        return sum(1 for s in self.suggestions if s.is_pending)

    @property
    def reviewed_count(self) -> int:
        """Number of reviewed (approved or rejected) suggestions."""
        return sum(1 for s in self.suggestions if not s.is_pending)


@dataclass(frozen=True)
class MergeSuggestionId:
    """Unique identifier for a merge suggestion."""

    value: str

    @classmethod
    def new(cls) -> MergeSuggestionId:
        """Generate a new unique merge suggestion ID."""
        return cls(value=f"merge_{uuid4().hex[:12]}")


@dataclass(frozen=True)
class MergeSuggestion:
    """
    A suggestion to merge one code into another.

    Represents a proposed merge operation awaiting approval.
    """

    id: MergeSuggestionId
    source_code_id: CodeId
    target_code_id: CodeId
    rationale: str
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.status not in ("pending", "approved", "rejected"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.source_code_id == self.target_code_id:
            raise ValueError("Cannot merge a code into itself")

    def with_status(self, new_status: str) -> MergeSuggestion:
        """Return new MergeSuggestion with updated status."""
        return MergeSuggestion(
            id=self.id,
            source_code_id=self.source_code_id,
            target_code_id=self.target_code_id,
            rationale=self.rationale,
            status=new_status,
            created_at=self.created_at,
        )

    @property
    def is_pending(self) -> bool:
        """Check if suggestion is awaiting review."""
        return self.status == "pending"
