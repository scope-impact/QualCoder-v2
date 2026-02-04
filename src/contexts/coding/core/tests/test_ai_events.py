"""
Tests for AI-Assisted Coding Events and Failure Events.

Tests for:
- Code Suggestion Events (CodeSuggested, CodeSuggestionApproved, CodeSuggestionRejected)
- Duplicate Detection Events (DuplicatesDetected, MergeSuggested, MergeSuggestionApproved, MergeSuggestionDismissed)
- Suggestion Failure Events (SuggestionNotCreated, SuggestionNotApproved, SuggestionNotRejected)
- Duplicate Detection Failure Events (DuplicatesNotDetected)
- Merge Failure Events (MergeNotCreated, MergeNotApproved, MergeNotDismissed)
"""

import pytest

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

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert CodeSuggested.event_type == "coding.ai_code_suggested"

    def test_create_with_all_fields(self):
        """create() should generate event with all fields populated."""
        suggestion_id = SuggestionId.new()
        color = Color(red=255, green=100, blue=50)
        context = TextContext(
            text="Sample text for analysis",
            source_id=SourceId(value=1),
            position=TextPosition(start=0, end=24),
        )
        source_id = SourceId(value=1)

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
        source_id = SourceId(value=1)

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

    def test_immutability(self):
        """CodeSuggested should be immutable (frozen dataclass)."""
        event = CodeSuggested.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
            color=Color(red=100, green=100, blue=100),
            rationale="Test",
            contexts=(),
            confidence=0.5,
            source_id=SourceId(value=1),
        )

        with pytest.raises(AttributeError):
            event.name = "Changed"  # type: ignore


class TestCodeSuggestionApproved:
    """Tests for CodeSuggestionApproved domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert CodeSuggestionApproved.event_type == "coding.ai_code_suggestion_approved"

    def test_create_without_modification(self):
        """create() should handle unmodified approvals."""
        suggestion_id = SuggestionId.new()
        code_id = CodeId(value=42)

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

    def test_create_with_modification(self):
        """create() should track when researcher modified the suggestion."""
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value=42),
            original_name="Anxiety",
            final_name="General Anxiety",
            modified=True,
        )

        assert event.original_name == "Anxiety"
        assert event.final_name == "General Anxiety"
        assert event.modified is True

    def test_modified_defaults_to_false(self):
        """modified parameter should default to False."""
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value=42),
            original_name="Test",
            final_name="Test",
        )

        assert event.modified is False

    def test_immutability(self):
        """CodeSuggestionApproved should be immutable."""
        event = CodeSuggestionApproved.create(
            suggestion_id=SuggestionId.new(),
            created_code_id=CodeId(value=42),
            original_name="Test",
            final_name="Test",
        )

        with pytest.raises(AttributeError):
            event.modified = True  # type: ignore


class TestCodeSuggestionRejected:
    """Tests for CodeSuggestionRejected domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert CodeSuggestionRejected.event_type == "coding.ai_code_suggestion_rejected"

    def test_create_with_reason(self):
        """create() should store rejection reason."""
        suggestion_id = SuggestionId.new()

        event = CodeSuggestionRejected.create(
            suggestion_id=suggestion_id,
            name="Anxiety",
            reason="Too broad for this analysis",
        )

        assert event.suggestion_id == suggestion_id
        assert event.name == "Anxiety"
        assert event.reason == "Too broad for this analysis"

    def test_create_without_reason(self):
        """create() should work without a reason."""
        event = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
            reason=None,
        )

        assert event.reason is None

    def test_reason_defaults_to_none(self):
        """reason parameter should default to None."""
        event = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
        )

        assert event.reason is None

    def test_immutability(self):
        """CodeSuggestionRejected should be immutable."""
        event = CodeSuggestionRejected.create(
            suggestion_id=SuggestionId.new(),
            name="Test",
        )

        with pytest.raises(AttributeError):
            event.reason = "Changed"  # type: ignore


# ============================================================
# Duplicate Detection Events Tests
# ============================================================


