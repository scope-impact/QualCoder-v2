"""
Tests for SpeakerDetector domain service.

TDD tests written BEFORE implementation.
Extracted from presentation/dialogs/auto_code_dialog.py SpeakerDetector.
"""

from src.domain.sources.services.speaker_detector import (
    SpeakerDetector,
)


class TestSpeakerDetectorPatterns:
    """Tests for speaker pattern detection."""

    def test_detects_uppercase_speaker_pattern(self):
        """Should detect UPPERCASE NAME: pattern."""
        text = """INTERVIEWER: Hello, how are you?
PARTICIPANT: I'm doing well, thanks."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "INTERVIEWER" in names
        assert "PARTICIPANT" in names

    def test_detects_title_case_speaker_pattern(self):
        """Should detect Title Case Name: pattern."""
        text = """John Smith: I think that...
Jane Doe: That's interesting."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "John Smith" in names
        assert "Jane Doe" in names

    def test_detects_bracket_speaker_pattern(self):
        """Should detect [Speaker] pattern."""
        text = """[Moderator] Welcome everyone.
[Participant 1] Thanks for having me."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "Moderator" in names
        assert "Participant 1" in names

    def test_counts_speaker_occurrences(self):
        """Should count how many times each speaker appears."""
        text = """JOHN: First statement.
JANE: Response.
JOHN: Follow-up.
JOHN: Another point."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        john = next(s for s in speakers if s.name == "JOHN")
        jane = next(s for s in speakers if s.name == "JANE")
        assert john.count == 3
        assert jane.count == 1

    def test_handles_mixed_patterns(self):
        """Should handle different patterns in same text."""
        text = """FACILITATOR: Let's begin.
Dr. Johnson: I'd like to add...
[Observer] Noting the interaction."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        # Should detect at least the clear patterns
        assert len(speakers) >= 2


class TestSpeakerSegmentExtraction:
    """Tests for extracting speaker segments."""

    def test_extracts_segments_for_speaker(self):
        """Should extract all segments for a specific speaker."""
        text = """JOHN: This is my first point.
JANE: I disagree.
JOHN: Let me clarify."""
        detector = SpeakerDetector(text)

        segments = detector.get_speaker_segments("JOHN")

        assert len(segments) == 2

    def test_segment_has_correct_positions(self):
        """Segments should have correct start/end positions."""
        text = "SPEAKER: Hello world"
        detector = SpeakerDetector(text)

        segments = detector.get_speaker_segments("SPEAKER")

        assert len(segments) == 1
        segment = segments[0]
        assert segment.start >= 0
        assert segment.end <= len(text)
        assert segment.start < segment.end

    def test_segment_contains_text_after_speaker(self):
        """Segment text should be the content after speaker label."""
        text = "JOHN: This is the content."
        detector = SpeakerDetector(text)

        segments = detector.get_speaker_segments("JOHN")

        assert len(segments) == 1
        assert "This is the content" in segments[0].text

    def test_nonexistent_speaker_returns_empty(self):
        """Should return empty list for non-existent speaker."""
        text = "JOHN: Something."
        detector = SpeakerDetector(text)

        segments = detector.get_speaker_segments("JANE")

        assert segments == []


class TestSpeakerReturnTypes:
    """Tests for return value structures."""

    def test_speaker_has_name_and_count(self):
        """Speaker should have name and count attributes."""
        text = "JOHN: Hello"
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 1
        speaker = speakers[0]
        assert hasattr(speaker, "name")
        assert hasattr(speaker, "count")
        assert speaker.name == "JOHN"
        assert speaker.count == 1

    def test_segment_has_required_attributes(self):
        """SpeakerSegment should have start, end, text."""
        text = "JOHN: Content here"
        detector = SpeakerDetector(text)

        segments = detector.get_speaker_segments("JOHN")

        assert len(segments) == 1
        segment = segments[0]
        assert hasattr(segment, "start")
        assert hasattr(segment, "end")
        assert hasattr(segment, "text")


class TestSpeakerDetectorEdgeCases:
    """Tests for edge cases."""

    def test_empty_text_returns_empty_speakers(self):
        """Should handle empty text gracefully."""
        detector = SpeakerDetector("")

        speakers = detector.detect_speakers()

        assert speakers == []

    def test_no_speakers_in_text(self):
        """Should return empty when no speaker patterns found."""
        text = "This is just regular text without any speaker markers."
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert speakers == []

    def test_handles_blank_lines(self):
        """Should handle text with blank lines."""
        text = """JOHN: First line.

JANE: After blank line."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 2

    def test_speaker_at_start_of_line_only(self):
        """Should only match speakers at line start."""
        text = """This mentions JOHN: but not as speaker.
JANE: This is a real speaker."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        # Should only detect JANE as speaker (at line start)
        names = [s.name for s in speakers]
        assert "JANE" in names

    def test_colon_required_for_uppercase(self):
        """UPPERCASE without colon should not match."""
        text = """JOHN said something
JANE: This has a colon."""
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()

        names = [s.name for s in speakers]
        assert "JANE" in names
        # JOHN without colon is not detected as a speaker pattern


class TestSpeakerDetectorImmutability:
    """Tests verifying immutability and purity."""

    def test_detection_does_not_modify_text(self):
        """Detection should not modify original text."""
        original = "JOHN: Hello"
        text = original
        detector = SpeakerDetector(text)

        detector.detect_speakers()

        assert text == original

    def test_multiple_detections_consistent(self):
        """Multiple calls should return consistent results."""
        text = "JOHN: Hello\nJANE: Hi"
        detector = SpeakerDetector(text)

        speakers1 = detector.detect_speakers()
        speakers2 = detector.detect_speakers()

        assert len(speakers1) == len(speakers2)
        assert speakers1[0].name == speakers2[0].name
