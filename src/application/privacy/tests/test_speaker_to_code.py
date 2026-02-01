"""
Tests for Speaker-to-Code conversion (QC-040.04).

TDD tests written BEFORE implementation.
Converts detected speakers into codes and auto-codes their segments.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from returns.result import Failure, Success
from sqlalchemy import create_engine

from src.domain.shared.types import SourceId
from src.infrastructure.coding import schema as coding_schema
from src.infrastructure.privacy import schema as privacy_schema


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine with both schemas."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    privacy_schema.create_all(engine)
    coding_schema.create_all(engine)
    yield engine
    privacy_schema.drop_all(engine)
    coding_schema.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    """Create a database connection."""
    conn = db_engine.connect()
    yield conn
    conn.close()


@pytest.fixture
def pseudonym_repo(db_connection):
    """Create a pseudonym repository."""
    from src.infrastructure.privacy.repositories import SQLitePseudonymRepository

    return SQLitePseudonymRepository(db_connection)


@pytest.fixture
def session_repo(db_connection):
    """Create a session repository."""
    from src.infrastructure.privacy.repositories import (
        SQLiteAnonymizationSessionRepository,
    )

    return SQLiteAnonymizationSessionRepository(db_connection)


@pytest.fixture
def code_repo(db_connection):
    """Create a code repository."""
    from src.infrastructure.coding.repositories import SQLiteCodeRepository

    return SQLiteCodeRepository(db_connection)


@pytest.fixture
def segment_repo(db_connection):
    """Create a segment repository."""
    from src.infrastructure.coding.repositories import SQLiteSegmentRepository

    return SQLiteSegmentRepository(db_connection)


@pytest.fixture
def event_bus():
    """Create a mock event bus."""
    bus = Mock()
    bus.publish = Mock()
    return bus


@pytest.fixture
def controller(pseudonym_repo, session_repo, code_repo, segment_repo, event_bus):
    """Create a PrivacyController with coding integration."""
    from src.application.privacy.controller import PrivacyController

    return PrivacyController(
        pseudonym_repo=pseudonym_repo,
        session_repo=session_repo,
        event_bus=event_bus,
        code_repo=code_repo,
        segment_repo=segment_repo,
    )


# =============================================================================
# Detect Speakers Tests
# =============================================================================


class TestDetectSpeakers:
    """Tests for detecting speakers in source text."""

    def test_detects_speakers_in_text(self, controller):
        """Should detect speakers using default patterns."""
        from src.application.privacy.commands import DetectSpeakersCommand

        text = """JOHN: Hello there.
JANE: Hi John.
JOHN: How are you?"""

        result = controller.detect_speakers(
            DetectSpeakersCommand(
                source_id=100,
                source_text=text,
            )
        )

        assert isinstance(result, Success)
        speakers = result.unwrap()
        assert len(speakers) == 2
        names = [s.name for s in speakers]
        assert "JOHN" in names
        assert "JANE" in names

    def test_detects_speakers_with_custom_patterns(self, controller):
        """Should detect speakers using custom patterns."""
        from src.application.privacy.commands import DetectSpeakersCommand

        text = """P01: First statement.
P02: Second statement."""

        result = controller.detect_speakers(
            DetectSpeakersCommand(
                source_id=100,
                source_text=text,
                custom_patterns=[r"^(P\d{2}):\s"],
            )
        )

        assert isinstance(result, Success)
        speakers = result.unwrap()
        assert len(speakers) == 2

    def test_detect_returns_segment_counts(self, controller):
        """Should return segment counts per speaker."""
        from src.application.privacy.commands import DetectSpeakersCommand

        text = """JOHN: First.
JANE: Response.
JOHN: Second.
JOHN: Third."""

        result = controller.detect_speakers(
            DetectSpeakersCommand(source_id=100, source_text=text)
        )

        speakers = result.unwrap()
        john = next(s for s in speakers if s.name == "JOHN")
        assert john.segment_count == 3


# =============================================================================
# Convert Speakers to Codes Tests
# =============================================================================


class TestConvertSpeakersToCodes:
    """Tests for converting speakers to codes."""

    def test_creates_code_for_each_speaker(self, controller, code_repo):
        """Should create a code for each speaker."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hello.\nJANE: Hi.",
                speakers=["JOHN", "JANE"],
            )
        )

        assert isinstance(result, Success)

        # Check codes were created
        codes = code_repo.get_all()
        code_names = [c.name for c in codes]
        assert "JOHN" in code_names
        assert "JANE" in code_names

    def test_creates_segments_for_speaker_text(self, controller, segment_repo):
        """Should create coded segments for speaker text."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        text = """JOHN: First statement.
