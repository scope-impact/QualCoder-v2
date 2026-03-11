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

    @allure.title("CodeSuggestionApproved: handles modifications and defaults")
    def test_code_suggestion_approved(self):
        """create() tracks modifications and defaults modified to False."""
        assert CodeSuggestionApproved.event_type == "coding.ai_code_suggestion_approved"

        # Unmodified
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value="42"),
            original_name="Anxiety",
            final_name="Anxiety",
            modified=False,
        )
        assert event.original_name == "Anxiety"
        assert event.final_name == "Anxiety"
        assert event.modified is False

        # Modified
        event2 = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value="42"),
            original_name="Anxiety",
            final_name="General Anxiety",
            modified=True,
        )
        assert event2.modified is True

        # Default: modified=False
        event3 = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value="42"),
            original_name="Test",
            final_name="Test",
        )
        assert event3.modified is False

    @allure.title("CodeSuggestionRejected: reason handling and defaults")
    def test_code_suggestion_rejected(self):
        """create() stores reason, handles None, and defaults to None."""
        assert CodeSuggestionRejected.event_type == "coding.ai_code_suggestion_rejected"

        event = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Anxiety",
            reason="Too broad for this analysis",
        )
        assert event.reason == "Too broad for this analysis"

        event_none = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(), name="Test", reason=None,
        )
        assert event_none.reason is None

        event_default = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(), name="Test",
        )
        assert event_default.reason is None


# ============================================================
# Duplicate Detection Events Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestDuplicateDetectionEvents:
    """Tests for DuplicatesDetected, MergeSuggested, MergeSuggestionApproved, MergeSuggestionDismissed."""

    @allure.title("DuplicatesDetected: correct event type, candidates, and empty case")
    def test_duplicates_detected(self):
        """create() stores detection results; works with empty candidates."""
        assert DuplicatesDetected.event_type == "coding.ai_duplicates_detected"

        detection_id = DetectionId.new()
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value="1"), code_a_name="Anxiety",
            code_b_id=CodeId(value="2"), code_b_name="Anxiousness",
            similarity=SimilarityScore(value=0.92), rationale="Both codes refer to worry",
        )

        event = DuplicatesDetected.create(
            detection_id=detection_id, candidates=(candidate,),
            threshold=0.8, codes_analyzed=50,
        )
        assert event.detection_id == detection_id
        assert len(event.candidates) == 1
        assert event.candidates[0].code_a_name == "Anxiety"
        assert event.threshold == 0.8
        assert event.codes_analyzed == 50

        # Empty candidates
        event2 = DuplicatesDetected.create(
            detection_id=DetectionId.new(), candidates=(),
            threshold=0.9, codes_analyzed=10,
        )
        assert len(event2.candidates) == 0
        assert event2.codes_analyzed == 10

    @allure.title("MergeSuggested: correct event type and all fields")
    def test_merge_suggested(self):
        """create() stores merge suggestion details."""
        assert MergeSuggested.event_type == "coding.ai_merge_suggested"

        event = MergeSuggested.create(
            source_code_id=CodeId(value="1"), source_code_name="Anxiety",
            target_code_id=CodeId(value="2"), target_code_name="Worry",
            similarity=SimilarityScore(value=0.88),
            rationale="Both codes describe similar emotional states",
        )
        assert event.source_code_id.value == "1"
        assert event.target_code_name == "Worry"
        assert event.similarity == SimilarityScore(value=0.88)

    @allure.title("MergeSuggestionApproved: segments moved tracking")
    def test_merge_suggestion_approved(self):
        """create() tracks segments moved."""
        assert MergeSuggestionApproved.event_type == "coding.ai_merge_suggestion_approved"

        event = MergeSuggestionApproved.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            segments_moved=15,
        )
        assert event.source_code_id.value == "1"
        assert event.segments_moved == 15

    @allure.title("MergeSuggestionDismissed: reason handling and defaults")
    def test_merge_suggestion_dismissed(self):
        """create() stores reason, handles None, defaults to None."""
        assert MergeSuggestionDismissed.event_type == "coding.ai_merge_suggestion_dismissed"

        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason="Codes are conceptually different",
        )
        assert event.reason == "Codes are conceptually different"

        event_none = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
            reason=None,
        )
        assert event_none.reason is None

        event_default = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value="1"),
            target_code_id=CodeId(value="2"),
        )
        assert event_default.reason is None