class TestDuplicatesDetected:
    """Tests for DuplicatesDetected domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert DuplicatesDetected.event_type == "coding.ai_duplicates_detected"

    def test_create_with_candidates(self):
        """create() should store detection results."""
        detection_id = DetectionId.new()
        candidate = DuplicateCandidate(
            code_a_id=CodeId(value=1),
            code_a_name="Anxiety",
            code_b_id=CodeId(value=2),
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

    def test_immutability(self):
        """DuplicatesDetected should be immutable."""
        event = DuplicatesDetected.create(
            detection_id=DetectionId.new(),
            candidates=(),
            threshold=0.8,
            codes_analyzed=10,
        )

        with pytest.raises(AttributeError):
            event.threshold = 0.5  # type: ignore


class TestMergeSuggested:
    """Tests for MergeSuggested domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert MergeSuggested.event_type == "coding.ai_merge_suggested"

    def test_create_with_all_fields(self):
        """create() should store merge suggestion details."""
        source_code_id = CodeId(value=1)
        target_code_id = CodeId(value=2)
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

    def test_immutability(self):
        """MergeSuggested should be immutable."""
        event = MergeSuggested.create(
            source_code_id=CodeId(value=1),
            source_code_name="A",
            target_code_id=CodeId(value=2),
            target_code_name="B",
            similarity=SimilarityScore(value=0.8),
            rationale="Test",
        )

        with pytest.raises(AttributeError):
            event.rationale = "Changed"  # type: ignore


