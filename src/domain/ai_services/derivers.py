"""
AI Services Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.
These are the core of the Functional DDD pattern for AI suggestions.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.ai_services.entities import (
    CodeSuggestion,
    DetectionId,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)
from src.domain.ai_services.events import (
    CodeSuggested,
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicatesDetected,
    MergeSuggested,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
)
from src.domain.ai_services.invariants import (
    has_minimum_codes_for_detection,
    has_text_to_analyze,
    is_suggestion_name_unique,
    is_valid_confidence,
    is_valid_rationale,
    is_valid_similarity_threshold,
    is_valid_suggestion_name,
)
from src.domain.coding.entities import Code, Color
from src.domain.shared.types import CodeId, Failure, SourceId

# ============================================================
# State Containers (Input to Derivers)
# ============================================================


@dataclass(frozen=True)
class AISuggestionState:
    """
    State container for AI suggestion derivers.

    Contains all the context needed to validate operations.
    """

    existing_codes: tuple[Code, ...] = ()
    pending_suggestions: tuple[CodeSuggestion, ...] = ()
    pending_duplicates: tuple[DuplicateCandidate, ...] = ()


# ============================================================
# Failure Reasons
# ============================================================


@dataclass(frozen=True)
class InvalidSuggestionName:
    """Suggested code name is invalid."""

    name: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", f"Invalid suggestion name: '{self.name}'")


@dataclass(frozen=True)
class SuggestionNameExists:
    """Suggested code name conflicts with existing code."""

    name: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Code with name '{self.name}' already exists"
        )


@dataclass(frozen=True)
class InvalidConfidence:
    """Confidence value is out of range."""

    confidence: float
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Confidence must be 0.0-1.0, got {self.confidence}"
        )


@dataclass(frozen=True)
class InvalidRationale:
    """Rationale is empty or too long."""

    message: str = "Rationale must be 1-1000 characters"


@dataclass(frozen=True)
class SuggestionNotFound:
    """Code suggestion was not found."""

    suggestion_id: SuggestionId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Suggestion {self.suggestion_id.value} not found"
        )


@dataclass(frozen=True)
class SuggestionNotPending:
    """Suggestion is not in pending status."""

    suggestion_id: SuggestionId
    status: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "message",
            f"Suggestion {self.suggestion_id.value} is {self.status}, not pending",
        )


@dataclass(frozen=True)
class InsufficientCodes:
    """Not enough codes for duplicate detection."""

    count: int
    minimum: int
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Need at least {self.minimum} codes, have {self.count}"
        )


@dataclass(frozen=True)
class InvalidThreshold:
    """Similarity threshold is invalid."""

    threshold: float
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Threshold must be 0.0-1.0, got {self.threshold}"
        )


@dataclass(frozen=True)
class InsufficientText:
    """Not enough text to analyze."""

    length: int
    minimum: int
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "message",
            f"Need at least {self.minimum} characters, have {self.length}",
        )


@dataclass(frozen=True)
class CodeNotFoundForMerge:
    """One of the codes for merge was not found."""

    code_id: CodeId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Code {self.code_id.value} not found for merge"
        )


@dataclass(frozen=True)
class DuplicateNotPending:
    """Duplicate candidate is not in pending status."""

    code_a_id: CodeId
    code_b_id: CodeId
    status: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "message",
            f"Duplicate pair ({self.code_a_id.value}, {self.code_b_id.value}) is {self.status}",
        )


# ============================================================
# Code Suggestion Derivers
# ============================================================


def derive_suggest_code(
    name: str,
    color: Color,
    rationale: str,
    contexts: tuple[TextContext, ...],
    confidence: float,
    source_id: SourceId,
    state: AISuggestionState,
) -> CodeSuggested | Failure:
    """
    Derive a CodeSuggested event or failure.

    Args:
        name: Suggested code name
        color: Suggested color
        rationale: Explanation for the suggestion
        contexts: Text contexts that led to suggestion
        confidence: Confidence score (0.0-1.0)
        source_id: Source being analyzed
        state: Current AI suggestion state

    Returns:
        CodeSuggested event or Failure with reason
    """
    # Validate name
    if not is_valid_suggestion_name(name):
        return Failure(InvalidSuggestionName(name))

    # Check uniqueness against existing codes
    if not is_suggestion_name_unique(name, state.existing_codes):
        return Failure(SuggestionNameExists(name))

    # Validate confidence
    if not is_valid_confidence(confidence):
        return Failure(InvalidConfidence(confidence))

    # Validate rationale
    if not is_valid_rationale(rationale):
        return Failure(InvalidRationale())

    # Generate suggestion ID
    suggestion_id = SuggestionId.new()

    return CodeSuggested.create(
        suggestion_id=suggestion_id,
        name=name,
        color=color,
        rationale=rationale,
        contexts=contexts,
        confidence=confidence,
        source_id=source_id,
    )


def derive_approve_suggestion(
    suggestion_id: SuggestionId,
    final_name: str,
    final_color: Color,
    state: AISuggestionState,
) -> CodeSuggestionApproved | Failure:
    """
    Derive a CodeSuggestionApproved event or failure.

    Args:
        suggestion_id: ID of suggestion to approve
        final_name: Final code name (may be modified from original)
        final_color: Final color (may be modified from original)
        state: Current AI suggestion state

    Returns:
        CodeSuggestionApproved event or Failure with reason
    """
    # Find the suggestion
    suggestion = next(
        (s for s in state.pending_suggestions if s.id == suggestion_id), None
    )
    if suggestion is None:
        return Failure(SuggestionNotFound(suggestion_id))

    # Check status
    if suggestion.status != "pending":
        return Failure(SuggestionNotPending(suggestion_id, suggestion.status))

    # Check final name is unique
    if not is_suggestion_name_unique(final_name, state.existing_codes):
        return Failure(SuggestionNameExists(final_name))

    # Validate final name
    if not is_valid_suggestion_name(final_name):
        return Failure(InvalidSuggestionName(final_name))

    # Determine if modified
    modified = final_name != suggestion.name or final_color != suggestion.color

    # Generate new code ID
    created_code_id = CodeId.new()

    return CodeSuggestionApproved.create(
        suggestion_id=suggestion_id,
        created_code_id=created_code_id,
        original_name=suggestion.name,
        final_name=final_name,
        modified=modified,
    )


def derive_reject_suggestion(
    suggestion_id: SuggestionId,
    reason: str | None,
    state: AISuggestionState,
) -> CodeSuggestionRejected | Failure:
    """
    Derive a CodeSuggestionRejected event or failure.

    Args:
        suggestion_id: ID of suggestion to reject
        reason: Optional rejection reason
        state: Current AI suggestion state

    Returns:
        CodeSuggestionRejected event or Failure with reason
    """
    # Find the suggestion
    suggestion = next(
        (s for s in state.pending_suggestions if s.id == suggestion_id), None
    )
    if suggestion is None:
        return Failure(SuggestionNotFound(suggestion_id))

    # Check status
    if suggestion.status != "pending":
        return Failure(SuggestionNotPending(suggestion_id, suggestion.status))

    return CodeSuggestionRejected.create(
        suggestion_id=suggestion_id,
        name=suggestion.name,
        reason=reason,
    )


# ============================================================
# Duplicate Detection Derivers
# ============================================================


def derive_detect_duplicates(
    candidates: tuple[DuplicateCandidate, ...],
    threshold: float,
    codes_analyzed: int,
    state: AISuggestionState,
) -> DuplicatesDetected | Failure:
    """
    Derive a DuplicatesDetected event or failure.

    Args:
        candidates: Duplicate candidates found
        threshold: Similarity threshold used
        codes_analyzed: Number of codes analyzed
        state: Current AI suggestion state

    Returns:
        DuplicatesDetected event or Failure with reason
    """
    # Validate threshold
    if not is_valid_similarity_threshold(threshold):
        return Failure(InvalidThreshold(threshold))

    # Check minimum codes
    if not has_minimum_codes_for_detection(state.existing_codes):
        count = len(state.existing_codes)
        return Failure(InsufficientCodes(count, 2))

    # Generate detection ID
    detection_id = DetectionId.new()

    return DuplicatesDetected.create(
        detection_id=detection_id,
        candidates=candidates,
        threshold=threshold,
        codes_analyzed=codes_analyzed,
    )


def derive_suggest_merge(
    source_code_id: CodeId,
    target_code_id: CodeId,
    similarity: SimilarityScore,
    rationale: str,
    state: AISuggestionState,
) -> MergeSuggested | Failure:
    """
    Derive a MergeSuggested event or failure.

    Args:
        source_code_id: Code to merge from (will be deleted)
        target_code_id: Code to merge into (will remain)
        similarity: Similarity score between codes
        rationale: Explanation for the merge suggestion
        state: Current AI suggestion state

    Returns:
        MergeSuggested event or Failure with reason
    """
    # Find source code
    source_code = next(
        (c for c in state.existing_codes if c.id == source_code_id), None
    )
    if source_code is None:
        return Failure(CodeNotFoundForMerge(source_code_id))

    # Find target code
    target_code = next(
        (c for c in state.existing_codes if c.id == target_code_id), None
    )
    if target_code is None:
        return Failure(CodeNotFoundForMerge(target_code_id))

    # Validate rationale
    if not is_valid_rationale(rationale):
        return Failure(InvalidRationale())

    return MergeSuggested.create(
        source_code_id=source_code_id,
        source_code_name=source_code.name,
        target_code_id=target_code_id,
        target_code_name=target_code.name,
        similarity=similarity,
        rationale=rationale,
    )


def derive_approve_merge(
    source_code_id: CodeId,
    target_code_id: CodeId,
    segments_to_move: int,
    state: AISuggestionState,
) -> MergeSuggestionApproved | Failure:
    """
    Derive a MergeSuggestionApproved event or failure.

    Args:
        source_code_id: Code to merge from
        target_code_id: Code to merge into
        segments_to_move: Number of segments that will be moved
        state: Current AI suggestion state

    Returns:
        MergeSuggestionApproved event or Failure with reason
    """
    # Candidate doesn't need to exist - user can merge manually
    # Just verify codes exist
    source_code = next(
        (c for c in state.existing_codes if c.id == source_code_id), None
    )
    if source_code is None:
        return Failure(CodeNotFoundForMerge(source_code_id))

    target_code = next(
        (c for c in state.existing_codes if c.id == target_code_id), None
    )
    if target_code is None:
        return Failure(CodeNotFoundForMerge(target_code_id))

    return MergeSuggestionApproved.create(
        source_code_id=source_code_id,
        target_code_id=target_code_id,
        segments_moved=segments_to_move,
    )


def derive_dismiss_merge(
    source_code_id: CodeId,
    target_code_id: CodeId,
    reason: str | None,
    state: AISuggestionState,
) -> MergeSuggestionDismissed | Failure:
    """
    Derive a MergeSuggestionDismissed event or failure.

    Args:
        source_code_id: First code in the pair
        target_code_id: Second code in the pair
        reason: Optional reason for dismissal
        state: Current AI suggestion state

    Returns:
        MergeSuggestionDismissed event or Failure with reason
    """
    # Find the pending duplicate candidate
    candidate = next(
        (
            c
            for c in state.pending_duplicates
            if (c.code_a_id == source_code_id and c.code_b_id == target_code_id)
            or (c.code_a_id == target_code_id and c.code_b_id == source_code_id)
        ),
        None,
    )

    if candidate is None:
        # Not an error - just dismiss anyway
        pass
    elif candidate.status != "pending":
        return Failure(
            DuplicateNotPending(source_code_id, target_code_id, candidate.status)
        )

    return MergeSuggestionDismissed.create(
        source_code_id=source_code_id,
        target_code_id=target_code_id,
        reason=reason,
    )


# ============================================================
# Validation Helpers
# ============================================================


def validate_text_for_analysis(
    text: str,
    min_length: int = 10,
) -> tuple[bool, str]:
    """
    Validate text is suitable for code suggestion analysis.

    Args:
        text: Text to validate
        min_length: Minimum required length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not has_text_to_analyze(text, min_length):
        return False, f"Text must be at least {min_length} characters"
    return True, ""
