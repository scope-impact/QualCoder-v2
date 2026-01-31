"""
Tests for Auto-Coding Payloads.

Verifies payloads carry correct data through factory methods.
"""

from src.application.coding.auto_coding_payloads import (
    AutoCodeBatchAppliedPayload,
    AutoCodeBatchUndonePayload,
    AutoCodeErrorPayload,
    MatchesFoundPayload,
    SpeakersDetectedPayload,
    SpeakerSegmentsPayload,
    TextMatchPayload,
)


class TestTextMatchPayload:
    """Tests for TextMatchPayload."""

    def test_length_property(self):
        """Payload stores positions and computes length correctly."""
        payload = TextMatchPayload(start=10, end=25)
        assert payload.start == 10
        assert payload.end == 25
        assert payload.length == 15


class TestMatchesFoundPayload:
    """Tests for MatchesFoundPayload."""

    def test_from_matches_factory(self):
        """Factory method creates payload correctly."""
        matches = [(0, 5), (10, 15), (20, 25)]

        payload = MatchesFoundPayload.from_matches(
            pattern="test",
            match_type="exact",
            scope="all",
            matches=matches,
        )

        assert payload.pattern == "test"
        assert payload.match_type == "exact"
        assert payload.scope == "all"
        assert payload.total_count == 3
        assert len(payload.matches) == 3
        assert payload.matches[0].start == 0
        assert payload.matches[1].end == 15
        assert payload.timestamp is not None


class TestSpeakersDetectedPayload:
    """Tests for SpeakersDetectedPayload."""

    def test_from_speakers_factory(self):
        """Factory method creates payload correctly."""
        speakers = [
            {"name": "INTERVIEWER", "count": 5},
            {"name": "PARTICIPANT", "count": 3},
        ]

        payload = SpeakersDetectedPayload.from_speakers(speakers)

        assert payload.total_count == 2
        assert payload.speakers[0].name == "INTERVIEWER"
        assert payload.speakers[0].count == 5
        assert payload.speakers[1].name == "PARTICIPANT"


class TestSpeakerSegmentsPayload:
    """Tests for SpeakerSegmentsPayload."""

    def test_from_segments_factory(self):
        """Factory method creates payload correctly."""
        segments = [
            {"start": 0, "end": 20, "text": "First segment"},
            {"start": 50, "end": 80, "text": "Second segment"},
        ]

        payload = SpeakerSegmentsPayload.from_segments(
            speaker_name="JOHN",
            segments=segments,
        )

        assert payload.speaker_name == "JOHN"
        assert payload.total_count == 2
        assert payload.segments[0].text == "First segment"


class TestAutoCodeBatchAppliedPayload:
    """Tests for AutoCodeBatchAppliedPayload."""

    def test_from_result_factory(self):
        """Factory method creates payload correctly."""
        payload = AutoCodeBatchAppliedPayload.from_result(
            batch_id="batch_123",
            code_id=1,
            code_name="Theme: Identity",
            pattern="identity",
            segment_count=5,
        )

        assert payload.batch_id == "batch_123"
        assert payload.code_id == 1
        assert payload.code_name == "Theme: Identity"
        assert payload.pattern == "identity"
        assert payload.segment_count == 5
        assert payload.can_undo is True

    def test_can_undo_false_for_empty_batch(self):
        """Cannot undo empty batch."""
        payload = AutoCodeBatchAppliedPayload.from_result(
            batch_id="batch_123",
            code_id=1,
            code_name="Test",
            pattern="test",
            segment_count=0,
        )
        assert payload.can_undo is False


class TestAutoCodeBatchUndonePayload:
    """Tests for AutoCodeBatchUndonePayload."""

    def test_from_result_factory(self):
        """Factory method creates payload correctly."""
        payload = AutoCodeBatchUndonePayload.from_result(
            batch_id="batch_123",
            segments_removed=3,
        )

        assert payload.batch_id == "batch_123"
        assert payload.segments_removed == 3


class TestAutoCodeErrorPayload:
    """Tests for AutoCodeErrorPayload."""

    def test_from_error_factory(self):
        """Factory method creates payload correctly."""
        payload = AutoCodeErrorPayload.from_error(
            operation="find_matches",
            error_message="Invalid regex pattern",
            error_code="INVALID_REGEX",
        )

        assert payload.operation == "find_matches"
        assert payload.error_message == "Invalid regex pattern"
        assert payload.error_code == "INVALID_REGEX"

    def test_error_code_optional(self):
        """Error code is optional."""
        payload = AutoCodeErrorPayload.from_error(
            operation="apply_batch",
            error_message="Unknown error",
        )
        assert payload.error_code is None
