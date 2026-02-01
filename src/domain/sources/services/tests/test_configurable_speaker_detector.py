"""
Tests for ConfigurableSpeakerDetector - extended speaker detection with custom patterns.

TDD tests written BEFORE implementation.
Extends existing SpeakerDetector with configurable pattern support (QC-040.03).
"""

from __future__ import annotations

import pytest


class TestConfigurableSpeakerDetectorCustomPatterns:
    """Tests for custom pattern support in speaker detection."""

    def test_accepts_custom_patterns_in_constructor(self):
        """Should accept custom patterns in constructor."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        custom_patterns = [r"^Speaker\s+(\d+):\s"]
        detector = ConfigurableSpeakerDetector(
            text="Speaker 1: Hello",
            custom_patterns=custom_patterns,
        )

        speakers = detector.detect_speakers()

        assert len(speakers) >= 1
        names = [s.name for s in speakers]
        assert "1" in names

    def test_custom_pattern_detects_numbered_speakers(self):
        """Should detect numbered speaker format."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """Speaker 1: First person talking.
Speaker 2: Second person response.
Speaker 1: First person again."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^Speaker\s+(\d+):\s"],
        )

        speakers = detector.detect_speakers()

        assert len(speakers) == 2
        speaker_1 = next(s for s in speakers if s.name == "1")
        assert speaker_1.count == 2

    def test_custom_pattern_detects_participant_codes(self):
        """Should detect P01, P02 style participant codes."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """P01: I think that...
P02: I agree with that.
P01: And furthermore..."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^(P\d{2}):\s"],
        )

        speakers = detector.detect_speakers()

        names = [s.name for s in speakers]
        assert "P01" in names
        assert "P02" in names

    def test_custom_pattern_with_timestamps(self):
        """Should detect speakers with timestamp prefix."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """[00:01:23] John: Hello everyone.
[00:01:45] Sarah: Hi John."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^\[\d{2}:\d{2}:\d{2}\]\s+([A-Za-z]+):\s"],
        )

        speakers = detector.detect_speakers()

        names = [s.name for s in speakers]
        assert "John" in names
        assert "Sarah" in names

    def test_combines_default_and_custom_patterns(self):
        """Should use both default and custom patterns when include_defaults=True."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """INTERVIEWER: Standard format.
P01: Custom format."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^(P\d{2}):\s"],
            include_defaults=True,
        )

        speakers = detector.detect_speakers()

        names = [s.name for s in speakers]
        assert "INTERVIEWER" in names  # From default pattern
        assert "P01" in names  # From custom pattern

    def test_custom_patterns_only_when_include_defaults_false(self):
        """Should only use custom patterns when include_defaults=False."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """INTERVIEWER: Standard format.
P01: Custom format."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^(P\d{2}):\s"],
            include_defaults=False,
        )

        speakers = detector.detect_speakers()

        names = [s.name for s in speakers]
        assert "INTERVIEWER" not in names  # Default pattern not used
        assert "P01" in names  # Custom pattern used

    def test_empty_custom_patterns_uses_defaults(self):
        """Should use defaults when no custom patterns provided."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = "JOHN: Hello there."

        detector = ConfigurableSpeakerDetector(text=text)

        speakers = detector.detect_speakers()

        assert len(speakers) == 1
        assert speakers[0].name == "JOHN"

    def test_invalid_pattern_raises_error(self):
        """Should raise error for invalid regex patterns."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
            InvalidPatternError,
        )

        with pytest.raises(InvalidPatternError):
            ConfigurableSpeakerDetector(
                text="test",
                custom_patterns=["[invalid(regex"],
            )

    def test_pattern_without_capture_group_raises_error(self):
        """Should raise error for patterns without capture group."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
            InvalidPatternError,
        )

        with pytest.raises(InvalidPatternError):
            ConfigurableSpeakerDetector(
                text="test",
                custom_patterns=[r"^Speaker:\s"],  # No capture group
            )


class TestConfigurableSpeakerDetectorSegments:
    """Tests for segment extraction with custom patterns."""

    def test_get_segments_with_custom_pattern(self):
        """Should extract segments using custom pattern."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = """P01: First statement.
P02: Response here.
P01: Follow-up."""

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^(P\d{2}):\s"],
        )

        segments = detector.get_speaker_segments("P01")

        assert len(segments) == 2
        assert "First statement" in segments[0].text
        assert "Follow-up" in segments[1].text

    def test_segment_positions_correct_with_custom_pattern(self):
        """Segment positions should be correct for custom patterns."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
        )

        text = "P01: Hello world"

        detector = ConfigurableSpeakerDetector(
            text=text,
            custom_patterns=[r"^(P\d{2}):\s"],
        )

        segments = detector.get_speaker_segments("P01")

        assert len(segments) == 1
        segment = segments[0]
        assert segment.start >= 0
        assert segment.end <= len(text)


class TestSpeakerPatternValueObject:
    """Tests for SpeakerPattern value object."""

    def test_create_speaker_pattern(self):
        """Should create SpeakerPattern with required fields."""
        from src.domain.sources.services.speaker_detector import SpeakerPattern

        pattern = SpeakerPattern(
            regex=r"^(P\d{2}):\s",
            description="Participant codes P01, P02, etc.",
            is_default=False,
        )

        assert pattern.regex == r"^(P\d{2}):\s"
        assert pattern.description == "Participant codes P01, P02, etc."
        assert pattern.is_default is False

    def test_speaker_pattern_is_immutable(self):
        """SpeakerPattern should be frozen."""
        from src.domain.sources.services.speaker_detector import SpeakerPattern

        pattern = SpeakerPattern(
            regex=r"^Test:\s",
            description="Test pattern",
            is_default=False,
        )

        with pytest.raises((AttributeError, TypeError)):
            pattern.regex = "new regex"

    def test_speaker_pattern_validates_regex(self):
        """Should validate regex on creation."""
        from src.domain.sources.services.speaker_detector import SpeakerPattern

        # Valid pattern should work
        pattern = SpeakerPattern(
            regex=r"^([A-Z]+):\s",
            description="Valid",
            is_default=False,
        )
        assert pattern.is_valid()

    def test_speaker_pattern_compile(self):
        """Should compile regex to Pattern object."""
        from src.domain.sources.services.speaker_detector import SpeakerPattern

        pattern = SpeakerPattern(
            regex=r"^([A-Z]+):\s",
            description="Uppercase",
            is_default=False,
        )

        compiled = pattern.compile()
        assert compiled.match("JOHN: Hello")


class TestDetectedSpeakerExtended:
    """Tests for DetectedSpeaker with extended info for code conversion."""

    def test_detected_speaker_includes_segments(self):
        """DetectedSpeaker should include segment details."""
        from src.domain.sources.services.speaker_detector import (
            ConfigurableSpeakerDetector,
            DetectedSpeakerInfo,
        )

        text = """JOHN: First thing.
JANE: Response.
JOHN: Second thing."""

        detector = ConfigurableSpeakerDetector(text=text)
        speakers = detector.detect_speakers_with_segments()

        john = next(s for s in speakers if s.name == "JOHN")
        assert isinstance(john, DetectedSpeakerInfo)
        assert john.segment_count == 2
        assert len(john.segments) == 2

    def test_detected_speaker_info_has_suggested_color(self):
        """DetectedSpeakerInfo can have suggested color for code conversion."""
        from src.domain.sources.services.speaker_detector import DetectedSpeakerInfo

        info = DetectedSpeakerInfo(
            name="JOHN",
            segment_count=3,
            segments=(),
            suggested_code_color="#FF5722",
        )

        assert info.suggested_code_color == "#FF5722"
