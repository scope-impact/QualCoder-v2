"""
Coding Context: AI Invariant Tests

Tests for pure predicate functions that validate business rules for AI-assisted coding.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]


# ============================================================
# Code Suggestion Invariant Tests
# ============================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestIsValidSuggestionName:
    """Tests for is_valid_suggestion_name invariant."""

    @allure.title("is_valid_suggestion_name validates name format and length")
    @pytest.mark.parametrize("value, expected", [
        ("Theme", True),
        ("Emerging-Pattern", True),
        ("Code_With_Numbers_123", True),
        ("", False),
        ("   ", False),
        ("\t\n", False),
        ("a" * 101, False),
        ("a" * 100, True),
        ("A", True),
    ])
    def test_is_valid_suggestion_name(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_suggestion_name

        assert is_valid_suggestion_name(value) is expected


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestIsSuggestionNameUnique:
    """Tests for is_suggestion_name_unique invariant."""

    @allure.title("is_suggestion_name_unique detects case-insensitive duplicates")
    def test_uniqueness_checks(self):
        """Checks empty list, case-insensitive duplicates, and multiple codes."""
        from src.contexts.coding.core.ai_invariants import is_suggestion_name_unique
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        # Any name is unique in a project with no codes
        assert is_suggestion_name_unique("Theme", []) is True

        # Case-insensitive duplicate detection
        existing = [Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))]
        assert is_suggestion_name_unique("Theme", existing) is False
        assert is_suggestion_name_unique("theme", existing) is False
        assert is_suggestion_name_unique("THEME", existing) is False
        assert is_suggestion_name_unique("Different", existing) is True

        # Check against all existing codes
        existing = [
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
            Code(id=CodeId(value="3"), name="Category", color=Color(0, 0, 255)),
        ]
        assert is_suggestion_name_unique("Theme", existing) is False
        assert is_suggestion_name_unique("Pattern", existing) is False
        assert is_suggestion_name_unique("Category", existing) is False
        assert is_suggestion_name_unique("NewCode", existing) is True


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestIsValidConfidenceAndRationale:
    """Tests for is_valid_confidence and is_valid_rationale invariants."""

    @allure.title("is_valid_confidence validates 0.0-1.0 range")
    @pytest.mark.parametrize("value, expected", [
        (0.0, True),
        (1.0, True),
        (0.5, True),
        (0.75, True),
        (0.99, True),
        (-0.1, False),
        (-1.0, False),
        (1.1, False),
        (2.0, False),
    ])
    def test_is_valid_confidence(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(value) is expected

    @allure.title("is_valid_rationale validates non-empty text within length bounds")
    @pytest.mark.parametrize("value, expected", [
        ("This code represents a recurring theme.", True),
        ("", False),
        ("   ", False),
        ("\t\n", False),
        ("a" * 1001, False),
        ("a" * 1000, True),
        ("X", True),
    ])
    def test_is_valid_rationale(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale(value) is expected


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCanSuggestionBeApproved:
    """Tests for can_suggestion_be_approved invariant."""

    @allure.title("Approval depends on pending status and unique name")
    def test_approval_and_rejection_cases(self):
        """Pending + unique name = approved; non-pending or duplicate = rejected."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import can_suggestion_be_approved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        # Can approve: pending + unique name
        suggestion = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )
        assert can_suggestion_be_approved(suggestion, []) is True

        # Cannot approve: already approved
        suggestion_approved = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="approved",
        )
        assert can_suggestion_be_approved(suggestion_approved, []) is False

        # Cannot approve: rejected
        suggestion_rejected = CodeSuggestion(
            id=SuggestionId.new(),
            name="NewCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="rejected",
        )
        assert can_suggestion_be_approved(suggestion_rejected, []) is False

        # Cannot approve: duplicate name (exact + case-insensitive)
        existing = [
            Code(id=CodeId(value="1"), name="ExistingCode", color=Color(0, 255, 0))
        ]
        suggestion_dup = CodeSuggestion(
            id=SuggestionId.new(),
            name="ExistingCode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )
        assert can_suggestion_be_approved(suggestion_dup, existing) is False

        suggestion_ci = CodeSuggestion(
            id=SuggestionId.new(),
            name="existingcode",
            color=Color(255, 0, 0),
            rationale="Test rationale",
            status="pending",
        )
        assert can_suggestion_be_approved(suggestion_ci, existing) is False


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestDoesSuggestionExist:
    """Tests for does_suggestion_exist invariant."""

    @allure.title("does_suggestion_exist finds suggestion by ID in list")
    def test_suggestion_existence(self):
        """Checks existing, missing, and multi-suggestion scenarios."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import does_suggestion_exist
        from src.contexts.coding.core.entities import Color

        # Missing in empty list
        assert does_suggestion_exist(SuggestionId.new(), []) is False

        # Found in single-element list
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

        # Found among multiple suggestions
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


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestSimilarityInvariants:
    """Tests for is_valid_similarity_threshold and is_similarity_above_threshold."""

    @allure.title("is_valid_similarity_threshold validates 0.0-1.0 range")
    @pytest.mark.parametrize("value, expected", [
        (0.0, True),
        (1.0, True),
        (0.7, True),
        (0.8, True),
        (0.9, True),
        (-0.1, False),
        (-1.0, False),
        (1.1, False),
        (2.0, False),
    ])
    def test_is_valid_similarity_threshold(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(value) is expected

    @allure.title("is_similarity_above_threshold compares score against threshold")
    @pytest.mark.parametrize("similarity, threshold, expected", [
        (0.9, 0.8, True),
        (1.0, 0.5, True),
        (0.8, 0.8, True),
        (0.0, 0.0, True),
        (0.7, 0.8, False),
        (0.0, 0.5, False),
    ])
    def test_is_similarity_above_threshold(self, similarity, threshold, expected):
        from src.contexts.coding.core.ai_invariants import is_similarity_above_threshold

        assert is_similarity_above_threshold(similarity, threshold) is expected


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestCanCodesBeCompared:
    """Tests for can_codes_be_compared invariant."""

    @allure.title("Valid comparison, self-comparison, and invalid names")
    def test_comparison_scenarios(self):
        """Two different codes with valid names can be compared; self/invalid cannot."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0))
        assert can_codes_be_compared(code_a, code_b) is True

        # Cannot compare with self
        assert can_codes_be_compared(code_a, code_a) is False

        # Invalid names
        code_empty = Code(id=CodeId(value="1"), name="", color=Color(255, 0, 0))
        assert can_codes_be_compared(code_empty, code_b) is False

        code_ws = Code(id=CodeId(value="2"), name="   ", color=Color(0, 255, 0))
        assert can_codes_be_compared(code_a, code_ws) is False

        code_long = Code(id=CodeId(value="1"), name="a" * 101, color=Color(255, 0, 0))
        assert can_codes_be_compared(code_long, code_b) is False


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestCanMergeBeApproved:
    """Tests for can_merge_be_approved invariant."""

    @allure.title("Merge approval depends on pending status and code existence")
    def test_approval_and_rejection(self):
        """Pending + both codes exist = approved; non-pending or missing codes = rejected."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        # Can approve: pending + both codes exist
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Theme",
            code_b_id=CodeId(value="2"),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="pending",
        )
        assert can_merge_be_approved(candidate, lambda cid: cid.value in ("1", "2")) is True

        # Cannot: already merged
        candidate_merged = DuplicateCandidate(
            code_a_id=CodeId(value="1"), code_a_name="Theme",
            code_b_id=CodeId(value="2"), code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9), rationale="Similar concepts",
            status="merged",
        )
        assert can_merge_be_approved(candidate_merged, lambda _: True) is False

        # Cannot: dismissed
        candidate_dismissed = DuplicateCandidate(
            code_a_id=CodeId(value="1"), code_a_name="Theme",
            code_b_id=CodeId(value="2"), code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9), rationale="Similar concepts",
            status="dismissed",
        )
        assert can_merge_be_approved(candidate_dismissed, lambda _: True) is False

        # Cannot: code A or B missing
        assert can_merge_be_approved(candidate, lambda cid: cid.value == "2") is False
        assert can_merge_be_approved(candidate, lambda cid: cid.value == "1") is False


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestIsDuplicatePairUnique:
    """Tests for is_duplicate_pair_unique invariant."""

    @allure.title("Unique pairs accepted; existing and reversed pairs rejected")
    def test_unique_and_duplicate_pairs(self):
        """Empty list, different pair, partial overlap are unique; exact/reversed are not."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import is_duplicate_pair_unique
        from src.shared import CodeId

        # Any pair is unique with no existing candidates
        assert is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="2"), []) is True

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value="1"), code_a_name="Theme",
                code_b_id=CodeId(value="2"), code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9), rationale="Similar",
            )
        ]

        # Different pair and partial overlap are unique
        assert is_duplicate_pair_unique(CodeId(value="3"), CodeId(value="4"), existing) is True
        assert is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="3"), existing) is True

        # Exact pair and reversed pair are duplicates
        assert is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="2"), existing) is False
        assert is_duplicate_pair_unique(CodeId(value="2"), CodeId(value="1"), existing) is False


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestHasMinimumCodesForDetection:
    """Tests for has_minimum_codes_for_detection invariant."""

    @allure.title("Checks code count against minimum, custom minimum, and generators")
    @pytest.mark.parametrize("count, expected", [
        (0, False),
        (1, False),
        (2, True),
        (10, True),
    ])
    def test_minimum_codes_by_count(self, count, expected):
        """Checks various code list sizes against default minimum."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [
            Code(id=CodeId(value=i), name=f"Code{i}", color=Color(i, i, i))
            for i in range(count)
        ]
        assert has_minimum_codes_for_detection(codes) is expected

    @allure.title("Custom minimum and generator support")
    def test_custom_minimum_and_generator(self):
        """Respects custom minimum parameter and works with generators."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = [
            Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
            Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
        ]
        assert has_minimum_codes_for_detection(codes, minimum=2) is True
        assert has_minimum_codes_for_detection(codes, minimum=3) is False

        def code_generator():
            for i in range(5):
                yield Code(id=CodeId(value=i), name=f"Code{i}", color=Color(i, i, i))

        assert has_minimum_codes_for_detection(code_generator()) is True


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestHasTextToAnalyze:
    """Tests for has_text_to_analyze invariant."""

    @allure.title("has_text_to_analyze validates text length after trimming")
    @pytest.mark.parametrize("text, kwargs, expected", [
        ("", {}, False),
        ("   ", {}, False),
        ("\t\n", {}, False),
        ("short", {}, False),
        ("abcdefghi", {}, False),
        ("0123456789", {}, True),
        ("This is a longer text for analysis.", {}, True),
        ("  short  ", {}, False),
        ("  0123456789  ", {}, True),
        ("abc", {"min_length": 3}, True),
        ("ab", {"min_length": 3}, False),
        ("This is sample text", {"min_length": 20}, False),
        ("This is sample text!", {"min_length": 20}, True),
    ])
    def test_has_text_to_analyze(self, text, kwargs, expected):
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze(text, **kwargs) is expected
