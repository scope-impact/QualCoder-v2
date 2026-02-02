"""
Tests for AutoCodingController - Application Service.

TDD tests written BEFORE implementation.
Controller orchestrates auto-coding operations following fDDD architecture:
- Receives commands from presentation layer
- Calls domain services (TextMatcher, SpeakerDetector)
- Uses BatchManager for batch operations
- Publishes domain events
"""

from unittest.mock import Mock

from returns.result import Failure, Success

from src.contexts.coding.core.services.text_matcher import MatchScope, MatchType
from src.contexts.shared.core.types import CodeId, SourceId


class TestFindMatches:
    """Tests for finding text matches via controller."""

    def test_find_matches_returns_match_positions(self):
        """Controller should return match positions using domain service."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "The cat sat on the mat. The cat was happy."
        result = controller.find_matches(
            text=text,
            pattern="cat",
            match_type=MatchType.EXACT,
            scope=MatchScope.ALL,
        )

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 2
        assert matches[0].start == 4
        assert matches[0].end == 7
        assert matches[1].start == 28
        assert matches[1].end == 31

    def test_find_matches_respects_scope_first(self):
        """Controller should respect FIRST scope."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "word word word"
        result = controller.find_matches(
            text=text,
            pattern="word",
            match_type=MatchType.EXACT,
            scope=MatchScope.FIRST,
        )

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 1
        assert matches[0].start == 0

    def test_find_matches_respects_scope_last(self):
        """Controller should respect LAST scope."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "word word word"
        result = controller.find_matches(
            text=text,
            pattern="word",
            match_type=MatchType.EXACT,
            scope=MatchScope.LAST,
        )

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 1
        assert matches[0].start == 10

    def test_find_matches_regex_mode(self):
        """Controller should support regex matching."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "Email: test@example.com and info@test.org"
        result = controller.find_matches(
            text=text,
            pattern=r"\S+@\S+\.\w+",
            match_type=MatchType.REGEX,
            scope=MatchScope.ALL,
        )

        assert isinstance(result, Success)
        matches = result.unwrap()
        assert len(matches) == 2

    def test_find_matches_empty_pattern_returns_failure(self):
        """Controller should fail gracefully with empty pattern."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        result = controller.find_matches(
            text="some text",
            pattern="",
            match_type=MatchType.EXACT,
            scope=MatchScope.ALL,
        )

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 0

    def test_find_matches_no_matches_returns_empty_list(self):
        """Controller should return empty list when no matches found."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        result = controller.find_matches(
            text="hello world",
            pattern="xyz",
            match_type=MatchType.EXACT,
            scope=MatchScope.ALL,
        )

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 0


class TestDetectSpeakers:
    """Tests for speaker detection via controller."""

    def test_detect_speakers_finds_uppercase_pattern(self):
        """Controller should detect UPPERCASE: speaker pattern."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = """
INTERVIEWER: How are you today?
PARTICIPANT: I'm doing well, thank you.
INTERVIEWER: Can you tell me about your experience?
"""
        result = controller.detect_speakers(text)

        assert isinstance(result, Success)
        speakers = result.unwrap()
        assert len(speakers) >= 2

        speaker_names = [s.name for s in speakers]
        assert "INTERVIEWER" in speaker_names
        assert "PARTICIPANT" in speaker_names

    def test_detect_speakers_counts_occurrences(self):
        """Controller should count speaker occurrences."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = """
SPEAKER A: First line.
SPEAKER B: Second line.
SPEAKER A: Third line.
SPEAKER A: Fourth line.
"""
        result = controller.detect_speakers(text)

        assert isinstance(result, Success)
        speakers = result.unwrap()

        speaker_a = next((s for s in speakers if s.name == "SPEAKER A"), None)
        assert speaker_a is not None
        assert speaker_a.count == 3

    def test_detect_speakers_empty_text_returns_empty(self):
        """Controller should return empty list for empty text."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        result = controller.detect_speakers("")

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 0


class TestGetSpeakerSegments:
    """Tests for getting segments by speaker."""

    def test_get_speaker_segments_returns_segments(self):
        """Controller should return segments for specific speaker."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = """SPEAKER A: First statement.
