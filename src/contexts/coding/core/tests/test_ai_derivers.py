"""
Coding Context: AI Deriver Tests

Tests for pure functions that compose invariants and derive domain events
for AI-assisted coding operations.
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
# Code Suggestion Deriver Tests
# ============================================================


@allure.story("QC-028.04 AI Code Suggestions")
class TestDeriveSuggestCode:
    """Tests for derive_suggest_code deriver."""

    @allure.title("Creates suggestion with valid inputs and boundary confidence")
    def test_creates_suggestion_with_valid_inputs_and_boundary_confidence(self):
        """Should create CodeSuggested event with valid inputs including boundary confidence values."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_entities import TextContext
        from src.contexts.coding.core.ai_events import CodeSuggested
        from src.contexts.coding.core.entities import Color, TextPosition
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        context = TextContext(
            text="This relates to the theme of resilience",
            source_id=SourceId(value="1"),
            position=TextPosition(start=0, end=40),
        )

        result = derive_suggest_code(
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="This text discusses overcoming challenges, which indicates resilience",
            contexts=(context,),
            confidence=0.85,
            source_id=SourceId(value="1"),
            state=state,
        )

        assert isinstance(result, CodeSuggested)
        assert result.name == "Resilience"
        assert result.color == Color(100, 150, 200)
        assert result.confidence == 0.85
        assert len(result.contexts) == 1

        # Boundary confidence 0.0
        result_zero = derive_suggest_code(
            name="Theme1",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.0,
            source_id=SourceId(value="1"),
            state=state,
        )
        assert isinstance(result_zero, CodeSuggested)
        assert result_zero.confidence == 0.0

        # Boundary confidence 1.0
        result_one = derive_suggest_code(
            name="Theme2",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=1.0,
            source_id=SourceId(value="1"),
            state=state,
        )
        assert isinstance(result_one, CodeSuggested)
        assert result_one.confidence == 1.0

    @pytest.mark.parametrize(
        "name, rationale, confidence, existing_name, expected_reason",
        [
            ("", "Valid rationale for the suggestion", 0.8, None, "INVALID_NAME"),
            ("   ", "Valid rationale for the suggestion", 0.8, None, "INVALID_NAME"),
            ("Theme", "", 0.8, None, "INVALID_RATIONALE"),
            ("Resilience", "Valid rationale", 0.8, "Resilience", "DUPLICATE_NAME"),
            ("RESILIENCE", "Valid rationale", 0.8, "Resilience", "DUPLICATE_NAME"),
            ("Theme", "Valid rationale for the suggestion", 1.5, None, "INVALID_CONFIDENCE"),
            ("Theme", "Valid rationale for the suggestion", -0.1, None, "INVALID_CONFIDENCE"),
        ],
        ids=["empty-name", "whitespace-name", "empty-rationale",
             "exact-duplicate", "case-insensitive-duplicate",
             "confidence-too-high", "confidence-negative"],
    )
    @allure.title("Fails with invalid name, rationale, duplicate, or confidence")
    def test_fails_with_invalid_inputs(self, name, rationale, confidence, existing_name, expected_reason):
        """Should fail with SuggestionNotCreated for various invalid inputs."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId, SourceId

        existing_codes = ()
        if existing_name:
            existing_codes = (
                Code(id=CodeId(value="1"), name=existing_name, color=Color(255, 0, 0)),
            )
        state = AISuggestionState(existing_codes=existing_codes)

        result = derive_suggest_code(
            name=name,
            color=Color(100, 100, 100),
            rationale=rationale,
            contexts=(),
            confidence=confidence,
            source_id=SourceId(value="1"),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == expected_reason


@allure.story("QC-028.04 AI Code Suggestions")
class TestDeriveApproveSuggestion:
    """Tests for derive_approve_suggestion deriver."""

    @allure.title("Approves pending suggestion unmodified and with modifications")
    def test_approves_pending_suggestion(self):
        """Should create CodeSuggestionApproved event, detecting modifications."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_events import CodeSuggestionApproved
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme of overcoming challenges",
            confidence=0.85,
            status="pending",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        # Unmodified
        result = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Resilience",
            final_color=Color(100, 150, 200),
            state=state,
        )
        assert isinstance(result, CodeSuggestionApproved)
        assert result.suggestion_id == suggestion_id
        assert result.original_name == "Resilience"
        assert result.final_name == "Resilience"
        assert result.modified is False

        # Modified name
        result_name = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Personal Resilience",
            final_color=Color(100, 150, 200),
            state=state,
        )
        assert isinstance(result_name, CodeSuggestionApproved)
        assert result_name.original_name == "Resilience"
        assert result_name.final_name == "Personal Resilience"
        assert result_name.modified is True

        # Modified color
        result_color = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Resilience",
            final_color=Color(255, 0, 0),
            state=state,
        )
        assert isinstance(result_color, CodeSuggestionApproved)
        assert result_color.modified is True

    @allure.title("Fails when suggestion not found, not pending, duplicate or invalid name")
    def test_fails_when_not_found_not_pending_or_invalid_name(self):
        """Should fail when suggestion doesn't exist, is not pending, or has invalid final name."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        # Not found
        suggestion_id = SuggestionId(value="sug_nonexistent")
        state = AISuggestionState(pending_suggestions=())
        result = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Theme",
            final_color=Color(100, 100, 100),
            state=state,
        )
        assert isinstance(result, SuggestionNotApproved)
        assert result.reason == "NOT_FOUND"

        # Not pending (already approved)
        suggestion_id2 = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id2,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme",
            confidence=0.85,
            status="approved",
        )
        state2 = AISuggestionState(pending_suggestions=(suggestion,))
        result2 = derive_approve_suggestion(
            suggestion_id=suggestion_id2,
            final_name="Resilience",
            final_color=Color(100, 150, 200),
            state=state2,
        )
        assert isinstance(result2, SuggestionNotApproved)
        assert result2.reason == "NOT_PENDING"
        assert result2.status == "approved"

        # Duplicate name
        suggestion_id3 = SuggestionId(value="sug_test123")
        suggestion3 = CodeSuggestion(
            id=suggestion_id3,
            name="Theme",
            color=Color(100, 150, 200),
            rationale="Theme description",
            confidence=0.85,
            status="pending",
        )
        existing_code = Code(
            id=CodeId(value="1"),
            name="Existing Theme",
            color=Color(255, 0, 0),
        )
        state3 = AISuggestionState(
            existing_codes=(existing_code,),
            pending_suggestions=(suggestion3,),
        )
        result_dup = derive_approve_suggestion(
            suggestion_id=suggestion_id3,
            final_name="Existing Theme",
            final_color=Color(100, 150, 200),
            state=state3,
        )
        assert isinstance(result_dup, SuggestionNotApproved)
        assert result_dup.reason == "DUPLICATE_NAME"

        # Invalid (empty) name
        state_no_codes = AISuggestionState(pending_suggestions=(suggestion3,))
        result_inv = derive_approve_suggestion(
            suggestion_id=suggestion_id3,
            final_name="",
            final_color=Color(100, 150, 200),
            state=state_no_codes,
        )
        assert isinstance(result_inv, SuggestionNotApproved)
        assert result_inv.reason == "INVALID_NAME"


@allure.story("QC-028.04 AI Code Suggestions")
class TestDeriveRejectSuggestion:
    """Tests for derive_reject_suggestion deriver."""

    @allure.title("Rejects pending suggestion and fails when not found or not pending")
    def test_rejects_and_fails_when_invalid(self):
        """Should reject pending suggestion and fail when not found or not pending."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_reject_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_events import CodeSuggestionRejected
        from src.contexts.coding.core.ai_failure_events import SuggestionNotRejected
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme of overcoming challenges",
            confidence=0.85,
            status="pending",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        # With reason
        result = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason="Not relevant to this study",
            state=state,
        )
        assert isinstance(result, CodeSuggestionRejected)
        assert result.suggestion_id == suggestion_id
        assert result.name == "Resilience"
        assert result.reason == "Not relevant to this study"

        # Without reason
        result_none = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason=None,
            state=state,
        )
        assert isinstance(result_none, CodeSuggestionRejected)
        assert result_none.reason is None

        # Not found
        result_nf = derive_reject_suggestion(
            suggestion_id=SuggestionId(value="sug_nonexistent"),
            reason="Not relevant",
            state=AISuggestionState(pending_suggestions=()),
        )
        assert isinstance(result_nf, SuggestionNotRejected)
        assert result_nf.reason == "NOT_FOUND"

        # Not pending
        rejected_suggestion = CodeSuggestion(
            id=SuggestionId(value="sug_test123"),
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme",
            confidence=0.85,
            status="rejected",
        )
        state2 = AISuggestionState(pending_suggestions=(rejected_suggestion,))
        result2 = derive_reject_suggestion(
            suggestion_id=SuggestionId(value="sug_test123"),
            reason="Duplicate",
            state=state2,
        )
        assert isinstance(result2, SuggestionNotRejected)
        assert result2.reason == "NOT_PENDING"


