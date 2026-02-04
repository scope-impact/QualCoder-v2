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
            source_id=SourceId(value=1),
            position=TextPosition(start=0, end=40),
        )

        result = derive_suggest_code(
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="This text discusses overcoming challenges, which indicates resilience",
            contexts=(context,),
            confidence=0.85,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, CodeSuggested)
        assert result.name == "Resilience"
        assert result.color == Color(100, 150, 200)
        assert result.confidence == 0.85
        assert len(result.contexts) == 1

    def test_fails_with_empty_name(self):
        """Should fail with SuggestionNotCreated for empty name."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Color
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        result = derive_suggest_code(
            name="",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "INVALID_NAME"

    def test_fails_with_whitespace_name(self):
        """Should fail with SuggestionNotCreated for whitespace-only name."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Color
        from src.shared import SourceId

        state = AISuggestionState(existing_codes=())

        result = derive_suggest_code(
            name="   ",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "INVALID_NAME"

    def test_fails_with_duplicate_name(self):
        """Should fail with SuggestionNotCreated when name matches existing code."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId, SourceId

        existing_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(existing_codes=(existing_code,))

        result = derive_suggest_code(
            name="Resilience",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "DUPLICATE_NAME"
        assert result.name == "Resilience"

    def test_fails_with_duplicate_name_case_insensitive(self):
        """Should detect duplicate name regardless of case."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_code,
        )
        from src.contexts.coding.core.ai_failure_events import SuggestionNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId, SourceId

        existing_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(existing_codes=(existing_code,))

        result = derive_suggest_code(
            name="RESILIENCE",
            color=Color(100, 100, 100),
            rationale="Valid rationale for the suggestion",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "DUPLICATE_NAME"

    def test_fails_with_invalid_confidence_too_high(self):
        """Should fail when confidence is greater than 1.0."""
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
            confidence=1.5,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "INVALID_CONFIDENCE"
        assert result.confidence == 1.5

    def test_fails_with_invalid_confidence_negative(self):
        """Should fail when confidence is negative."""
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
            confidence=-0.1,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "INVALID_CONFIDENCE"

    def test_fails_with_empty_rationale(self):
        """Should fail when rationale is empty."""
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
            rationale="",
            contexts=(),
            confidence=0.8,
            source_id=SourceId(value=1),
            state=state,
        )

        assert isinstance(result, SuggestionNotCreated)
        assert result.reason == "INVALID_RATIONALE"

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
            source_id=SourceId(value=1),
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
            source_id=SourceId(value=1),
            state=state,
        )
        assert isinstance(result_one, CodeSuggested)
        assert result_one.confidence == 1.0


