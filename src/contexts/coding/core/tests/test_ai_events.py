"""
Tests for AI-Assisted Coding Events and Failure Events.

Tests for:
- Code Suggestion Events (CodeSuggested, CodeSuggestionApproved, CodeSuggestionRejected)
- Duplicate Detection Events (DuplicatesDetected, MergeSuggested, MergeSuggestionApproved, MergeSuggestionDismissed)
- Suggestion Failure Events (SuggestionNotCreated, SuggestionNotApproved, SuggestionNotRejected)
- Duplicate Detection Failure Events (DuplicatesNotDetected)
- Merge Failure Events (MergeNotCreated, MergeNotApproved, MergeNotDismissed)
"""

import allure
import pytest

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-028 Code Management"),
]

from src.contexts.coding.core.ai_entities import (
    DetectionId,
    DuplicateCandidate,
    SimilarityScore,
    SuggestionId,
    TextContext,
)
from src.contexts.coding.core.ai_events import (
    CodeSuggested,
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicatesDetected,
    MergeSuggested,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
)
from src.contexts.coding.core.ai_failure_events import (
    DuplicatesNotDetected,
    MergeNotApproved,
    MergeNotCreated,
    MergeNotDismissed,
    SuggestionNotApproved,
    SuggestionNotCreated,
    SuggestionNotRejected,
)
from src.contexts.coding.core.entities import Color, TextPosition
from src.shared.common.types import CodeId, SourceId

# ============================================================
# Code Suggestion Events Tests
# ============================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestCodeSuggestionEvents:
    """Tests for CodeSuggested, CodeSuggestionApproved, CodeSuggestionRejected events."""

    @allure.title("CodeSuggested: correct event type, fields, and unique IDs")
    def test_code_suggested(self):
        """create() should generate event with correct type and all fields; unique event IDs."""
        assert CodeSuggested.event_type == "coding.ai_code_suggested"

        suggestion_id = SuggestionId.new()
        color = Color(red=255, green=100, blue=50)
        context = TextContext(
            text="Sample text for analysis",
            source_id=SourceId(value="1"),
            position=TextPosition(start=0, end=24),
        )
        source_id = SourceId(value="1")

        event = CodeSuggested.create(
            suggestion_id=suggestion_id,
            name="Anxiety",
            color=color,
            rationale="Text discusses anxiety symptoms",
            contexts=(context,),
            confidence=0.85,
            source_id=source_id,
        )

        assert event.suggestion_id == suggestion_id
        assert event.name == "Anxiety"
        assert event.color == color
        assert event.rationale == "Text discusses anxiety symptoms"
        assert event.contexts == (context,)
        assert event.confidence == 0.85
        assert event.source_id == source_id
        assert event.event_id is not None
        assert event.occurred_at is not None

        # Unique event IDs
        event2 = CodeSuggested.create(
            suggestion_id=suggestion_id, name="Test", color=color,
            rationale="Test rationale", contexts=(), confidence=0.5,
            source_id=source_id,
        )
        assert event.event_id != event2.event_id

    @allure.title("CodeSuggestionApproved and Rejected: modifications, reasons, defaults")
    def test_code_suggestion_approved_and_rejected(self):
        """Approved tracks modifications; Rejected stores reason with None default."""
        assert CodeSuggestionApproved.event_type == "coding.ai_code_suggestion_approved"
        assert CodeSuggestionRejected.event_type == "coding.ai_code_suggestion_rejected"

        # Approved: unmodified
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(), created_code_id=CodeId(value="42"),
            original_name="Anxiety", final_name="Anxiety", modified=False,
        )
        assert event.modified is False

        # Approved: modified
        event2 = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(), created_code_id=CodeId(value="42"),
            original_name="Anxiety", final_name="General Anxiety", modified=True,
        )
        assert event2.modified is True

        # Approved: default modified=False
        event3 = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(), created_code_id=CodeId(value="42"),
            original_name="Test", final_name="Test",
        )
        assert event3.modified is False

        # Rejected: with reason, None, and default
        ev_r1 = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(), name="Anxiety",
            reason="Too broad for this analysis",
        )
        assert ev_r1.reason == "Too broad for this analysis"

        ev_r2 = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(), name="Test", reason=None,
        )
        assert ev_r2.reason is None

        ev_r3 = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(), name="Test",
        )
        assert ev_r3.reason is None