# ============================================================
# Duplicate Detection Deriver Tests
# ============================================================


@allure.story("QC-028.04 AI Duplicate Detection")
class TestDeriveDetectDuplicates:
    """Tests for derive_detect_duplicates deriver."""

    @allure.title("Detects duplicates with and without candidates")
    def test_detects_duplicates_with_and_without_candidates(self):
        """Should create DuplicatesDetected event with valid inputs, including empty candidates."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_events import DuplicatesDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Resilience",
            code_b_id=CodeId(value="2"),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Both relate to overcoming difficulties",
        )

        # With candidates
        result = derive_detect_duplicates(
            candidates=(candidate,),
            threshold=0.8,
            codes_analyzed=2,
            state=state,
        )
        assert isinstance(result, DuplicatesDetected)
        assert len(result.candidates) == 1
        assert result.threshold == 0.8
        assert result.codes_analyzed == 2

        # Empty candidates
        result_empty = derive_detect_duplicates(
            candidates=(),
            threshold=0.8,
            codes_analyzed=2,
            state=state,
        )
        assert isinstance(result_empty, DuplicatesDetected)
        assert len(result_empty.candidates) == 0

    @pytest.mark.parametrize(
        "threshold, codes_spec, codes_analyzed, expected_reason",
        [
            (1.5, "two", 2, "INVALID_THRESHOLD"),
            (-0.1, "two", 2, "INVALID_THRESHOLD"),
            (0.8, "one", 1, "INSUFFICIENT_CODES"),
            (0.8, "none", 0, "INSUFFICIENT_CODES"),
        ],
        ids=["threshold-too-high", "threshold-negative", "single-code", "no-codes"],
    )
    @allure.title("Fails with invalid threshold or insufficient codes")
    def test_fails_with_invalid_threshold_or_insufficient_codes(
        self, threshold, codes_spec, codes_analyzed, expected_reason
    ):
        """Should fail when threshold is out of range or not enough codes."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes_map = {
            "two": (
                Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),
                Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0)),
            ),
            "one": (Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0)),),
            "none": (),
        }
        state = AISuggestionState(existing_codes=codes_map[codes_spec])

        result = derive_detect_duplicates(
            candidates=(),
            threshold=threshold,
            codes_analyzed=codes_analyzed,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == expected_reason


@allure.story("QC-028.04 AI Merge Suggestions")
class TestDeriveSuggestMerge:
    """Tests for derive_suggest_merge deriver."""

    @allure.title("Suggests merge and fails when code not found or rationale empty")
    def test_suggests_merge_and_fails_on_invalid(self):
        """Should create MergeSuggested event and fail on missing code or empty rationale."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_events import MergeSuggested
        from src.contexts.coding.core.ai_failure_events import MergeNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0))
        target_code = Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(source_code, target_code))

        # Valid merge
        result = derive_suggest_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            similarity=SimilarityScore(0.9),
            rationale="Both codes relate to overcoming obstacles",
            state=state,
        )
        assert isinstance(result, MergeSuggested)
        assert result.source_code_id == CodeId(value="1")
        assert result.source_code_name == "Resilience"
        assert result.target_code_id == CodeId(value="2")
        assert result.target_code_name == "Perseverance"
        assert result.similarity == SimilarityScore(0.9)

        # Source missing
        state_no_source = AISuggestionState(existing_codes=(target_code,))
        result_ns = derive_suggest_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            similarity=SimilarityScore(0.9),
            rationale="Both codes are similar",
            state=state_no_source,
        )
        assert isinstance(result_ns, MergeNotCreated)
        assert result_ns.reason == "CODE_NOT_FOUND"
        assert result_ns.code_id == CodeId(value="1")

        # Target missing
        state_no_target = AISuggestionState(existing_codes=(source_code,))
        result_nt = derive_suggest_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            similarity=SimilarityScore(0.9),
            rationale="Both codes are similar",
            state=state_no_target,
        )
        assert isinstance(result_nt, MergeNotCreated)
        assert result_nt.reason == "CODE_NOT_FOUND"
        assert result_nt.code_id == CodeId(value="2")

        # Empty rationale
        result_er = derive_suggest_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            similarity=SimilarityScore(0.9),
            rationale="",
            state=state,
        )
        assert isinstance(result_er, MergeNotCreated)
        assert result_er.reason == "INVALID_RATIONALE"


@allure.story("QC-028.04 AI Merge Suggestions")
class TestDeriveApproveMerge:
    """Tests for derive_approve_merge deriver."""

    @allure.title("Approves merge and fails when code not found")
    def test_approves_merge_and_fails_when_not_found(self):
        """Should create MergeSuggestionApproved event and fail on missing code."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionApproved
        from src.contexts.coding.core.ai_failure_events import MergeNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0))
        target_code = Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(source_code, target_code))

        # Normal case
        result = derive_approve_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_to_move=5,
            state=state,
        )
        assert isinstance(result, MergeSuggestionApproved)
        assert result.source_code_id == CodeId(value="1")
        assert result.target_code_id == CodeId(value="2")
        assert result.segments_moved == 5

        # Zero segments
        result_zero = derive_approve_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_to_move=0,
            state=state,
        )
        assert isinstance(result_zero, MergeSuggestionApproved)
        assert result_zero.segments_moved == 0

        # Source missing
        state_ns = AISuggestionState(existing_codes=(target_code,))
        result_ns = derive_approve_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_to_move=5,
            state=state_ns,
        )
        assert isinstance(result_ns, MergeNotApproved)
        assert result_ns.reason == "CODE_NOT_FOUND"
        assert result_ns.code_id == CodeId(value="1")

        # Target missing
        state_nt = AISuggestionState(existing_codes=(source_code,))
        result_nt = derive_approve_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_to_move=5,
            state=state_nt,
        )
        assert isinstance(result_nt, MergeNotApproved)
        assert result_nt.reason == "CODE_NOT_FOUND"
        assert result_nt.code_id == CodeId(value="2")


