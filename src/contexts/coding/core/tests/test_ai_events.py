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


class TestCodeSuggested:
    """Tests for CodeSuggested domain event."""

    def test_create_with_correct_event_type_and_all_fields(self):
        """create() should generate event with correct type and all fields populated."""
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

    def test_create_generates_unique_event_ids(self):
        """Each created event should have a unique event_id."""
        suggestion_id = SuggestionId.new()
        color = Color(red=100, green=100, blue=100)
        source_id = SourceId(value="1")

        event1 = CodeSuggested.create(
            suggestion_id=suggestion_id,
            name="Test",
            color=color,
            rationale="Test rationale",
            contexts=(),
            confidence=0.5,
            source_id=source_id,
        )
        event2 = CodeSuggested.create(
            suggestion_id=suggestion_id,
            name="Test",
            color=color,
            rationale="Test rationale",
            contexts=(),
            confidence=0.5,
            source_id=source_id,
        )

        assert event1.event_id != event2.event_id


class TestCodeSuggestionApproved:
    """Tests for CodeSuggestionApproved domain event."""

    def test_create_with_correct_event_type_and_all_fields(self):
        """create() should generate event with correct type, handle modifications and defaults."""
        assert CodeSuggestionApproved.event_type == "coding.ai_code_suggestion_approved"

        suggestion_id = SuggestionId.new()
        code_id = CodeId(value="42")

        # Unmodified approval
        event = CodeSuggestionApproved.create(
            suggestion_id=suggestion_id,
            created_code_id=code_id,
            original_name="Anxiety",
            final_name="Anxiety",
            modified=False,
        )
        assert event.suggestion_id == suggestion_id
        assert event.created_code_id == code_id
        assert event.original_name == "Anxiety"
        assert event.final_name == "Anxiety"
        assert event.modified is False

    def test_create_with_modification_and_defaults(self):
        """create() should track modifications and default modified to False."""
        # Modified approval
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value="42"),
            original_name="Anxiety",
            final_name="General Anxiety",
            modified=True,
        )
        assert event.original_name == "Anxiety"
        assert event.final_name == "General Anxiety"
        assert event.modified is True

        # Default: modified=False
        event_default = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value="42"),
            original_name="Test",
            final_name="Test",
        )
        assert event_default.modified is False


class TestCodeSuggestionRejected:
    """Tests for CodeSuggestionRejected domain event."""

    def test_create_with_correct_event_type_and_reason_handling(self):
        """create() should store rejection reason, handle None, and default to None."""
        assert CodeSuggestionRejected.event_type == "coding.ai_code_suggestion_rejected"

        suggestion_id = SuggestionId.new()

        # With reason
        event = CodeSuggestionRejected.create(
            suggestion_id=suggestion_id,
            name="Anxiety",
            reason="Too broad for this analysis",
        )
        assert event.suggestion_id == suggestion_id
        assert event.name == "Anxiety"
        assert event.reason == "Too broad for this analysis"

        # Explicit None
        event_none = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
            reason=None,
        )
        assert event_none.reason is None

        # Default (no reason parameter)
        event_default = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
        )
        assert event_default.reason is None


# ============================================================
# Duplicate Detection Events Tests
# ============================================================


class TestDuplicatesDetected:
    """Tests for DuplicatesDetected domain event."""

    def test_create_with_correct_event_type_and_candidates(self):
        """create() should store detection results with correct event type."""
        assert DuplicatesDetected.event_type == "coding.ai_duplicates_detected"

        detection_id = DetectionId.new()
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"),
            code_a_name="Anxiety",
            code_b_id=CodeId(value="2"),
            code_b_name="Anxiousness",
            similarity=SimilarityScore(value=0.92),
            rationale="Both codes refer to worry",
        )

        event = DuplicatesDetected.create(
            detection_id=detection_id,
            candidates=(candidate,),
            threshold=0.8,
            codes_analyzed=50,
        )

        assert event.detection_id == detection_id
        assert len(event.candidates) == 1
        assert event.candidates[0].code_a_name == "Anxiety"
        assert event.threshold == 0.8
        assert event.codes_analyzed == 50

    def test_create_with_empty_candidates(self):
        """create() should work with no candidates found."""
        event = DuplicatesDetected.create(
            detection_id=DetectionId.new(),
            candidates=(),
            threshold=0.9,
            codes_analyzed=10,
        )

        assert len(event.candidates) == 0
        assert event.codes_analyzed == 10