class TestDeriveApproveSuggestion:
    """Tests for derive_approve_suggestion deriver."""

    def test_approves_pending_suggestion(self):
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

    def test_approves_with_modified_name(self):
        """Should indicate modification when name is changed."""
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
            final_name="Personal Resilience",
            final_color=Color(100, 150, 200),
            state=state,
        )

        assert isinstance(result, CodeSuggestionApproved)
        assert result.original_name == "Resilience"
        assert result.final_name == "Personal Resilience"
        assert result.modified is True

    def test_approves_with_modified_color(self):
        """Should indicate modification when color is changed."""
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
            final_color=Color(255, 0, 0),
            state=state,
        )

        assert isinstance(result, CodeSuggestionApproved)
        assert result.modified is True

    def test_fails_when_suggestion_not_found(self):
        """Should fail when suggestion doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Color

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

    def test_fails_when_suggestion_not_pending(self):
        """Should fail when suggestion is not in pending status."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme",
            confidence=0.85,
            status="approved",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        result = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Resilience",
            final_color=Color(100, 150, 200),
            state=state,
        )

        assert isinstance(result, SuggestionNotApproved)
        assert result.reason == "NOT_PENDING"
        assert result.status == "approved"

    def test_fails_with_duplicate_final_name(self):
        """Should fail when final name conflicts with existing code."""
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
            id=CodeId(value=1),
            name="Existing Theme",
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(
            existing_codes=(existing_code,),
            pending_suggestions=(suggestion,),
        )

        result = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="Existing Theme",
            final_color=Color(100, 150, 200),
            state=state,
        )

        assert isinstance(result, SuggestionNotApproved)
        assert result.reason == "DUPLICATE_NAME"
        assert result.name == "Existing Theme"

    def test_fails_with_invalid_final_name(self):
        """Should fail when final name is invalid."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotApproved
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
            name="Valid Name",
            color=Color(100, 150, 200),
            rationale="Theme description",
            confidence=0.85,
            status="pending",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        result = derive_approve_suggestion(
            suggestion_id=suggestion_id,
            final_name="",
            final_color=Color(100, 150, 200),
            state=state,
        )

        assert isinstance(result, SuggestionNotApproved)
        assert result.reason == "INVALID_NAME"


class TestDeriveRejectSuggestion:
    """Tests for derive_reject_suggestion deriver."""

    def test_rejects_pending_suggestion(self):
        """Should create CodeSuggestionRejected event for pending suggestion."""
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

        result = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason="Not relevant to this study",
            state=state,
        )

        assert isinstance(result, CodeSuggestionRejected)
        assert result.suggestion_id == suggestion_id
        assert result.name == "Resilience"
        assert result.reason == "Not relevant to this study"

    def test_rejects_without_reason(self):
        """Should allow rejection without reason."""
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
            rationale="Theme",
            confidence=0.85,
            status="pending",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        result = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason=None,
            state=state,
        )

        assert isinstance(result, CodeSuggestionRejected)
        assert result.reason is None

    def test_fails_when_suggestion_not_found(self):
        """Should fail when suggestion doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_reject_suggestion,
        )
        from src.contexts.coding.core.ai_entities import SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotRejected

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

    def test_fails_when_suggestion_not_pending(self):
        """Should fail when suggestion is not in pending status."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_reject_suggestion,
        )
        from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
        from src.contexts.coding.core.ai_failure_events import SuggestionNotRejected
        from src.contexts.coding.core.entities import Color

        suggestion_id = SuggestionId(value="sug_test123")
        suggestion = CodeSuggestion(
            id=suggestion_id,
            name="Resilience",
            color=Color(100, 150, 200),
            rationale="Theme",
            confidence=0.85,
            status="rejected",
        )
        state = AISuggestionState(pending_suggestions=(suggestion,))

        result = derive_reject_suggestion(
            suggestion_id=suggestion_id,
            reason="Duplicate",
            state=state,
        )

        assert isinstance(result, SuggestionNotRejected)
        assert result.reason == "NOT_PENDING"
        assert result.status == "rejected"


# ============================================================
# Duplicate Detection Deriver Tests
# ============================================================


class TestDeriveDetectDuplicates:
    """Tests for derive_detect_duplicates deriver."""

    def test_detects_duplicates_with_valid_inputs(self):
        """Should create DuplicatesDetected event with valid inputs."""
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

        code1 = Code(id=CodeId(value=1), name="Resilience", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Perseverance", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Resilience",
            code_b_id=CodeId(value=2),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Both relate to overcoming difficulties",
        )

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

    def test_detects_with_empty_candidates(self):
        """Should succeed with no candidates found (above threshold)."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_events import DuplicatesDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        result = derive_detect_duplicates(
            candidates=(),
            threshold=0.8,
            codes_analyzed=2,
            state=state,
        )

        assert isinstance(result, DuplicatesDetected)
        assert len(result.candidates) == 0

    def test_fails_with_invalid_threshold_too_high(self):
        """Should fail when threshold is greater than 1.0."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        result = derive_detect_duplicates(
            candidates=(),
            threshold=1.5,
            codes_analyzed=2,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == "INVALID_THRESHOLD"
        assert result.threshold == 1.5

    def test_fails_with_invalid_threshold_negative(self):
        """Should fail when threshold is negative."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        code2 = Code(id=CodeId(value=2), name="Pattern", color=Color(0, 255, 0))
        state = AISuggestionState(existing_codes=(code1, code2))

        result = derive_detect_duplicates(
            candidates=(),
            threshold=-0.1,
            codes_analyzed=2,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == "INVALID_THRESHOLD"

    def test_fails_with_insufficient_codes(self):
        """Should fail when not enough codes for detection."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        code1 = Code(id=CodeId(value=1), name="Theme", color=Color(255, 0, 0))
        state = AISuggestionState(existing_codes=(code1,))

        result = derive_detect_duplicates(
            candidates=(),
            threshold=0.8,
            codes_analyzed=1,
            state=state,
        )

        assert isinstance(result, DuplicatesNotDetected)
        assert result.reason == "INSUFFICIENT_CODES"
        assert result.count == 1
        assert result.minimum == 2

    def test_fails_with_no_codes(self):
        """Should fail when no codes exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_detect_duplicates,
        )
        from src.contexts.coding.core.ai_failure_events import DuplicatesNotDetected

        state = AISuggestionState(existing_codes=())

        result = derive_detect_duplicates(
            candidates=(),
            threshold=0.8,
            codes_analyzed=0,
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
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(source_code, target_code))

        result = derive_suggest_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            similarity=SimilarityScore(0.9),
            rationale="Both codes relate to overcoming obstacles",
            state=state,
        )

        assert isinstance(result, MergeSuggested)
        assert result.source_code_id == CodeId(value=1)
        assert result.source_code_name == "Resilience"
        assert result.target_code_id == CodeId(value=2)
        assert result.target_code_name == "Perseverance"
        assert result.similarity == SimilarityScore(0.9)

    def test_fails_when_source_code_not_found(self):
        """Should fail when source code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_failure_events import MergeNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(target_code,))

        result = derive_suggest_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            similarity=SimilarityScore(0.9),
            rationale="Both codes are similar",
            state=state,
        )

        assert isinstance(result, MergeNotCreated)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=1)

    def test_fails_when_target_code_not_found(self):
        """Should fail when target code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_suggest_merge,
        )
        from src.contexts.coding.core.ai_entities import SimilarityScore
        from src.contexts.coding.core.ai_failure_events import MergeNotCreated
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(existing_codes=(source_code,))

        result = derive_suggest_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            similarity=SimilarityScore(0.9),
            rationale="Both codes are similar",
            state=state,
        )

        assert isinstance(result, MergeNotCreated)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=2)

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

        source_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(source_code, target_code))

        result = derive_suggest_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            similarity=SimilarityScore(0.9),
            rationale="",
            state=state,
        )

        assert isinstance(result, MergeNotCreated)
        assert result.reason == "INVALID_RATIONALE"