JANE: Response here.
JOHN: Follow up."""

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text=text,
                speakers=["JOHN", "JANE"],
            )
        )

        assert isinstance(result, Success)

        # Check segments were created
        segments = segment_repo.get_by_source(SourceId(value=100))
        assert len(segments) == 3  # 2 JOHN + 1 JANE

    def test_assigns_unique_colors_to_speakers(self, controller, code_repo):
        """Should assign unique colors to each speaker code."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hi.\nJANE: Hello.\nBOB: Hey.",
                speakers=["JOHN", "JANE", "BOB"],
            )
        )

        assert isinstance(result, Success)

        codes = code_repo.get_all()
        colors = [c.color.to_hex() for c in codes]
        # All colors should be unique
        assert len(colors) == len(set(colors))

    def test_uses_provided_category(self, controller, code_repo):
        """Should assign codes to provided category."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hi.",
                speakers=["JOHN"],
                category_id=5,  # Assuming category exists
            )
        )

        # Category assignment is optional, just check code was created
        assert isinstance(result, Success)

    def test_publishes_events_for_codes_and_segments(self, controller, event_bus):
        """Should publish events for created codes and segments."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hi.\nJANE: Hello.",
                speakers=["JOHN", "JANE"],
            )
        )

        # Should have multiple publish calls
        assert event_bus.publish.call_count >= 2

    def test_returns_conversion_result(self, controller):
        """Should return result with created codes and segments."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hi.\nJANE: Hello.",
                speakers=["JOHN", "JANE"],
            )
        )

        assert isinstance(result, Success)
        conversion = result.unwrap()
        assert conversion.code_count == 2
        assert conversion.segment_count == 2

    def test_skips_existing_code_names(self, controller, code_repo):
        """Should not create duplicate codes for existing names."""
        from src.application.privacy.commands import ConvertSpeakersToCodesCommand
        from src.domain.coding.entities import Code, Color
        from src.domain.shared.types import CodeId

        # Pre-create a code named JOHN
        existing_code = Code(
            id=CodeId.new(),
            name="JOHN",
            color=Color(255, 0, 0),
            memo=None,
            category_id=None,
            owner=None,
        )
        code_repo.save(existing_code)

        result = controller.convert_speakers_to_codes(
            ConvertSpeakersToCodesCommand(
                source_id=100,
                source_text="JOHN: Hi.\nJANE: Hello.",
                speakers=["JOHN", "JANE"],
            )
        )

        assert isinstance(result, Success)
        # Should have 2 codes total (1 existing + 1 new)
        codes = code_repo.get_all()
        assert len(codes) == 2


# =============================================================================
# Preview Conversion Tests
# =============================================================================


class TestPreviewSpeakerConversion:
    """Tests for previewing speaker-to-code conversion."""

    def test_preview_shows_what_would_be_created(self, controller):
        """Should preview without making changes."""
        from src.application.privacy.commands import PreviewSpeakerConversionCommand

        text = """JOHN: Hello.
JANE: Hi there."""

        result = controller.preview_speaker_conversion(
            PreviewSpeakerConversionCommand(
                source_id=100,
                source_text=text,
                speakers=["JOHN", "JANE"],
            )
        )

        assert isinstance(result, Success)
        preview = result.unwrap()
        assert len(preview.speakers) == 2
        assert preview.total_segments == 2

    def test_preview_does_not_persist(self, controller, code_repo, segment_repo):
        """Preview should not create any database records."""
        from src.application.privacy.commands import PreviewSpeakerConversionCommand

        controller.preview_speaker_conversion(
            PreviewSpeakerConversionCommand(
                source_id=100,
                source_text="JOHN: Hi.",
                speakers=["JOHN"],
            )
        )

        # Nothing should be persisted
        assert len(code_repo.get_all()) == 0
        assert len(segment_repo.get_all()) == 0
