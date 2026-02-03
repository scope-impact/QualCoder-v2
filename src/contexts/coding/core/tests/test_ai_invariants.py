"""
Coding Context: AI Invariant Tests

Tests for pure predicate functions that validate business rules for AI-assisted coding.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ============================================================
# Code Suggestion Invariant Tests
# ============================================================


class TestIsValidSuggestionName:
    """Tests for is_valid_suggestion_name invariant."""

    def test_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        assert is_valid_suggestion_name("Theme") is True
        assert is_valid_suggestion_name("Emerging-Pattern") is True
        assert is_valid_suggestion_name("Code_With_Numbers_123") is True

    def test_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        assert is_valid_suggestion_name("") is False

    def test_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        assert is_valid_suggestion_name("   ") is False
        assert is_valid_suggestion_name("\t\n") is False

    def test_rejects_too_long(self):
        """Names exceeding 100 characters should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        long_name = "a" * 101
        assert is_valid_suggestion_name(long_name) is False

    def test_accepts_max_length(self):
        """Names at exactly 100 characters should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        max_name = "a" * 100
        assert is_valid_suggestion_name(max_name) is True

    def test_accepts_single_character(self):
        """Single character name should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        assert is_valid_suggestion_name("A") is True


class TestIsSuggestionNameUnique:
    """Tests for is_suggestion_name_unique invariant."""

    def test_unique_in_empty_project(self):
        """Any name is unique in a project with no codes."""
        from src.contexts.coding.core.ai_invariants import is_suggestion_name_unique

        assert is_suggestion_name_unique("Theme", []) is True

    def test_detects_duplicate(self):
        """Duplicate names should be detected (case-insensitive)."""
        from src.contexts.coding.core.ai_invariants import is_suggestion_name_unique
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        existing = [Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))]

        assert is_suggestion_name_unique("Theme", existing) is False
        assert is_suggestion_name_unique("theme", existing) is False
        assert is_suggestion_name_unique("THEME", existing) is False
        assert is_suggestion_name_unique("Different", existing) is True

    def test_unique_with_multiple_codes(self):
        """Should check against all existing codes."""
        from src.contexts.coding.core.ai_invariants import is_suggestion_name_unique
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        existing = [
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0)),
            Code(id=CodeId(value=3), name="Category", color=Color(0, 0, 255)),
        ]

        assert is_suggestion_name_unique("Theme", existing) is False
        assert is_suggestion_name_unique("Pattern", existing) is False
        assert is_suggestion_name_unique("Category", existing) is False
        assert is_suggestion_name_unique("NewCode", existing) is True


class TestIsValidConfidence:
    """Tests for is_valid_confidence invariant."""

    def test_accepts_zero(self):
        """Zero confidence should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(0.0) is True

    def test_accepts_one(self):
        """Maximum confidence (1.0) should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(1.0) is True

    def test_accepts_mid_range(self):
        """Mid-range confidence values should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(0.5) is True
        assert is_valid_confidence(0.75) is True
        assert is_valid_confidence(0.99) is True

    def test_rejects_negative(self):
        """Negative confidence should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(-0.1) is False
        assert is_valid_confidence(-1.0) is False

    def test_rejects_above_one(self):
        """Confidence above 1.0 should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(1.1) is False
        assert is_valid_confidence(2.0) is False


class TestIsValidRationale:
    """Tests for is_valid_rationale invariant."""

    def test_accepts_normal_string(self):
        """Normal rationale text should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale("This code represents a recurring theme.") is True

    def test_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale("") is False

    def test_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale("   ") is False
        assert is_valid_rationale("\t\n") is False

    def test_rejects_too_long(self):
        """Rationale exceeding 1000 characters should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        long_rationale = "a" * 1001
        assert is_valid_rationale(long_rationale) is False

    def test_accepts_max_length(self):
        """Rationale at exactly 1000 characters should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        max_rationale = "a" * 1000
        assert is_valid_rationale(max_rationale) is True

    def test_accepts_single_character(self):
        """Single character rationale should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale("X") is True


class TestCanSuggestionBeApproved:
    """Tests for can_suggestion_be_approved invariant."""

    def test_allows_approval_of_pending_with_unique_name(self):
        """Pending suggestion with unique name can be approved."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Color

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )

        assert can_suggestion_be_approved(suggestion, []) is True

    def test_prevents_approval_of_approved(self):
        """Already approved suggestions cannot be approved again."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Color

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="approved",
        )

        assert can_suggestion_be_approved(suggestion, []) is False

    def test_prevents_approval_of_rejected(self):
        """Rejected suggestions cannot be approved."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Color

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="rejected",
        )

        assert can_suggestion_be_approved(suggestion, []) is False

    def test_prevents_approval_with_duplicate_name(self):
        """Pending suggestion with duplicate name cannot be approved."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="ExistingCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )

        existing = [
            Code(id=CodeId(value=1), name="ExistingCode", color=Color(0, 255, 0))
        ]

        assert can_suggestion_be_approved(suggestion, existing) is False

    def test_prevents_approval_with_case_insensitive_duplicate(self):
        """Name uniqueness check is case-insensitive."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="existingcode",  # lowercase
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )

        existing = [
            Code(id=CodeId(value=1), name="ExistingCode", color=Color(0, 255, 0))
        ]

        assert can_suggestion_be_approved(suggestion, existing) is False