class TestDeriveApproveMerge:
    """Tests for derive_approve_merge deriver."""

    def test_approves_merge_with_valid_inputs(self):
        """Should create MergeSuggestionApproved event with valid inputs."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(source_code, target_code))

        result = derive_approve_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            segments_to_move=5,
            state=state,
        )

        assert isinstance(result, MergeSuggestionApproved)
        assert result.source_code_id == CodeId(value=1)
        assert result.target_code_id == CodeId(value=2)
        assert result.segments_moved == 5

    def test_fails_when_source_code_not_found(self):
        """Should fail when source code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_failure_events import MergeNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(target_code,))

        result = derive_approve_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            segments_to_move=5,
            state=state,
        )

        assert isinstance(result, MergeNotApproved)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=1)

    def test_fails_when_target_code_not_found(self):
        """Should fail when target code doesn't exist."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_failure_events import MergeNotApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        state = AISuggestionState(existing_codes=(source_code,))

        result = derive_approve_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            segments_to_move=5,
            state=state,
        )

        assert isinstance(result, MergeNotApproved)
        assert result.reason == "CODE_NOT_FOUND"
        assert result.code_id == CodeId(value=2)

    def test_approves_with_zero_segments(self):
        """Should allow merge with zero segments to move."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_approve_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionApproved
        from src.contexts.coding.core.entities import Code, Color
        from src.shared import CodeId

        source_code = Code(
            id=CodeId(value=1),
            name="Resilience",
            color=Color(255, 0, 0),
        )
        target_code = Code(
            id=CodeId(value=2),
            name="Perseverance",
            color=Color(0, 255, 0),
        )
        state = AISuggestionState(existing_codes=(source_code, target_code))

        result = derive_approve_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            segments_to_move=0,
            state=state,
        )

        assert isinstance(result, MergeSuggestionApproved)
        assert result.segments_moved == 0