class TestMergeSuggested:
    """Tests for MergeSuggested domain event."""

    def test_create_with_correct_event_type_and_all_fields(self):
        """create() should store merge suggestion details with correct event type."""
        assert MergeSuggested.event_type == "coding.ai_merge_suggested"

        source_code_id = CodeId(value="1")
        target_code_id = CodeId(value="2")
        similarity = SimilarityScore(value=0.88)

        event = MergeSuggested.create(
            source_code_id=source_code_id,
            source_code_name="Anxiety",
            target_code_id=target_code_id,
            target_code_name="Worry",
            similarity=similarity,
            rationale="Both codes describe similar emotional states",
        )

        assert event.source_code_id == source_code_id
        assert event.source_code_name == "Anxiety"
        assert event.target_code_id == target_code_id
        assert event.target_code_name == "Worry"
        assert event.similarity == similarity
        assert event.rationale == "Both codes describe similar emotional states"


class TestMergeSuggestionApproved:
    """Tests for MergeSuggestionApproved domain event."""

    def test_create_with_correct_event_type_and_segment_count(self):
        """create() should track segments moved with correct event type."""
        assert (
            MergeSuggestionApproved.event_type == "coding.ai_merge_suggestion_approved"
        )

        source_code_id = CodeId(value="1")
        target_code_id = CodeId(value="2")

        event = MergeSuggestionApproved.create(
            source_code_id=source_code_id,
            target_code_id=target_code_id,
            segments_moved=15,
        )

        assert event.source_code_id == source_code_id
        assert event.target_code_id == target_code_id
        assert event.segments_moved == 15


class TestMergeSuggestionDismissed:
    """Tests for MergeSuggestionDismissed domain event."""

    def test_create_with_correct_event_type_and_reason_handling(self):
        """create() should store dismissal reason, handle None, and default to None."""
        assert (
            MergeSuggestionDismissed.event_type
            == "coding.ai_merge_suggestion_dismissed"
        )

        # With reason
        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Codes are conceptually different",
        )
        assert event.source_code_id.value == "1"
        assert event.target_code_id.value == "2"
        assert event.reason == "Codes are conceptually different"

        # Explicit None
        event_none = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason=None,
        )
        assert event_none.reason is None

        # Default (no reason parameter)
        event_default = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
        )
        assert event_default.reason is None


# ============================================================
# Suggestion Failure Events Tests
# ============================================================


class TestSuggestionNotCreated:
    """Tests for SuggestionNotCreated failure event."""

    def test_all_factories_and_properties(self):
        """All factory methods should create correct failure events with proper properties."""
        # invalid_name
        ev1 = SuggestionNotCreated.invalid_name("  ")
        assert ev1.event_type == "SUGGESTION_NOT_CREATED/INVALID_NAME"
        assert ev1.name == "  "
        assert ev1.reason == "INVALID_NAME"
        assert "Invalid suggestion name" in ev1.message
        assert ev1.is_failure is True
        assert ev1.operation == "SUGGESTION_NOT_CREATED"

        # duplicate_name
        ev2 = SuggestionNotCreated.duplicate_name("Anxiety")
        assert ev2.event_type == "SUGGESTION_NOT_CREATED/DUPLICATE_NAME"
        assert ev2.name == "Anxiety"
        assert ev2.reason == "DUPLICATE_NAME"
        assert "already exists" in ev2.message

        # invalid_confidence
        ev3 = SuggestionNotCreated.invalid_confidence(1.5)
        assert ev3.event_type == "SUGGESTION_NOT_CREATED/INVALID_CONFIDENCE"
        assert ev3.confidence == 1.5
        assert ev3.reason == "INVALID_CONFIDENCE"
        assert "0.0-1.0" in ev3.message

        # invalid_rationale
        ev4 = SuggestionNotCreated.invalid_rationale()
        assert ev4.event_type == "SUGGESTION_NOT_CREATED/INVALID_RATIONALE"
        assert ev4.reason == "INVALID_RATIONALE"
        assert "1-1000 characters" in ev4.message


class TestSuggestionNotApproved:
    """Tests for SuggestionNotApproved failure event."""

    def test_all_factories(self):
        """All factory methods should create correct failure events."""
        suggestion_id = SuggestionId(value="sug_abc123")

        # not_found
        ev1 = SuggestionNotApproved.not_found(suggestion_id)
        assert ev1.event_type == "SUGGESTION_NOT_APPROVED/NOT_FOUND"
        assert ev1.suggestion_id == suggestion_id
        assert ev1.reason == "NOT_FOUND"
        assert "not found" in ev1.message

        # not_pending
        ev2 = SuggestionNotApproved.not_pending(suggestion_id, "rejected")
        assert ev2.event_type == "SUGGESTION_NOT_APPROVED/NOT_PENDING"
        assert ev2.suggestion_id == suggestion_id
        assert ev2.status == "rejected"
        assert ev2.reason == "NOT_PENDING"
        assert "rejected" in ev2.message

        # duplicate_name
        ev3 = SuggestionNotApproved.duplicate_name("Anxiety")
        assert ev3.event_type == "SUGGESTION_NOT_APPROVED/DUPLICATE_NAME"
        assert ev3.name == "Anxiety"
        assert "already exists" in ev3.message

        # invalid_name
        ev4 = SuggestionNotApproved.invalid_name("")
        assert ev4.event_type == "SUGGESTION_NOT_APPROVED/INVALID_NAME"
        assert ev4.name == ""
        assert "Invalid name" in ev4.message