SPEAKER B: Second statement.
SPEAKER A: Third statement."""

        result = controller.get_speaker_segments(text, "SPEAKER A")

        assert isinstance(result, Success)
        segments = result.unwrap()
        assert len(segments) == 2

    def test_get_speaker_segments_includes_positions(self):
        """Segments should include start/end positions."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "JOHN: Hello there."
        result = controller.get_speaker_segments(text, "JOHN")

        assert isinstance(result, Success)
        segments = result.unwrap()
        assert len(segments) == 1
        assert hasattr(segments[0], "start")
        assert hasattr(segments[0], "end")
        assert segments[0].start >= 0

    def test_get_speaker_segments_nonexistent_speaker(self):
        """Controller should return empty for nonexistent speaker."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        text = "ALICE: Some text."
        result = controller.get_speaker_segments(text, "BOB")

        assert isinstance(result, Success)
        assert len(result.unwrap()) == 0


class TestApplyAutoCodeBatch:
    """Tests for applying auto-code to multiple matches."""

    def test_apply_auto_code_batch_creates_segments(self):
        """Controller should create segments for all matches."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.contexts.coding.core.services.text_matcher import TextMatch

        # Mock segment repository
        segment_repo = Mock()
        segment_repo.save = Mock()

        # Mock event bus
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        matches = [
            TextMatch(start=0, end=5),
            TextMatch(start=10, end=15),
            TextMatch(start=20, end=25),
        ]

        result = controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=matches,
        )

        assert isinstance(result, Success)
        batch = result.unwrap()
        assert batch.segment_count == 3

    def test_apply_auto_code_batch_creates_batch_record(self):
        """Controller should create batch record for undo."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.contexts.coding.core.services.text_matcher import TextMatch

        segment_repo = Mock()
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        matches = [TextMatch(start=0, end=5)]

        result = controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=matches,
        )

        assert isinstance(result, Success)
        batch = result.unwrap()
        assert batch.batch_id is not None
        assert batch.pattern == "test"

    def test_apply_auto_code_batch_publishes_event(self):
        """Controller should publish BatchCreated event."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.contexts.coding.core.services.text_matcher import TextMatch

        segment_repo = Mock()
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        matches = [TextMatch(start=0, end=5)]

        controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=matches,
        )

        # Verify event was published
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert published_event.pattern == "test"

    def test_apply_auto_code_batch_empty_matches_returns_empty_batch(self):
        """Controller should handle empty matches gracefully."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        segment_repo = Mock()
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        result = controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=[],
        )

        assert isinstance(result, Success)
        batch = result.unwrap()
        assert batch.segment_count == 0


class TestUndoLastBatch:
    """Tests for undoing the last auto-code batch."""

    def test_undo_last_batch_removes_segments(self):
        """Controller should remove segments from last batch."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.contexts.coding.core.services.text_matcher import TextMatch

        segment_repo = Mock()
        segment_repo.delete = Mock()
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # First create a batch
        matches = [TextMatch(start=0, end=5), TextMatch(start=10, end=15)]
        controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=matches,
        )

        # Then undo it
        result = controller.undo_last_batch()

        assert isinstance(result, Success)
        undone = result.unwrap()
        assert undone.segment_count == 2
        # Verify segments were deleted
        assert segment_repo.delete.call_count == 2

    def test_undo_last_batch_publishes_event(self):
        """Controller should publish BatchUndone event."""
        from src.application.coding.auto_coding_controller import AutoCodingController
        from src.contexts.coding.core.services.text_matcher import TextMatch

        segment_repo = Mock()
        event_bus = Mock()

        controller = AutoCodingController(
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # Create and undo batch
        matches = [TextMatch(start=0, end=5)]
        controller.apply_auto_code_batch(
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            pattern="test",
            matches=matches,
        )
        event_bus.reset_mock()

        controller.undo_last_batch()

        event_bus.publish.assert_called_once()

    def test_undo_last_batch_nothing_to_undo(self):
        """Controller should return failure when nothing to undo."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        result = controller.undo_last_batch()

        assert isinstance(result, Failure)


class TestControllerImmutability:
    """Tests verifying controller doesn't mutate inputs."""

    def test_find_matches_does_not_mutate_text(self):
        """Controller should not modify input text."""
        from src.application.coding.auto_coding_controller import AutoCodingController

        controller = AutoCodingController()

        original_text = "hello world"
        text_copy = original_text

        controller.find_matches(
            text=text_copy,
            pattern="hello",
            match_type=MatchType.EXACT,
            scope=MatchScope.ALL,
        )

        assert text_copy == original_text