# ============================================================
# Duplicate Detection Events Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestDuplicateDetectionEvents:
    """Tests for DuplicatesDetected, MergeSuggested, MergeSuggestionApproved, MergeSuggestionDismissed."""

    @allure.title("DuplicatesDetected and MergeSuggested: event types and fields")
    def test_duplicates_detected_and_merge_suggested(self):
        """DuplicatesDetected stores candidates; MergeSuggested stores merge details."""
        assert DuplicatesDetected.event_type == "coding.ai_duplicates_detected"
        assert MergeSuggested.event_type == "coding.ai_merge_suggested"

        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"), code_a_name="Anxiety",
            code_b_id=CodeId(value="2"), code_b_name="Anxiousness",
            similarity=SimilarityScore(value=0.92), rationale="Both codes refer to worry",
        )
        event = DuplicatesDetected.create(
            detection_id=DetectionId.new(), candidates=(candidate,),
            threshold=0.8, codes_analyzed=50,
        )
        assert len(event.candidates) == 1
        assert event.candidates[0].code_a_name == "Anxiety"
        assert event.threshold == 0.8

        # Empty candidates
        event2 = DuplicatesDetected.create(
            detection_id=DetectionId.new(), candidates=(), threshold=0.9, codes_analyzed=10,
        )
        assert len(event2.candidates) == 0

        # MergeSuggested
        merge_event = MergeSuggested.create(
            source_code_id=CodeId(value="1"), source_code_name="Anxiety",
            target_code_id=CodeId(value="2"), target_code_name="Worry",
            similarity=SimilarityScore(value=0.88),
            rationale="Both codes describe similar emotional states",
        )
        assert merge_event.source_code_id.value == "1"
        assert merge_event.target_code_name == "Worry"

    @allure.title("MergeSuggestionApproved and Dismissed: segments, reasons, defaults")
    def test_merge_approved_and_dismissed(self):
        """Approved tracks segments moved; Dismissed stores reason with None default."""
        assert MergeSuggestionApproved.event_type == "coding.ai_merge_suggestion_approved"
        assert MergeSuggestionDismissed.event_type == "coding.ai_merge_suggestion_dismissed"

        event = MergeSuggestionApproved.create(
            source_code_id=CodeId(value="1"), target_code_id=CodeId(value="2"),
            segments_moved=15,
        )
        assert event.segments_moved == 15

        # Dismissed with reason, None, and default
        ev1 = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"), target_code_id=CodeId(value="2"),
            reason="Codes are conceptually different",
        )
        assert ev1.reason == "Codes are conceptually different"

        ev2 = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"), target_code_id=CodeId(value="2"), reason=None,
        )
        assert ev2.reason is None

        ev3 = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"), target_code_id=CodeId(value="2"),
        )
        assert ev3.reason is None