class TestDoesSuggestionExist:
    """Tests for does_suggestion_exist invariant."""

    def test_finds_existing_suggestion(self):
        """Should find suggestion that exists."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import does_suggestion_exist
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId.new()
        suggestions = [
            CodeSuggestion(
                id=suggestion_id,
                name="Theme",
                color=Color(255, 0, 0),
                rationale="Test rationale",
            )
        ]

        assert does_suggestion_exist(suggestion_id, suggestions) is True

    def test_returns_false_for_missing_suggestion(self):
        """Should return False for non-existent suggestion."""
        from src.contexts.coding.core.ai_entities import SuggestionId
        from src.contexts.coding.core.ai_invariants import does_suggestion_exist

        assert does_suggestion_exist(SuggestionId.new(), []) is False

    def test_finds_suggestion_in_multiple(self):
        """Should find suggestion among multiple suggestions."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import does_suggestion_exist
        from src.contexts.coding.core.entities import Color

        target_id = SuggestionId.new()
        suggestions = [
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Theme1",
                color=Color(255, 0, 0),
                rationale="Test 1",
            ),
            CodeSuggestion(
                id=target_id,
                name="Theme2",
                color=Color(0, 255, 0),
                rationale="Test 2",
            ),
            CodeSuggestion(
                id=SuggestionId.new(),
                name="Theme3",
                color=Color(0, 0, 255),
                rationale="Test 3",
            ),
        ]

        assert does_suggestion_exist(target_id, suggestions) is True


# ============================================================
# Duplicate Detection Invariant Tests
# ============================================================