class TestMergeSuggestionApproved:
    """Tests for MergeSuggestionApproved domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert (
            MergeSuggestionApproved.event_type == "coding.ai_merge_suggestion_approved"
        )

    def test_create_with_segment_count(self):
        """create() should track segments moved."""
        source_code_id = CodeId(value=1)
        target_code_id = CodeId(value=2)

        event = MergeSuggestionApproved.create(
            source_code_id=source_code_id,
            target_code_id=target_code_id,
            segments_moved=15,
        )

        assert event.source_code_id == source_code_id
        assert event.target_code_id == target_code_id
        assert event.segments_moved == 15

    def test_immutability(self):
        """MergeSuggestionApproved should be immutable."""
        event = MergeSuggestionApproved.create(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            segments_moved=5,
        )

        with pytest.raises(AttributeError):
            event.segments_moved = 10  # type: ignore


class TestMergeSuggestionDismissed:
    """Tests for MergeSuggestionDismissed domain event."""

    def test_event_type_is_correct(self):
        """Event type should follow naming convention."""
        assert (
            MergeSuggestionDismissed.event_type
            == "coding.ai_merge_suggestion_dismissed"
        )

    def test_create_with_reason(self):
        """create() should store dismissal reason."""
        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason="Codes are conceptually different",
        )

        assert event.source_code_id.value == 1
        assert event.target_code_id.value == 2
        assert event.reason == "Codes are conceptually different"

    def test_create_without_reason(self):
        """create() should work without a reason."""
        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
            reason=None,
        )

        assert event.reason is None

    def test_reason_defaults_to_none(self):
        """reason parameter should default to None."""
        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
        )

        assert event.reason is None

    def test_immutability(self):
        """MergeSuggestionDismissed should be immutable."""
        event = MergeSuggestionDismissed.create(
            source_code_id=CodeId(value=1),
            target_code_id=CodeId(value=2),
        )

        with pytest.raises(AttributeError):
            event.reason = "Changed"  # type: ignore


# ============================================================
# Suggestion Failure Events Tests
# ============================================================


class TestSuggestionNotCreated:
    """Tests for SuggestionNotCreated failure event."""

    def test_invalid_name_factory(self):
        """invalid_name() should create correct failure event."""
        event = SuggestionNotCreated.invalid_name("  ")

        assert event.event_type == "SUGGESTION_NOT_CREATED/INVALID_NAME"
        assert event.name == "  "
        assert event.reason == "INVALID_NAME"
        assert "Invalid suggestion name" in event.message

    def test_duplicate_name_factory(self):
        """duplicate_name() should create correct failure event."""
        event = SuggestionNotCreated.duplicate_name("Anxiety")

        assert event.event_type == "SUGGESTION_NOT_CREATED/DUPLICATE_NAME"
        assert event.name == "Anxiety"
        assert event.reason == "DUPLICATE_NAME"
        assert "already exists" in event.message

    def test_invalid_confidence_factory(self):
        """invalid_confidence() should create correct failure event."""
        event = SuggestionNotCreated.invalid_confidence(1.5)

        assert event.event_type == "SUGGESTION_NOT_CREATED/INVALID_CONFIDENCE"
        assert event.confidence == 1.5
        assert event.reason == "INVALID_CONFIDENCE"
        assert "0.0-1.0" in event.message

    def test_invalid_rationale_factory(self):
        """invalid_rationale() should create correct failure event."""
        event = SuggestionNotCreated.invalid_rationale()

        assert event.event_type == "SUGGESTION_NOT_CREATED/INVALID_RATIONALE"
        assert event.reason == "INVALID_RATIONALE"
        assert "1-1000 characters" in event.message

    def test_is_failure_property(self):
        """is_failure should always return True."""
        event = SuggestionNotCreated.invalid_name("test")
        assert event.is_failure is True

    def test_operation_property(self):
        """operation should extract operation from event_type."""
        event = SuggestionNotCreated.invalid_name("test")
        assert event.operation == "SUGGESTION_NOT_CREATED"

    def test_immutability(self):
        """SuggestionNotCreated should be immutable."""
        event = SuggestionNotCreated.invalid_name("test")

        with pytest.raises(AttributeError):
            event.name = "changed"  # type: ignore


class TestSuggestionNotApproved:
    """Tests for SuggestionNotApproved failure event."""

    def test_not_found_factory(self):
        """not_found() should create correct failure event."""
        suggestion_id = SuggestionId(value="sug_abc123")
        event = SuggestionNotApproved.not_found(suggestion_id)

        assert event.event_type == "SUGGESTION_NOT_APPROVED/NOT_FOUND"
        assert event.suggestion_id == suggestion_id
        assert event.reason == "NOT_FOUND"
        assert "not found" in event.message

    def test_not_pending_factory(self):
        """not_pending() should create correct failure event."""
        suggestion_id = SuggestionId(value="sug_abc123")
        event = SuggestionNotApproved.not_pending(suggestion_id, "rejected")

        assert event.event_type == "SUGGESTION_NOT_APPROVED/NOT_PENDING"
        assert event.suggestion_id == suggestion_id
        assert event.status == "rejected"
        assert event.reason == "NOT_PENDING"
        assert "rejected" in event.message

    def test_duplicate_name_factory(self):
        """duplicate_name() should create correct failure event."""
        event = SuggestionNotApproved.duplicate_name("Anxiety")

        assert event.event_type == "SUGGESTION_NOT_APPROVED/DUPLICATE_NAME"
        assert event.name == "Anxiety"
        assert "already exists" in event.message

    def test_invalid_name_factory(self):
        """invalid_name() should create correct failure event."""
        event = SuggestionNotApproved.invalid_name("")

        assert event.event_type == "SUGGESTION_NOT_APPROVED/INVALID_NAME"
        assert event.name == ""
        assert "Invalid name" in event.message

    def test_immutability(self):
        """SuggestionNotApproved should be immutable."""
        event = SuggestionNotApproved.not_found(SuggestionId.new())

        with pytest.raises(AttributeError):
            event.status = "changed"  # type: ignore


class TestSuggestionNotRejected:
    """Tests for SuggestionNotRejected failure event."""

    def test_not_found_factory(self):
        """not_found() should create correct failure event."""
        suggestion_id = SuggestionId(value="sug_xyz789")
        event = SuggestionNotRejected.not_found(suggestion_id)

        assert event.event_type == "SUGGESTION_NOT_REJECTED/NOT_FOUND"
        assert event.suggestion_id == suggestion_id
        assert "not found" in event.message

    def test_not_pending_factory(self):
        """not_pending() should create correct failure event."""
        suggestion_id = SuggestionId(value="sug_xyz789")
        event = SuggestionNotRejected.not_pending(suggestion_id, "approved")

        assert event.event_type == "SUGGESTION_NOT_REJECTED/NOT_PENDING"
        assert event.suggestion_id == suggestion_id
        assert event.status == "approved"
        assert "approved" in event.message

    def test_immutability(self):
        """SuggestionNotRejected should be immutable."""
        event = SuggestionNotRejected.not_found(SuggestionId.new())

        with pytest.raises(AttributeError):
            event.suggestion_id = SuggestionId.new()  # type: ignore


# ============================================================
# Duplicate Detection Failure Events Tests
# ============================================================


class TestDuplicatesNotDetected:
    """Tests for DuplicatesNotDetected failure event."""

    def test_invalid_threshold_factory(self):
        """invalid_threshold() should create correct failure event."""
        event = DuplicatesNotDetected.invalid_threshold(1.5)

        assert event.event_type == "DUPLICATES_NOT_DETECTED/INVALID_THRESHOLD"
        assert event.threshold == 1.5
        assert event.reason == "INVALID_THRESHOLD"
        assert "0.0-1.0" in event.message

    def test_insufficient_codes_factory(self):
        """insufficient_codes() should create correct failure event."""
        event = DuplicatesNotDetected.insufficient_codes(count=1, minimum=2)

        assert event.event_type == "DUPLICATES_NOT_DETECTED/INSUFFICIENT_CODES"
        assert event.count == 1
        assert event.minimum == 2
        assert event.reason == "INSUFFICIENT_CODES"
        assert "at least 2" in event.message

    def test_is_failure_property(self):
        """is_failure should always return True."""
        event = DuplicatesNotDetected.invalid_threshold(0.5)
        assert event.is_failure is True

    def test_immutability(self):
        """DuplicatesNotDetected should be immutable."""
        event = DuplicatesNotDetected.invalid_threshold(1.5)

        with pytest.raises(AttributeError):
            event.threshold = 0.8  # type: ignore


# ============================================================
# Merge Failure Events Tests
# ============================================================


class TestMergeNotCreated:
    """Tests for MergeNotCreated failure event."""

    def test_code_not_found_factory(self):
        """code_not_found() should create correct failure event."""
        code_id = CodeId(value=42)
        event = MergeNotCreated.code_not_found(code_id)

        assert event.event_type == "MERGE_NOT_CREATED/CODE_NOT_FOUND"
        assert event.code_id == code_id
        assert event.reason == "CODE_NOT_FOUND"
        assert "not found" in event.message

    def test_invalid_rationale_factory(self):
        """invalid_rationale() should create correct failure event."""
        event = MergeNotCreated.invalid_rationale()

        assert event.event_type == "MERGE_NOT_CREATED/INVALID_RATIONALE"
        assert event.reason == "INVALID_RATIONALE"
        assert "1-1000 characters" in event.message

    def test_immutability(self):
        """MergeNotCreated should be immutable."""
        event = MergeNotCreated.code_not_found(CodeId(value=1))

        with pytest.raises(AttributeError):
            event.code_id = CodeId(value=2)  # type: ignore


class TestMergeNotApproved:
    """Tests for MergeNotApproved failure event."""

    def test_code_not_found_factory(self):
        """code_not_found() should create correct failure event."""
        code_id = CodeId(value=99)
        event = MergeNotApproved.code_not_found(code_id)

        assert event.event_type == "MERGE_NOT_APPROVED/CODE_NOT_FOUND"
        assert event.code_id == code_id
        assert event.reason == "CODE_NOT_FOUND"
        assert "not found" in event.message

    def test_immutability(self):
        """MergeNotApproved should be immutable."""
        event = MergeNotApproved.code_not_found(CodeId(value=1))

        with pytest.raises(AttributeError):
            event.code_id = CodeId(value=2)  # type: ignore


class TestMergeNotDismissed:
    """Tests for MergeNotDismissed failure event."""

    def test_not_pending_factory(self):
        """not_pending() should create correct failure event."""
        code_a_id = CodeId(value=1)
        code_b_id = CodeId(value=2)
        event = MergeNotDismissed.not_pending(code_a_id, code_b_id, "merged")

        assert event.event_type == "MERGE_NOT_DISMISSED/NOT_PENDING"
        assert event.code_a_id == code_a_id
        assert event.code_b_id == code_b_id
        assert event.status == "merged"
        assert event.reason == "NOT_PENDING"
        assert "merged" in event.message

    def test_message_includes_both_code_ids(self):
        """Message should reference both code IDs."""
        event = MergeNotDismissed.not_pending(
            CodeId(value=10),
            CodeId(value=20),
            "dismissed",
        )

        assert "10" in event.message or "20" in event.message

    def test_immutability(self):
        """MergeNotDismissed should be immutable."""
        event = MergeNotDismissed.not_pending(
            CodeId(value=1),
            CodeId(value=2),
            "merged",
        )

        with pytest.raises(AttributeError):
            event.status = "pending"  # type: ignore