class TestSuggestionNotRejected:
    """Tests for SuggestionNotRejected failure event."""

    def test_all_factories(self):
        """All factory methods should create correct failure events."""
        suggestion_id = SuggestionId(value="sug_xyz789")

        # not_found
        ev1 = SuggestionNotRejected.not_found(suggestion_id)
        assert ev1.event_type == "SUGGESTION_NOT_REJECTED/NOT_FOUND"
        assert ev1.suggestion_id == suggestion_id
        assert "not found" in ev1.message

        # not_pending
        ev2 = SuggestionNotRejected.not_pending(suggestion_id, "approved")
        assert ev2.event_type == "SUGGESTION_NOT_REJECTED/NOT_PENDING"
        assert ev2.suggestion_id == suggestion_id
        assert ev2.status == "approved"
        assert "approved" in ev2.message


# ============================================================
# Duplicate Detection Failure Events Tests
# ============================================================


class TestDuplicatesNotDetected:
    """Tests for DuplicatesNotDetected failure event."""

    def test_all_factories_and_properties(self):
        """All factory methods should create correct failure events with proper properties."""
        # invalid_threshold
        ev1 = DuplicatesNotDetected.invalid_threshold(1.5)
        assert ev1.event_type == "DUPLICATES_NOT_DETECTED/INVALID_THRESHOLD"
        assert ev1.threshold == 1.5
        assert ev1.reason == "INVALID_THRESHOLD"
        assert "0.0-1.0" in ev1.message
        assert ev1.is_failure is True

        # insufficient_codes
        ev2 = DuplicatesNotDetected.insufficient_codes(count=1, minimum=2)
        assert ev2.event_type == "DUPLICATES_NOT_DETECTED/INSUFFICIENT_CODES"
        assert ev2.count == 1
        assert ev2.minimum == 2
        assert ev2.reason == "INSUFFICIENT_CODES"
        assert "at least 2" in ev2.message


# ============================================================
# Merge Failure Events Tests
# ============================================================


class TestMergeNotCreated:
    """Tests for MergeNotCreated failure event."""

    def test_all_factories(self):
        """All factory methods should create correct failure events."""
        # code_not_found
        code_id = CodeId(value="42")
        ev1 = MergeNotCreated.code_not_found(code_id)
        assert ev1.event_type == "MERGE_NOT_CREATED/CODE_NOT_FOUND"
        assert ev1.code_id == code_id
        assert ev1.reason == "CODE_NOT_FOUND"
        assert "not found" in ev1.message

        # invalid_rationale
        ev2 = MergeNotCreated.invalid_rationale()
        assert ev2.event_type == "MERGE_NOT_CREATED/INVALID_RATIONALE"
        assert ev2.reason == "INVALID_RATIONALE"
        assert "1-1000 characters" in ev2.message


class TestMergeNotApproved:
    """Tests for MergeNotApproved failure event."""

    def test_all_factories(self):
        """All factory methods should create correct failure events."""
        code_id = CodeId(value="99")
        event = MergeNotApproved.code_not_found(code_id)

        assert event.event_type == "MERGE_NOT_APPROVED/CODE_NOT_FOUND"
        assert event.code_id == code_id
        assert event.reason == "CODE_NOT_FOUND"
        assert "not found" in event.message


class TestMergeNotDismissed:
    """Tests for MergeNotDismissed failure event."""

    def test_all_factories(self):
        """All factory methods should create correct failure events."""
        code_a_id = CodeId(value="1")
        code_b_id = CodeId(value="2")
        event = MergeNotDismissed.not_pending(code_a_id, code_b_id, "merged")

        assert event.event_type == "MERGE_NOT_DISMISSED/NOT_PENDING"
        assert event.code_a_id == code_a_id
        assert event.code_b_id == code_b_id
        assert event.status == "merged"
        assert event.reason == "NOT_PENDING"
        assert "merged" in event.message
        # Message should reference code IDs
        assert "1" in event.message or "2" in event.message