class TestIsValidSimilarityThreshold:
    """Tests for is_valid_similarity_threshold invariant."""

    def test_accepts_zero(self):
        """Zero threshold should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(0.0) is True

    def test_accepts_one(self):
        """Maximum threshold (1.0) should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(1.0) is True

    def test_accepts_typical_thresholds(self):
        """Typical duplicate detection thresholds should be valid."""
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(0.7) is True
        assert is_valid_similarity_threshold(0.8) is True
        assert is_valid_similarity_threshold(0.9) is True

    def test_rejects_negative(self):
        """Negative threshold should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(-0.1) is False
        assert is_valid_similarity_threshold(-1.0) is False

    def test_rejects_above_one(self):
        """Threshold above 1.0 should be invalid."""
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(1.1) is False
        assert is_valid_similarity_threshold(2.0) is False


class TestIsSimilarityAboveThreshold:
    """Tests for is_similarity_above_threshold invariant."""

    def test_above_threshold(self):
        """Similarity above threshold should return True."""
        from src.contexts.coding.core.ai_invariants import is_similarity_above_threshold

        assert is_similarity_above_threshold(0.9, 0.8) is True
        assert is_similarity_above_threshold(1.0, 0.5) is True

    def test_equal_to_threshold(self):
        """Similarity equal to threshold should return True."""
        from src.contexts.coding.core.ai_invariants import is_similarity_above_threshold

        assert is_similarity_above_threshold(0.8, 0.8) is True
        assert is_similarity_above_threshold(0.0, 0.0) is True

    def test_below_threshold(self):
        """Similarity below threshold should return False."""
        from src.contexts.coding.core.ai_invariants import is_similarity_above_threshold

        assert is_similarity_above_threshold(0.7, 0.8) is False
        assert is_similarity_above_threshold(0.0, 0.5) is False


class TestCanCodesBeCompared:
    """Tests for can_codes_be_compared invariant."""

    def test_allows_comparison_of_different_codes(self):
        """Two different codes can be compared."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))

        assert can_codes_be_compared(code_a, code_b) is True

    def test_prevents_comparison_with_self(self):
        """Cannot compare a code with itself."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))

        assert can_codes_be_compared(code, code) is False

    def test_prevents_comparison_with_invalid_name_a(self):
        """Cannot compare if first code has invalid name."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value=1), name="", color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))

        assert can_codes_be_compared(code_a, code_b) is False

    def test_prevents_comparison_with_invalid_name_b(self):
        """Cannot compare if second code has invalid name."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value=2), name="   ", color=Color(0, 255, 0))

        assert can_codes_be_compared(code_a, code_b) is False

    def test_prevents_comparison_with_too_long_name(self):
        """Cannot compare if code has name exceeding max length."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value=1), name="a" * 101, color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))

        assert can_codes_be_compared(code_a, code_b) is False


