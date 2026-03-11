"""
Coding Context: AI Deriver Tests

Tests for pure functions that compose invariants and derive domain events
for AI-assisted coding operations.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ============================================================
# Code Suggestion Deriver Tests
# ============================================================


class TestDeriveSuggestCode:
    """Tests for derive_suggest_code deriver."""

    def test_creates_suggestion_with_valid_inputs(self):
        """Should create CodeSuggested event with valid inputs."""
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

    @pytest.mark.parametrize(
        "name, rationale, expected_reason",
        [
            ("", "Valid rationale for the suggestion", "INVALID_NAME"),
            ("   ", "Valid rationale for the suggestion", "INVALID_NAME"),
            ("Theme", "", "INVALID_RATIONALE"),
        ],
        ids=["empty-name", "whitespace-name", "empty-rationale"],
    )
    def test_fails_with_invalid_name_or_rationale(self, name, rationale, expected_reason):
        """Should fail with SuggestionNotCreated for invalid name or rationale."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Color
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        result = derive_suggest_code(
            name=name,
            color=Color(100, 100, 100),
            rationale=rationale,
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value="1"),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == expected_reason

    @pytest.mark.parametrize(
        "suggestion_name, existing_name",
        [
            ("Resilience", "Resilience"),
            ("RESILIENCE", "Resilience"),
        ],
        ids=["exact-match", "case-insensitive"],
    )
    def test_fails_with_duplicate_name(self, suggestion_name, existing_name):
        """Should detect duplicate name regardless of case."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId, SourceId

        existing_code = Code(
            id=CodeId(value="1"),
            name=existing_name,
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(existing_codes=(existing_code,))

        result = derive_suggest_code(
            name=suggestion_name,
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value="1"),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "DUPLICATE_NAME"

    @pytest.mark.parametrize(
        "confidence, expected_reason",
        [
            (1.5, "INVALID_CONFIDENCE"),
            (-0.1, "INVALID_CONFIDENCE"),
        ],
        ids=["too-high", "negative"],
    )
    def test_fails_with_invalid_confidence(self, confidence, expected_reason):
        """Should fail when confidence is out of range."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Color
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        result = derive_suggest_code(
            name="Theme",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=confidence,
            source_id=SourceId(value="1"),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == expected_reason

    def test_accepts_boundary_confidence_values(self):
        """Should accept confidence at boundaries (0.0 and 1.0)."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_events import CodeSuggested
        from src.contexts.coding.core.entities import Color
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        # Test 0.0
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

        # Test 1.0
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


class TestDeriveApproveSuggestion:
    """Tests for derive_approve_suggestion deriver."""

    def test_approves_pending_suggestion_unmodified(self):
        """Should create CodeSuggestionApproved event for pending suggestion."""
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

    def test_approves_with_modifications(self):
        """Should indicate modification when name or color is changed."""
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

    def test_fails_when_suggestion_not_found_or_not_pending(self):
        """Should fail when suggestion doesn't exist or is not pending."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Color

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
        assert result.suggestion_id == suggestion_id

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

    def test_fails_with_duplicate_or_invalid_final_name(self):
        """Should fail when final name conflicts with existing code or is invalid."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
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
        state = AISuggestionState(
            existing_codes=(existing_code,),
            pending_suggestions=(suggestion,),
        )

        # Duplicate name
        result_dup = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Existing Theme",
            final_color=Color(100, 150, 200),
            state=state,
        )
        assert isinstance(result_dup, SuggestionNotApproved)
        assert result_dup.reason == "DUPLICATE_NAME"
        assert result_dup.name == "Existing Theme"

        # Invalid (empty) name
        state_no_codes = AISuggestionState(pending_suggestions=(suggestion,))
        result_inv = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="",
            final_color=Color(100, 150, 200),
            state=state_no_codes,
        )
        assert isinstance(result_inv, SuggestionNotApproved)
        assert result_inv.reason == "INVALID_NAME"


class TestDeriveRejectSuggestion:
    """Tests for derive_reject_suggestion deriver."""

    def test_rejects_pending_suggestion_with_and_without_reason(self):
        """Should create CodeSuggestionRejected event, with or without reason."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_reject_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_events import CodeSuggestionRejected
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

    def test_fails_when_suggestion_not_found_or_not_pending(self):
        """Should fail when suggestion doesn't exist or is not pending."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_reject_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotRejected
        from src.contexts.coding.core.entities import Color

        # Not found
        suggestion_id = SuggestionId(value="sug_nonexistent")
        state = AISuggestionState(pending_suggestions=())
        result = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason="Not relevant",
            state=state,
        )
        assert isinstance(result, SuggestionNotRejected)
        assert result.reason == "NOT_FOUND"
        assert result.suggestion_id == suggestion_id

        # Not pending
        suggestion_id2 = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id2,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme",
            confidence=0.85,
            status="rejected",
        )
        state2 = AISuggestionState(pending_suggestions=(suggestion,))
        result2 = derive_reject_suggestion(
            suggestion_id=suggestion_id2,
            reason="Duplicate",
            state=state2,
        )
        assert isinstance(result2, SuggestionNotRejected)
        assert result2.reason == "NOT_PENDING"
        assert result2.status == "rejected"


# ============================================================
# Duplicate Detection Deriver Tests
# ============================================================


class TestDeriveDetectDuplicates:
    """Tests for derive_detect_duplicates deriver."""

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
        "threshold",
        [1.5, -0.1],
        ids=["too-high", "negative"],
    )
    def test_fails_with_invalid_threshold(self, threshold):
        """Should fail when threshold is out of range."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value="1"), name="Theme", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value="2"), name="Pattern", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        result = derive_detect_duplicates(
            candidates=(),
            threshold=threshold,
            codes_analyzed=2,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == "INVALID_THRESHOLD"

    @pytest.mark.parametrize(
        "codes, codes_analyzed",
        [
            (("1_Theme",), 1),
            ((), 0),
        ],
        ids=["single-code", "no-codes"],
    )
    def test_fails_with_insufficient_codes(self, codes, codes_analyzed):
        """Should fail when not enough codes for detection."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        existing = tuple(
            Code(id=CodeId(value=c.split("_")[0]), name=c.split("_")[1], color=Color(255, 0, 0))
            for c in codes
        )
        state = AISuggestionState(existing_codes=existing)

        result = derive_detect_duplicates(
            candidates=(),
            threshold=0.8,
            codes_analyzed=codes_analyzed,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == "INSUFFICIENT_CODES"


class TestDeriveSuggestMerge:
    """Tests for derive_suggest_merge deriver."""

    def test_suggests_merge_with_valid_inputs(self):
        """Should create MergeSuggested event with valid inputs."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_events import MergeSuggested
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(
            id=CodeId(value="1"),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        target_code = Code(
            id=CodeId(value="2"),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(source_code, target_code))

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

    @pytest.mark.parametrize(
        "missing_code, source_id, target_id, expected_code_id",
        [
            ("source", "1", "2", "1"),
            ("target", "1", "2", "2"),
        ],
        ids=["source-missing", "target-missing"],
    )
    def test_fails_when_code_not_found(self, missing_code, source_id, target_id, expected_code_id):
        """Should fail when source or target code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_failure_events import MergeNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = []
        if missing_code != "source":
            codes.append(Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0)))
        if missing_code != "target":
            codes.append(Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0)))
        state = AISuggestionState(existing_codes=tuple(codes))

        result = derive_suggest_merge(
            source_code_id=CodeId(value=source_id),
            target_code_id=CodeId(value=target_id),
            similarity=SimilarityScore(0.9),
            rationale="Both codes are similar",
            state=state,
        )

        assert isinstance(result, MergeNotCreated)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=expected_code_id)

    def test_fails_with_empty_rationale(self):
        """Should fail when rationale is empty."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_failure_events import MergeNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0))
        target_code = Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(source_code, target_code))

        result = derive_suggest_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            similarity=SimilarityScore(0.9),
            rationale="",
            state=state,
        )

        assert isinstance(result, MergeNotCreated)
        assert result.reason == "INVALID_RATIONALE"