@allure.story("QC-028.04 AI Merge Suggestions")
class TestDeriveDismissMerge:
    """Tests for derive_dismiss_merge deriver."""

    @allure.title("Dismisses merge and fails when candidate not pending")
    def test_dismisses_and_fails_when_not_pending(self):
        """Should dismiss merge in various scenarios and fail when candidate is not pending."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_dismiss_merge,
        )
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionDismissed
        from src.contexts.coding.core.ai_failure_events import MergeNotDismissed
        from src.shared import CodeId

        # Without candidate, with reason
        state_empty = AISuggestionState(pending_duplicates=())
        result = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Not actually duplicates",
            state=state_empty,
        )
        assert isinstance(result, MergeSuggestionDismissed)
        assert result.source_code_id == CodeId(value="1")
        assert result.reason == "Not actually duplicates"

        # With candidate
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Resilience",
            code_b_id=CodeId(value="2"),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="pending",
        )
        state_with = AISuggestionState(pending_duplicates=(candidate,))
        result_with = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Different contexts",
            state=state_with,
        )
        assert isinstance(result_with, MergeSuggestionDismissed)

        # Without reason
        result_none = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason=None,
            state=state_empty,
        )
        assert isinstance(result_none, MergeSuggestionDismissed)
        assert result_none.reason is None

        # Reversed code order
        result_reversed = derive_dismiss_merge(
            source_code_id=CodeId(value="2"),
            target_code_id=CodeId(value="1"),
            reason="Not duplicates",
            state=state_with,
        )
        assert isinstance(result_reversed, MergeSuggestionDismissed)

        # Not pending
        candidate_merged = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Resilience",
            code_b_id=CodeId(value="2"),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="merged",
        )
        state_merged = AISuggestionState(pending_duplicates=(candidate_merged,))
        result_fail = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Not duplicates",
            state=state_merged,
        )
        assert isinstance(result_fail, MergeNotDismissed)
        assert result_fail.reason == "NOT_PENDING"
        assert result_fail.status == "merged"


# ============================================================
# Validation Helper Tests
# ============================================================


@allure.story("QC-028.04 AI Validation Helpers")
class TestValidateTextForAnalysis:
    """Tests for validate_text_for_analysis helper."""

    @pytest.mark.parametrize(
        "text, min_length, expected_valid, error_fragment",
        [
            ("This is a reasonably long text for analysis", 10, True, ""),
            ("Short", 10, False, "at least 10 characters"),
            ("", 10, False, None),
            ("          ", 10, False, None),
            ("Hello", 5, True, ""),
            ("Hello", 10, False, "at least 10 characters"),
        ],
        ids=["valid", "too-short", "empty", "whitespace-only", "custom-min-pass", "custom-min-fail"],
    )
    @allure.title("Validates text length with default and custom min_length")
    def test_validates_text_length(self, text, min_length, expected_valid, error_fragment):
        """Should accept or reject text based on length requirements."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis(text, min_length=min_length)

        assert is_valid is expected_valid
        if error_fragment:
            assert error_fragment in error