# ============================================================
# Suggestion Failure Events Tests
# ============================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestSuggestionFailureEvents:
    """Tests for SuggestionNotCreated, SuggestionNotApproved, SuggestionNotRejected."""

    @allure.title("All suggestion failure factory methods produce correct events")
    def test_all_suggestion_failure_factories(self):
        """All factory methods create correct failure events with proper properties."""
        # SuggestionNotCreated
        ev1 = SuggestionNotCreated.invalid_name("  ")
        assert ev1.event_type == "SUGGESTION_NOT_CREATED/INVALID_NAME"
        assert ev1.name == "  "
        assert ev1.reason == "INVALID_NAME"
        assert "Invalid suggestion name" in ev1.message
        assert ev1.is_failure is True
        assert ev1.operation == "SUGGESTION_NOT_CREATED"

        ev2 = SuggestionNotCreated.duplicate_name("Anxiety")
        assert ev2.event_type == "SUGGESTION_NOT_CREATED/DUPLICATE_NAME"
        assert "already exists" in ev2.message

        ev3 = SuggestionNotCreated.invalid_confidence(1.5)
        assert ev3.event_type == "SUGGESTION_NOT_CREATED/INVALID_CONFIDENCE"
        assert "0.0-1.0" in ev3.message

        ev4 = SuggestionNotCreated.invalid_rationale()
        assert ev4.event_type == "SUGGESTION_NOT_CREATED/INVALID_RATIONALE"
        assert "1-1000 characters" in ev4.message

        # SuggestionNotApproved
        suggestion_id = SuggestionId(value="sug_abc123")
        ev5 = SuggestionNotApproved.not_found(suggestion_id)
        assert ev5.event_type == "SUGGESTION_NOT_APPROVED/NOT_FOUND"
        assert "not found" in ev5.message

        ev6 = SuggestionNotApproved.not_pending(suggestion_id, "rejected")
        assert ev6.event_type == "SUGGESTION_NOT_APPROVED/NOT_PENDING"
        assert ev6.status == "rejected"

        ev7 = SuggestionNotApproved.duplicate_name("Anxiety")
        assert ev7.event_type == "SUGGESTION_NOT_APPROVED/DUPLICATE_NAME"

        ev8 = SuggestionNotApproved.invalid_name("")
        assert ev8.event_type == "SUGGESTION_NOT_APPROVED/INVALID_NAME"

        # SuggestionNotRejected
        suggestion_id2 = SuggestionId(value="sug_xyz789")
        ev9 = SuggestionNotRejected.not_found(suggestion_id2)
        assert ev9.event_type == "SUGGESTION_NOT_REJECTED/NOT_FOUND"

        ev10 = SuggestionNotRejected.not_pending(suggestion_id2, "approved")
        assert ev10.event_type == "SUGGESTION_NOT_REJECTED/NOT_PENDING"
        assert ev10.status == "approved"


# ============================================================
# Duplicate Detection & Merge Failure Events Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestDuplicateAndMergeFailureEvents:
    """Tests for DuplicatesNotDetected, MergeNotCreated, MergeNotApproved, MergeNotDismissed."""

    @allure.title("All duplicate detection and merge failure factory methods")
    def test_all_failure_factories(self):
        """All factory methods create correct failure events."""
        # DuplicatesNotDetected
        ev1 = DuplicatesNotDetected.invalid_threshold(1.5)
        assert ev1.event_type == "DUPLICATES_NOT_DETECTED/INVALID_THRESHOLD"
        assert ev1.threshold == 1.5
        assert ev1.is_failure is True
        assert "0.0-1.0" in ev1.message

        ev2 = DuplicatesNotDetected.insufficient_codes(count=1, minimum=2)
        assert ev2.event_type == "DUPLICATES_NOT_DETECTED/INSUFFICIENT_CODES"
        assert ev2.count == 1
        assert ev2.minimum == 2
        assert "at least 2" in ev2.message

        # MergeNotCreated
        ev3 = MergeNotCreated.code_not_found(CodeId(value="42"))
        assert ev3.event_type == "MERGE_NOT_CREATED/CODE_NOT_FOUND"
        assert "not found" in ev3.message

        ev4 = MergeNotCreated.invalid_rationale()
        assert ev4.event_type == "MERGE_NOT_CREATED/INVALID_RATIONALE"
        assert "1-1000 characters" in ev4.message

        # MergeNotApproved
        ev5 = MergeNotApproved.code_not_found(CodeId(value="99"))
        assert ev5.event_type == "MERGE_NOT_APPROVED/CODE_NOT_FOUND"
        assert "not found" in ev5.message

        # MergeNotDismissed
        ev6 = MergeNotDismissed.not_pending(CodeId(value="1"), CodeId(value="2"), "merged")
        assert ev6.event_type == "MERGE_NOT_DISMISSED/NOT_PENDING"
        assert ev6.status == "merged"
        assert "merged" in ev6.message
        assert "1" in ev6.message or "2" in ev6.message