# ============================================================
# Suggestion Failure Events Tests
# ============================================================


@allure.story("QC-028.08 Agent Suggest New Codes")
class TestSuggestionFailureEvents:
    """Tests for SuggestionNotCreated, SuggestionNotApproved, SuggestionNotRejected."""

    @allure.title("SuggestionNotCreated: all factory methods and properties")
    def test_suggestion_not_created(self):
        """All factory methods create correct failure events with proper properties."""
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

    @allure.title("SuggestionNotApproved: all factory methods")
    def test_suggestion_not_approved(self):
        """All factory methods create correct failure events."""
        suggestion_id = SuggestionId(value="sug_abc123")

        ev1 = SuggestionNotApproved.not_found(suggestion_id)
        assert ev1.event_type == "SUGGESTION_NOT_APPROVED/NOT_FOUND"
        assert "not found" in ev1.message

        ev2 = SuggestionNotApproved.not_pending(suggestion_id, "rejected")
        assert ev2.event_type == "SUGGESTION_NOT_APPROVED/NOT_PENDING"
        assert ev2.status == "rejected"
        assert "rejected" in ev2.message

        ev3 = SuggestionNotApproved.duplicate_name("Anxiety")
        assert ev3.event_type == "SUGGESTION_NOT_APPROVED/DUPLICATE_NAME"
        assert "already exists" in ev3.message

        ev4 = SuggestionNotApproved.invalid_name("")
        assert ev4.event_type == "SUGGESTION_NOT_APPROVED/INVALID_NAME"
        assert "Invalid name" in ev4.message

    @allure.title("SuggestionNotRejected: all factory methods")
    def test_suggestion_not_rejected(self):
        """All factory methods create correct failure events."""
        suggestion_id = SuggestionId(value="sug_xyz789")

        ev1 = SuggestionNotRejected.not_found(suggestion_id)
        assert ev1.event_type == "SUGGESTION_NOT_REJECTED/NOT_FOUND"
        assert "not found" in ev1.message

        ev2 = SuggestionNotRejected.not_pending(suggestion_id, "approved")
        assert ev2.event_type == "SUGGESTION_NOT_REJECTED/NOT_PENDING"
        assert ev2.status == "approved"
        assert "approved" in ev2.message


# ============================================================
# Duplicate Detection & Merge Failure Events Tests
# ============================================================


@allure.story("QC-028.09 Agent Detect Duplicates")
class TestDuplicateAndMergeFailureEvents:
    """Tests for DuplicatesNotDetected, MergeNotCreated, MergeNotApproved, MergeNotDismissed."""

    @allure.title("DuplicatesNotDetected: invalid threshold and insufficient codes")
    def test_duplicates_not_detected(self):
        """All factory methods create correct failure events."""
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

    @allure.title("MergeNotCreated, MergeNotApproved, MergeNotDismissed factories")
    def test_merge_failure_events(self):
        """All merge failure factory methods create correct events."""
        # MergeNotCreated
        code_id = CodeId(value="42")
        ev1 = MergeNotCreated.code_not_found(code_id)
        assert ev1.event_type == "MERGE_NOT_CREATED/CODE_NOT_FOUND"
        assert "not found" in ev1.message

        ev2 = MergeNotCreated.invalid_rationale()
        assert ev2.event_type == "MERGE_NOT_CREATED/INVALID_RATIONALE"
        assert "1-1000 characters" in ev2.message

        # MergeNotApproved
        ev3 = MergeNotApproved.code_not_found(CodeId(value="99"))
        assert ev3.event_type == "MERGE_NOT_APPROVED/CODE_NOT_FOUND"
        assert "not found" in ev3.message

        # MergeNotDismissed
        ev4 = MergeNotDismissed.not_pending(
            CodeId(value="1"), CodeId(value="2"), "merged",
        )
        assert ev4.event_type == "MERGE_NOT_DISMISSED/NOT_PENDING"
        assert ev4.status == "merged"
        assert "merged" in ev4.message
        assert "1" in ev4.message or "2" in ev4.message
