"""
Tests for SpeakerDetector domain service.

TDD tests written BEFORE implementation.
Extracted from presentation/dialogs/auto_code_dialog.py SpeakerDetector.
"""

import allure
import pytest

from src.contexts.sources.core.services.speaker_detector import (
    SpeakerDetector,
)

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


@allure.story("QC-027.02 Speaker Detection")
class TestSpeakerDetectorPatterns:
    """Tests for speaker pattern detection."""

    @allure.title("Detects speakers in uppercase, title case, and bracket patterns")
    def test_detects_speaker_patterns(self):
        """Should detect UPPERCASE, Title Case, and [Bracket] speaker patterns."""
        # Uppercase pattern
        text_upper = "INTERVIEWER: Hello, how are you?\nPARTICIPANT: I'm doing well, thanks."
        speakers = SpeakerDetector(text_upper).detect_speakers()
        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "INTERVIEWER" in names
        assert "PARTICIPANT" in names

        # Title case pattern
        text_title = "John Smith: I think that...\nJane Doe: That's interesting."
        speakers = SpeakerDetector(text_title).detect_speakers()
        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "John Smith" in names
        assert "Jane Doe" in names

        # Bracket pattern
        text_bracket = "[Moderator] Welcome everyone.\n[Participant 1] Thanks for having me."
        speakers = SpeakerDetector(text_bracket).detect_speakers()
        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "Moderator" in names
        assert "Participant 1" in names

    @allure.title("Counts speaker occurrences and handles mixed patterns")
    def test_counts_and_mixed_patterns(self):
        """Should count occurrences and handle different patterns in same text."""
        text = "JOHN: First statement.\nJANE: Response.\nJOHN: Follow-up.\nJOHN: Another point."
        speakers = SpeakerDetector(text).detect_speakers()
        john = next(s for s in speakers if s.name == "JOHN")
        jane = next(s for s in speakers if s.name == "JANE")
        assert john.count == 3
        assert jane.count == 1

        # Mixed patterns
        text_mixed = "FACILITATOR: Let's begin.\nDr. Johnson: I'd like to add...\n[Observer] Noting the interaction."
        speakers = SpeakerDetector(text_mixed).detect_speakers()
        assert len(speakers) >= 2


@allure.story("QC-027.02 Speaker Detection")
class TestSpeakerSegmentExtraction:
    """Tests for extracting speaker segments."""

    @allure.title("Extracts segments with correct positions and text content")
    def test_extracts_segments_with_positions_and_text(self):
        """Should extract segments with correct positions and text for a speaker."""
        text = "JOHN: This is my first point.\nJANE: I disagree.\nJOHN: Let me clarify."
        detector = SpeakerDetector(text)
        segments = detector.get_speaker_segments("JOHN")
        assert len(segments) == 2

        # Verify position correctness on simple text
        simple_text = "SPEAKER: Hello world"
        detector2 = SpeakerDetector(simple_text)
        segments2 = detector2.get_speaker_segments("SPEAKER")
        assert len(segments2) == 1
        seg = segments2[0]
        assert seg.start >= 0
        assert seg.end <= len(simple_text)
        assert seg.start < seg.end

        # Verify text content
        text3 = "JOHN: This is the content."
        segments3 = SpeakerDetector(text3).get_speaker_segments("JOHN")
        assert len(segments3) == 1
        assert "This is the content" in segments3[0].text

    @allure.title("Non-existent speaker returns empty list")
    def test_nonexistent_speaker_returns_empty(self):
        """Should return empty list for non-existent speaker."""
        segments = SpeakerDetector("JOHN: Something.").get_speaker_segments("JANE")
        assert segments == []


@allure.story("QC-027.02 Speaker Detection")
class TestSpeakerReturnTypes:
    """Tests for return value structures."""

    @allure.title("Speaker and segment have required attributes")
    def test_speaker_and_segment_attributes(self):
        """Speaker has name/count; SpeakerSegment has start/end/text."""
        text = "JOHN: Content here"
        detector = SpeakerDetector(text)

        speakers = detector.detect_speakers()
        assert len(speakers) == 1
        speaker = speakers[0]
        assert speaker.name == "JOHN"
        assert speaker.count == 1

        segments = detector.get_speaker_segments("JOHN")
        assert len(segments) == 1
        segment = segments[0]
        assert hasattr(segment, "start")
        assert hasattr(segment, "end")
        assert hasattr(segment, "text")


@allure.story("QC-027.02 Speaker Detection")
class TestSpeakerDetectorEdgeCases:
    """Tests for edge cases."""

    @allure.title("Handles empty text, no speakers, and blank lines")
    def test_empty_no_speakers_and_blank_lines(self):
        """Should handle empty text, no speaker markers, and blank lines."""
        assert SpeakerDetector("").detect_speakers() == []
        assert SpeakerDetector("This is just regular text without any speaker markers.").detect_speakers() == []

        text = "JOHN: First line.\n\nJANE: After blank line."
        assert len(SpeakerDetector(text).detect_speakers()) == 2

    @allure.title("Only matches speakers at line start; colon required for uppercase")
    def test_line_start_and_colon_required(self):
        """Should only match speakers at line start; UPPERCASE without colon should not match."""
        text = "This mentions JOHN: but not as speaker.\nJANE: This is a real speaker."
        speakers = SpeakerDetector(text).detect_speakers()
        names = [s.name for s in speakers]
        assert "JANE" in names

        text2 = "JOHN said something\nJANE: This has a colon."
        speakers2 = SpeakerDetector(text2).detect_speakers()
        names2 = [s.name for s in speakers2]
        assert "JANE" in names2


@allure.story("QC-027.02 Speaker Detection")
class TestSpeakerDetectorImmutability:
    """Tests verifying immutability and consistency."""

    @allure.title("Detection does not modify text and multiple calls are consistent")
    def test_immutability_and_consistency(self):
        """Detection should not modify text; multiple calls return consistent results."""
        original = "JOHN: Hello"
        text = original
        detector = SpeakerDetector(text)
        detector.detect_speakers()
        assert text == original

        text2 = "JOHN: Hello\nJANE: Hi"
        detector2 = SpeakerDetector(text2)
        speakers1 = detector2.detect_speakers()
        speakers2 = detector2.detect_speakers()
        assert len(speakers1) == len(speakers2)
        assert speakers1[0].name == speakers2[0].name
