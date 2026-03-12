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
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Theme", True),
            ("Emerging-Pattern", True),
            ("Code_With_Numbers_123", True),
            ("", False),
            ("   ", False),
            ("\t\n", False),
            ("a" * 101, False),
            ("a" * 100, True),
            ("A", True),
        ],
    )
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
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0.0, True),
            (1.0, True),
            (0.5, True),
            (0.75, True),
            (0.99, True),
            (-0.1, False),
            (-1.0, False),
            (1.1, False),
            (2.0, False),
        ],
    )
    def test_is_valid_confidence(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_confidence

        assert is_valid_confidence(value) is expected

    @allure.title("is_valid_rationale validates non-empty text within length bounds")
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("This code represents a recurring theme.", True),
            ("", False),
            ("   ", False),
            ("\t\n", False),
            ("a" * 1001, False),
            ("a" * 1000, True),
            ("X", True),
        ],
    )
    def test_is_valid_rationale(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_rationale

        assert is_valid_rationale(value) is expected


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestSuggestionApprovalAndExistence:
    """Tests for can_suggestion_be_approved and does_suggestion_exist invariants."""

    @allure.title("Approval depends on pending status, unique name; existence by ID")
    def test_approval_rejection_and_existence(self):
        """Pending + unique = approved; non-pending/duplicate = rejected; existence by ID."""
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_invariants import (
            can_suggestion_be_approved,
            does_suggestion_exist,
        )
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

        # Cannot approve: already approved / rejected
        for status in ("approved", "rejected"):
            s = CodeSuggestion(
                id=SuggestionId.new(),
                name="NewCode",
                color=Color(255, 0, 0),
                rationale="Test rationale",
                status=status,
            )
            assert can_suggestion_be_approved(s, []) is False

        # Cannot approve: duplicate name (exact + case-insensitive)
        existing = [
            Code(id=CodeId(value="1"), name="ExistingCode", color=Color(0, 255, 0))
        ]
        for name in ("ExistingCode", "existingcode"):
            s = CodeSuggestion(
                id=SuggestionId.new(),
                name=name,
                color=Color(255, 0, 0),
                rationale="Test rationale",
                status="pending",
            )
            assert can_suggestion_be_approved(s, existing) is False

        # does_suggestion_exist: missing in empty, found in single and multi-element lists
        assert does_suggestion_exist(SuggestionId.new(), []) is False

        suggestion_id = SuggestionId.new()
        suggestions = [
            CodeSuggestion(
                id=suggestion_id, name="Theme", color=Color(255, 0, 0), rationale="Test"
            ),
        ]
        assert does_suggestion_exist(suggestion_id, suggestions) is True

        target_id = SuggestionId.new()
        suggestions = [
            CodeSuggestion(
                id=SuggestionId.new(), name="T1", color=Color(255, 0, 0), rationale="R1"
            ),
            CodeSuggestion(
                id=target_id, name="T2", color=Color(0, 255, 0), rationale="R2"
            ),
            CodeSuggestion(
                id=SuggestionId.new(), name="T3", color=Color(0, 0, 255), rationale="R3"
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
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0.0, True),
            (1.0, True),
            (0.7, True),
            (0.8, True),
            (0.9, True),
            (-0.1, False),
            (-1.0, False),
            (1.1, False),
            (2.0, False),
        ],
    )
    def test_is_valid_similarity_threshold(self, value, expected):
        from src.contexts.coding.core.ai_invariants import is_valid_similarity_threshold

        assert is_valid_similarity_threshold(value) is expected

    @allure.title("is_similarity_above_threshold compares score against threshold")
    @pytest.mark.parametrize(
        "similarity, threshold, expected",
        [
            (0.9, 0.8, True),
            (1.0, 0.5, True),
            (0.8, 0.8, True),
            (0.0, 0.0, True),
            (0.7, 0.8, False),
            (0.0, 0.5, False),
        ],
    )
    def test_is_similarity_above_threshold(self, similarity, threshold, expected):
        from src.contexts.coding.core.ai_invariants import is_similarity_above_threshold

        assert is_similarity_above_threshold(similarity, threshold) is expected


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestCodeComparisonAndMergeApproval:
    """Tests for can_codes_be_compared and can_merge_be_approved invariants."""

    @allure.title("Code comparison: valid pairs, self, and invalid names")
    def test_comparison_scenarios(self):
        """Two different codes with valid names can be compared; self/invalid cannot."""
        from src.contexts.coding.core.ai_invariants import can_codes_be_compared
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code_a = Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))
        code_b = Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0))
        assert can_codes_be_compared(code_a, code_b) is True
        assert can_codes_be_compared(code_a, code_a) is False

        for name in ("", "   ", "a" * 101):
            bad = Code(id=CodeId(value="9"), name=name, color=Color(255, 0, 0))
            assert can_codes_be_compared(bad, code_b) is False

    @allure.title("Merge approval: pending+existing vs non-pending/missing codes")
    def test_merge_approval_and_rejection(self):
        """Pending + both codes exist = approved; non-pending or missing = rejected."""
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_invariants import can_merge_be_approved
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Theme",
            code_b_id=CodeId(value="2"),
            code_b_name="Pattern",
            similarity=SimilarityScore(value=0.9),
            rationale="Similar concepts",
            status="pending",
        )
        assert (
            can_merge_be_approved(candidate, lambda cid: cid.value in ("1", "2"))
            is True
        )

        for status in ("merged", "dismissed"):
            c = DuplicateCandidate(
                code_a_id=CodeId(value="1"),
                code_a_name="Theme",
                code_b_id=CodeId(value="2"),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
                status=status,
            )
            assert can_merge_be_approved(c, lambda _: True) is False

        # Missing codes
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
        assert (
            is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="2"), []) is True
        )

        existing = [
            DuplicateCandidate(
                code_a_id=CodeId(value="1"),
                code_a_name="Theme",
                code_b_id=CodeId(value="2"),
                code_b_name="Pattern",
                similarity=SimilarityScore(value=0.9),
                rationale="Similar",
            )
        ]

        # Different pair and partial overlap are unique
        assert (
            is_duplicate_pair_unique(CodeId(value="3"), CodeId(value="4"), existing)
            is True
        )
        assert (
            is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="3"), existing)
            is True
        )

        # Exact pair and reversed pair are duplicates
        assert (
            is_duplicate_pair_unique(CodeId(value="1"), CodeId(value="2"), existing)
            is False
        )
        assert (
            is_duplicate_pair_unique(CodeId(value="2"), CodeId(value="1"), existing)
            is False
        )


# ============================================================
# Cross-Entity Invariant Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestHasMinimumCodesForDetection:
    """Tests for has_minimum_codes_for_detection invariant."""

    @allure.title("Code count checks, custom minimum, and generator support")
    def test_minimum_codes_and_custom_minimum(self):
        """Checks code list sizes, custom minimum, and generator support."""
        from src.contexts.coding.core.ai_invariants import (
            has_minimum_codes_for_detection,
        )
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        for count, expected in [(0, False), (1, False), (2, True), (10, True)]:
            codes = [
                Code(id=CodeId(value=i), name=f"Code{i}", color=Color(i, i, i))
                for i in range(count)
            ]
            assert has_minimum_codes_for_detection(codes) is expected

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
    @pytest.mark.parametrize(
        "text, kwargs, expected",
        [
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
        ],
    )
    def test_has_text_to_analyze(self, text, kwargs, expected):
        from src.contexts.coding.core.ai_invariants import has_text_to_analyze

        assert has_text_to_analyze(text, **kwargs) is expected
