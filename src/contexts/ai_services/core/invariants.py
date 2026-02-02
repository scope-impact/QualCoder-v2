"""
AI Services Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate business rules for AI suggestions.
These are composed by Derivers to determine if an operation is valid.

Architecture:
    Invariant: (entity, context) -> bool
    - Pure function, no side effects
    - Returns True if rule is satisfied, False if violated
    - Named with is_* or can_* prefix
"""

from __future__ import annotations

from collections.abc import Iterable
from itertools import islice

from src.contexts.ai_services.core.entities import (
    CodeSuggestion,
    DuplicateCandidate,
    SuggestionId,
)
from src.contexts.coding.core.entities import Code
from src.contexts.shared.core.types import CodeId
from src.contexts.shared.core.validation import is_non_empty_string, is_within_length

# ============================================================
# Code Suggestion Invariants
# ============================================================


def is_valid_suggestion_name(name: str) -> bool:
    """
    Check that a suggested code name is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 100 characters
    """
    return is_non_empty_string(name) and is_within_length(name, 1, 100)


def is_suggestion_name_unique(
    name: str,
    existing_codes: Iterable[Code],
) -> bool:
    """
    Check that a suggested code name doesn't conflict with existing codes.

    Args:
        name: The proposed code name
        existing_codes: All codes in the project

    Returns:
        True if name is unique (case-insensitive)
    """
    return all(code.name.lower() != name.lower() for code in existing_codes)


def is_valid_confidence(confidence: float) -> bool:
    """
    Check that confidence value is valid.

    Rules:
    - Must be between 0.0 and 1.0
    """
    return 0.0 <= confidence <= 1.0


def is_valid_rationale(rationale: str) -> bool:
    """
    Check that rationale is valid.

    Rules:
    - Not empty or whitespace-only
    - Between 1 and 1000 characters
    """
    return is_non_empty_string(rationale) and is_within_length(rationale, 1, 1000)


def can_suggestion_be_approved(
    suggestion: CodeSuggestion,
    existing_codes: Iterable[Code],
) -> bool:
    """
    Check if a suggestion can be approved.

    Args:
        suggestion: The suggestion to approve
        existing_codes: All codes in the project

    Returns:
        True if suggestion can be approved
    """
    if suggestion.status != "pending":
        return False

    # Check name is still unique (may have changed since suggestion)
    return is_suggestion_name_unique(suggestion.name, existing_codes)


def does_suggestion_exist(
    suggestion_id: SuggestionId,
    suggestions: Iterable[CodeSuggestion],
) -> bool:
    """Check if a suggestion exists."""
    return any(s.id == suggestion_id for s in suggestions)


# ============================================================
# Duplicate Detection Invariants
# ============================================================


def is_valid_similarity_threshold(threshold: float) -> bool:
    """
    Check that similarity threshold is valid.

    Rules:
    - Must be between 0.0 and 1.0
    - Typically 0.7-0.9 for useful duplicate detection
    """
    return 0.0 <= threshold <= 1.0


def is_similarity_above_threshold(
    similarity: float,
    threshold: float,
) -> bool:
    """
    Check if similarity exceeds the threshold.

    Args:
        similarity: The calculated similarity score
        threshold: The minimum threshold for duplicates

    Returns:
        True if similarity >= threshold
    """
    return similarity >= threshold


def can_codes_be_compared(
    code_a: Code,
    code_b: Code,
) -> bool:
    """
    Check if two codes can be compared for similarity.

    Rules:
    - Codes must be different
    - Both must have valid names

    Args:
        code_a: First code
        code_b: Second code

    Returns:
        True if comparison is valid
    """
    if code_a.id == code_b.id:
        return False

    return is_valid_suggestion_name(code_a.name) and is_valid_suggestion_name(
        code_b.name
    )


def can_merge_be_approved(
    candidate: DuplicateCandidate,
    code_exists_fn: callable,
) -> bool:
    """
    Check if a merge suggestion can be approved.

    Args:
        candidate: The duplicate candidate
        code_exists_fn: Function to check if a code exists

    Returns:
        True if merge can proceed
    """
    if candidate.status != "pending":
        return False

    # Both codes must still exist
    return code_exists_fn(candidate.code_a_id) and code_exists_fn(candidate.code_b_id)


def is_duplicate_pair_unique(
    code_a_id: CodeId,
    code_b_id: CodeId,
    existing_candidates: Iterable[DuplicateCandidate],
) -> bool:
    """
    Check that a duplicate pair hasn't already been detected.

    Args:
        code_a_id: First code ID
        code_b_id: Second code ID
        existing_candidates: Already detected candidates

    Returns:
        True if this pair hasn't been detected before
    """
    for candidate in existing_candidates:
        # Check both orderings
        if candidate.code_a_id == code_a_id and candidate.code_b_id == code_b_id:
            return False
        if candidate.code_a_id == code_b_id and candidate.code_b_id == code_a_id:
            return False
    return True


# ============================================================
# Cross-Entity Invariants
# ============================================================


def has_minimum_codes_for_detection(
    codes: Iterable[Code],
    minimum: int = 2,
) -> bool:
    """
    Check if there are enough codes for duplicate detection.

    Args:
        codes: All codes in the project
        minimum: Minimum number of codes required

    Returns:
        True if enough codes exist
    """
    # Count up to minimum items without consuming entire iterable
    count = sum(1 for _ in islice(codes, minimum))
    return count >= minimum


def has_text_to_analyze(
    text: str,
    min_length: int = 10,
) -> bool:
    """
    Check if there's enough text to analyze for code suggestions.

    Args:
        text: The text to analyze
        min_length: Minimum required text length

    Returns:
        True if text is long enough
    """
    return len(text.strip()) >= min_length