class TestCanMergeBeApproved:
    """Tests for can_merge_be_approved invariant."""

    def test_allows_merge_when_both_codes_exist(self):
        """Pending merge with both codes existing can be approved."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Theme",
            code_b_id=CodeId(value=2),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="pending",
        )

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value in (1, 2)

        assert can_merge_be_approved(candidate, code_exists) is True

    def test_prevents_merge_when_status_is_merged(self):
        """Already merged candidates cannot be approved again."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Theme",
            code_b_id=CodeId(value=2),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="merged",
        )

        def code_exists(code_id: CodeId) -> bool:
            return True

        assert can_merge_be_approved(candidate, code_exists) is False

    def test_prevents_merge_when_status_is_dismissed(self):
        """Dismissed candidates cannot be approved."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Theme",
            code_b_id=CodeId(value=2),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="dismissed",
        )

        def code_exists(code_id: CodeId) -> bool:
            return True

        assert can_merge_be_approved(candidate, code_exists) is False

    def test_prevents_merge_when_code_a_missing(self):
        """Cannot merge if first code doesn't exist."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Theme",
            code_b_id=CodeId(value=2),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="pending",
        )

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value == 2  # Only code B exists

        assert can_merge_be_approved(candidate, code_exists) is False

    def test_prevents_merge_when_code_b_missing(self):
        """Cannot merge if second code doesn't exist."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Theme",
            code_b_id=CodeId(value=2),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="pending",
        )

        def code_exists(code_id: CodeId) -> bool:
            return code_id.value == 1  # Only code A exists

        assert can_merge_be_approved(candidate, code_exists) is False


class TestIsDuplicatePairUnique:
    """Tests for is_duplicate_pair_unique invariant."""

    def test_unique_in_empty_list(self):
        """Any pair is unique with no existing candidates."""
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        assert is_duplicate_pair_unique(CodeId(value=1), CodeId(value=2), []) is True

    def test_detects_existing_pair(self):
        """Should detect pair that already exists."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value=1),
                code_a_name="Theme",
                code_b_id=CodeId(value=2),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
            )
        ]

        assert (
            is_duplicate_pair_unique(CodeId(value=1), CodeId(value=2), existing)
            is False
        )

    def test_detects_reverse_pair(self):
        """Should detect pair with reversed order."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value=1),
                code_a_name="Theme",
                code_b_id=CodeId(value=2),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
            )
        ]

        # Check reverse order (2, 1) should also be detected as duplicate
        assert (
            is_duplicate_pair_unique(CodeId(value=2), CodeId(value=1), existing)
            is False
        )

    def test_unique_different_pair(self):
        """Different pair should be unique."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value=1),
                code_a_name="Theme",
                code_b_id=CodeId(value=2),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
            )
        ]

        # Different pair (3, 4) should be unique
        assert (
            is_duplicate_pair_unique(CodeId(value=3), CodeId(value=4), existing) is True
        )

    def test_unique_partially_different_pair(self):
        """Pair sharing one code should be unique."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value=1),
                code_a_name="Theme",
                code_b_id=CodeId(value=2),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
            )
        ]

        # Pair (1, 3) shares one code but is a different pair
        assert (
            is_duplicate_pair_unique(CodeId(value=1), CodeId(value=3), existing) is True
        )


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


class TestHasMinimumCodesForDetection:
    """Tests for has_minimum_codes_for_detection invariant."""

    def test_returns_false_for_empty(self):
        """Empty list doesn't have enough codes."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )

        assert has_minimum_codes_for_detection([]) is False

    def test_returns_false_for_single_code(self):
        """Single code isn't enough for duplicate detection."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))]

        assert has_minimum_codes_for_detection(codes) is False

    def test_returns_true_for_two_codes(self):
        """Two codes is minimum for duplicate detection."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0)),
        ]

        assert has_minimum_codes_for_detection(codes) is True

    def test_returns_true_for_many_codes(self):
        """Many codes should satisfy minimum."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [
            Code(id=CodeId(value=i), name=f"Code{i}", color=Color(i, i, i))
            for i in range(10)
        ]

        assert has_minimum_codes_for_detection(codes) is True

    def test_custom_minimum(self):
        """Should respect custom minimum parameter."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [
            Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0)),
        ]

        # Default minimum (2) is satisfied
        assert has_minimum_codes_for_detection(codes, minimum=2) is True
        # Higher minimum (3) is not satisfied
        assert has_minimum_codes_for_detection(codes, minimum=3) is False

    def test_works_with_generator(self):
        """Should work with generator/iterator."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        def code_generator():
            for i in range(5):
                yield Code(id=CodeId(value=i), name=f"Code{i}", color=Color(i, i, i))

        # Generator should work without consuming entire iterable
        assert has_minimum_codes_for_detection(code_generator()) is True


class TestHasTextToAnalyze:
    """Tests for has_text_to_analyze invariant."""

    def test_returns_false_for_empty(self):
        """Empty text doesn't have enough to analyze."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("") is False

    def test_returns_false_for_whitespace(self):
        """Whitespace-only text doesn't have enough to analyze."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("   ") is False
        assert has_text_to_analyze("\t\n") is False

    def test_returns_false_for_short_text(self):
        """Text shorter than minimum isn't enough."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("short") is False  # 5 chars
        assert has_text_to_analyze("abcdefghi") is False  # 9 chars

    def test_returns_true_for_exact_minimum(self):
        """Text at exactly minimum length is enough."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("0123456789") is True  # 10 chars

    def test_returns_true_for_long_text(self):
        """Long text is enough to analyze."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("This is a longer text for analysis.") is True

    def test_strips_whitespace_before_check(self):
        """Whitespace is stripped before length check."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        # "  short  " has 5 chars after strip, which is < 10
        assert has_text_to_analyze("  short  ") is False
        # "  0123456789  " has 10 chars after strip
        assert has_text_to_analyze("  0123456789  ") is True

    def test_custom_minimum(self):
        """Should respect custom minimum parameter."""
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze("abc", min_length=3) is True
        assert has_text_to_analyze("ab", min_length=3) is False
        assert has_text_to_analyze("This is sample text", min_length=20) is False
        assert has_text_to_analyze("This is sample text!", min_length=20) is True