class TestDeriveDismissMerge:
    """Tests for derive_dismiss_merge deriver."""

    def test_dismisses_merge_without_candidate(self):
        """Should succeed even without a pending candidate."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_dismiss_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionDismissed
        from src.shared import CodeId

        state = AISuggestionState(pending_duplicates=())

        result = derive_dismiss_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason="Not actually duplicates",
            state=state,
        )

        assert isinstance(result, MergeSuggestionDismissed)
        assert result.source_code_id == CodeId(value=1)
        assert result.target_code_id == CodeId(value=2)
        assert result.reason == "Not actually duplicates"

    def test_dismisses_with_pending_candidate(self):
        """Should succeed with a pending candidate."""
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

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Resilience",
            code_b_id=CodeId(value=2),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="pending",
        )
        state = AISuggestionState(pending_duplicates=(candidate,))

        result = derive_dismiss_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason="Different contexts",
            state=state,
        )

        assert isinstance(result, MergeSuggestionDismissed)
        assert result.reason == "Different contexts"

    def test_dismisses_without_reason(self):
        """Should allow dismissal without reason."""
        from src.contexts.coding.core.ai_derivers import (
            AISuggestionState,
            derive_dismiss_merge,
        )
        from src.contexts.coding.core.ai_events import MergeSuggestionDismissed
        from src.shared import CodeId

        state = AISuggestionState(pending_duplicates=())

        result = derive_dismiss_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason=None,
            state=state,
        )

        assert isinstance(result, MergeSuggestionDismissed)
        assert result.reason is None

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
            code_a_id=CodeId(value=1),
            code_a_name="Resilience",
            code_b_id=CodeId(value=2),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="merged",
        )
        state = AISuggestionState(pending_duplicates=(candidate,))

        result = derive_dismiss_merge(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason="Not duplicates",
            state=state,
        )

        assert isinstance(result, MergeNotDismissed)
        assert result.reason == "NOT_PENDING"
        assert result.status == "merged"

    def test_handles_reversed_code_order(self):
        """Should find candidate regardless of code order."""
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

        # Candidate has code_a=1, code_b=2
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Resilience",
            code_b_id=CodeId(value=2),
            code_b_name="Perseverance",
            similarity=SimilarityScore(0.85),
            rationale="Similar codes",
            status="pending",
        )
        state = AISuggestionState(pending_duplicates=(candidate,))

        # Dismiss with reversed order (source=2, target=1)
        result = derive_dismiss_merge(
            source_code_id=CodeId(value=2),
            target_code_id=CodeId(value=1),
            reason="Not duplicates",
            state=state,
        )

        assert isinstance(result, MergeSuggestionDismissed)


# ============================================================
# Validation Helper Tests
# ============================================================


class TestValidateTextForAnalysis:
    """Tests for validate_text_for_analysis helper."""

    def test_accepts_valid_text(self):
        """Should accept text meeting minimum length."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis(
            "This is a reasonably long text for analysis"
        )

        assert is_valid is True
        assert error == ""

    def test_rejects_short_text(self):
        """Should reject text below minimum length."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis("Short")

        assert is_valid is False
        assert "at least 10 characters" in error

    def test_rejects_empty_text(self):
        """Should reject empty text."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis("")

        assert is_valid is False

    def test_rejects_whitespace_only(self):
        """Should reject whitespace-only text."""
        from src.contexts.coding.core.ai_derivers import validate_text_for_analysis

        is_valid, error = validate_text_for_analysis("          ")

        assert is_valid is False

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