class TestDeriveApproveMerge:
    """Tests for derive_approve_merge deriver."""

    def test_approves_merge_with_valid_inputs_and_zero_segments(self):
        """Should create MergeSuggestionApproved event, including zero segments."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionApproved
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

    @pytest.mark.parametrize(
        "missing_code, expected_code_id",
        [
            ("source", "1"),
            ("target", "2"),
        ],
        ids=["source-missing", "target-missing"],
    )
    def test_fails_when_code_not_found(self, missing_code, expected_code_id):
        """Should fail when source or target code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_failure_events import MergeNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        codes = []
        if missing_code != "source":
            codes.append(Code(id=CodeId(value="1"), name="Resilience", color=Color(255, 0, 0)))
        if missing_code != "target":
            codes.append(Code(id=CodeId(value="2"), name="Perseverance", color=Color(0, 255, 0)))
        state = AISuggestionState(existing_codes=tuple(codes))

        result = derive_approve_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_to_move=5,
            state=state,
        )

        assert isinstance(result, MergeNotApproved)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=expected_code_id)


class TestDeriveDismissMerge:
    """Tests for derive_dismiss_merge deriver."""

    def test_dismisses_merge_with_and_without_candidate_and_reason(self):
        """Should succeed with or without pending candidate, and with or without reason."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_dismiss_merge,
        )
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionDismissed
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
        assert result.target_code_id == CodeId(value="2")
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
        assert result_with.reason == "Different contexts"

        # Without reason
        result_none = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason=None,
            state=state_empty,
        )
        assert isinstance(result_none, MergeSuggestionDismissed)
        assert result_none.reason is None

        # Reversed code order should still find candidate
        result_reversed = derive_dismiss_merge(
            source_code_id=CodeId(value="2"),
            target_code_id=CodeId(value="1"),
            reason="Not duplicates",
            state=state_with,
        )
        assert isinstance(result_reversed, MergeSuggestionDismissed)

    def test_fails_when_candidate_not_pending(self):
        """Should fail when candidate is not in pending status."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_dismiss_merge,
        )
        from src.contexts.coding.core.ai_entities import (
            DuplicateCandidate,
            SimilarityScore,
        )
        from src.contexts.coding.core.ai_failure_events import MergeNotDismissed
        from src.shared import CodeId

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Resilience",
            code_b_id=CodeId(value="2"),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="merged",
        )
        state = AISuggestionState(pending_duplicates=(candidate,))

        result = derive_dismiss_merge(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Not duplicates",
            state=state,
        )

        assert isinstance(result, MergeNotDismissed)
        assert result.reason == "NOT_PENDING"
        assert result.status == "merged"



# ============================================================
# Validation Helper Tests
# ============================================================


class TestValidateTextForAnalysis:
    """Tests for validate_text_for_analysis helper."""

    @pytest.mark.parametrize(
        "text, expected_valid, error_fragment",
        [
            ("This is a reasonably long text for analysis", True, ""),
            ("Short", False, "at least 10 characters"),
            ("", False, None),
            ("          ", False, None),
        ],
        ids=["valid", "too-short", "empty", "whitespace-only"],
    )
    def test_validates_text_length(self, text, expected_valid, error_fragment):
        """Should accept or reject text based on length requirements."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis(text)

        assert is_valid is expected_valid
        if error_fragment:
            assert error_fragment in error

    def test_uses_custom_min_length(self):
        """Should respect custom minimum length."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        # Should pass with min_length=5
        is_valid_short, _ = validate_text_for_analysis("Hello", min_length=5)
        assert is_valid_short is True

        # Should fail with min_length=10
        is_valid_long, error = validate_text_for_analysis("Hello", min_length=10)
        assert is_valid_long is False
        assert "at least 10 characters" in error
