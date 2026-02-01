"""
Tests for Privacy domain entities.

TDD tests written BEFORE implementation.
Tests verify entity immutability, validation, and behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.privacy.entities import (
    AnonymizationSession,
    DetectedIdentifier,
    Pseudonym,
    PseudonymCategory,
    TextReplacement,
)
from src.domain.shared.types import SourceId


class TestPseudonymCategory:
    """Tests for PseudonymCategory enum."""

    def test_has_person_category(self):
        """Should have PERSON category."""
        assert PseudonymCategory.PERSON.value == "person"

    def test_has_organization_category(self):
        """Should have ORGANIZATION category."""
        assert PseudonymCategory.ORGANIZATION.value == "organization"

    def test_has_location_category(self):
        """Should have LOCATION category."""
        assert PseudonymCategory.LOCATION.value == "location"

    def test_has_date_category(self):
        """Should have DATE category."""
        assert PseudonymCategory.DATE.value == "date"

    def test_has_other_category(self):
        """Should have OTHER category."""
        assert PseudonymCategory.OTHER.value == "other"


class TestPseudonym:
    """Tests for Pseudonym entity."""

    def test_create_pseudonym_with_required_fields(self):
        """Should create pseudonym with required fields."""
        from src.domain.privacy.entities import PseudonymId

        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant A",
            category=PseudonymCategory.PERSON,
        )

        assert pseudonym.id.value == 1
        assert pseudonym.real_name == "John Smith"
        assert pseudonym.alias == "Participant A"
        assert pseudonym.category == PseudonymCategory.PERSON
        assert pseudonym.notes is None

    def test_create_pseudonym_with_all_fields(self):
        """Should create pseudonym with all optional fields."""
        from src.domain.privacy.entities import PseudonymId

        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        pseudonym = Pseudonym(
            id=PseudonymId(value=2),
            real_name="Acme Corp",
            alias="Company X",
            category=PseudonymCategory.ORGANIZATION,
            notes="Main research partner",
            created_at=created,
        )

        assert pseudonym.notes == "Main research partner"
        assert pseudonym.created_at == created

    def test_pseudonym_is_immutable(self):
        """Pseudonym should be frozen/immutable."""
        from src.domain.privacy.entities import PseudonymId

        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="Test",
            alias="Alias",
            category=PseudonymCategory.PERSON,
        )

        with pytest.raises((AttributeError, TypeError)):
            pseudonym.alias = "New Alias"

    def test_with_alias_returns_new_pseudonym(self):
        """with_alias should return new instance with updated alias."""
        from src.domain.privacy.entities import PseudonymId

        original = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )

        updated = original.with_alias("Participant Alpha")

        assert updated.alias == "Participant Alpha"
        assert original.alias == "P1"  # Original unchanged
        assert updated.id == original.id
        assert updated.real_name == original.real_name

    def test_with_notes_returns_new_pseudonym(self):
        """with_notes should return new instance with updated notes."""
        from src.domain.privacy.entities import PseudonymId

        original = Pseudonym(
            id=PseudonymId(value=1),
            real_name="Test",
            alias="Alias",
            category=PseudonymCategory.PERSON,
            notes=None,
        )

        updated = original.with_notes("Important note")

        assert updated.notes == "Important note"
        assert original.notes is None


class TestPseudonymId:
    """Tests for PseudonymId typed identifier."""

    def test_create_pseudonym_id(self):
        """Should create PseudonymId with value."""
        from src.domain.privacy.entities import PseudonymId

        pid = PseudonymId(value=42)
        assert pid.value == 42

    def test_pseudonym_id_is_immutable(self):
        """PseudonymId should be frozen."""
        from src.domain.privacy.entities import PseudonymId

        pid = PseudonymId(value=1)
        with pytest.raises((AttributeError, TypeError)):
            pid.value = 2

    def test_pseudonym_id_new_generates_unique_id(self):
        """PseudonymId.new() should generate unique IDs."""
        from src.domain.privacy.entities import PseudonymId

        id1 = PseudonymId.new()
        id2 = PseudonymId.new()
        assert id1.value != id2.value

    def test_pseudonym_id_equality(self):
        """PseudonymIds with same value should be equal."""
        from src.domain.privacy.entities import PseudonymId

        id1 = PseudonymId(value=5)
        id2 = PseudonymId(value=5)
        assert id1 == id2


class TestAnonymizationSessionId:
    """Tests for AnonymizationSessionId typed identifier."""

    def test_create_session_id(self):
        """Should create AnonymizationSessionId with value."""
        from src.domain.privacy.entities import AnonymizationSessionId

        sid = AnonymizationSessionId(value="anon_abc123")
        assert sid.value == "anon_abc123"

    def test_session_id_new_generates_unique_id(self):
        """AnonymizationSessionId.new() should generate unique IDs."""
        from src.domain.privacy.entities import AnonymizationSessionId

        id1 = AnonymizationSessionId.new()
        id2 = AnonymizationSessionId.new()
        assert id1.value != id2.value
        assert id1.value.startswith("anon_")


class TestTextReplacement:
    """Tests for TextReplacement value object."""

    def test_create_text_replacement(self):
        """Should create TextReplacement with positions."""
        replacement = TextReplacement(
            original_text="John Smith",
            replacement_text="Participant A",
            positions=((0, 10), (50, 60)),
        )

        assert replacement.original_text == "John Smith"
        assert replacement.replacement_text == "Participant A"
        assert len(replacement.positions) == 2
        assert replacement.positions[0] == (0, 10)

    def test_text_replacement_is_immutable(self):
        """TextReplacement should be frozen."""
        replacement = TextReplacement(
            original_text="Test",
            replacement_text="Alias",
            positions=((0, 4),),
        )

        with pytest.raises((AttributeError, TypeError)):
            replacement.original_text = "Changed"


class TestAnonymizationSession:
    """Tests for AnonymizationSession entity."""

    def test_create_session(self):
        """Should create AnonymizationSession with required fields."""
        from src.domain.privacy.entities import AnonymizationSessionId, PseudonymId

        session = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_test123"),
            source_id=SourceId(value=100),
            original_text="The original interview text with John Smith.",
            pseudonym_ids=(PseudonymId(value=1), PseudonymId(value=2)),
            replacements=(
                TextReplacement(
                    original_text="John Smith",
                    replacement_text="P1",
                    positions=((34, 44),),
                ),
            ),
        )

        assert session.id.value == "anon_test123"
        assert session.source_id.value == 100
        assert len(session.pseudonym_ids) == 2
        assert session.reverted_at is None

    def test_session_is_reversible_when_not_reverted(self):
        """Session should be reversible when reverted_at is None."""
        from src.domain.privacy.entities import AnonymizationSessionId

        session = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_test"),
            source_id=SourceId(value=1),
            original_text="Original",
            pseudonym_ids=(),
            replacements=(),
            reverted_at=None,
        )

        assert session.is_reversible() is True

    def test_session_not_reversible_when_reverted(self):
        """Session should not be reversible when already reverted."""
        from src.domain.privacy.entities import AnonymizationSessionId

        reverted_time = datetime.now(UTC)
        session = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_test"),
            source_id=SourceId(value=1),
            original_text="Original",
            pseudonym_ids=(),
            replacements=(),
            reverted_at=reverted_time,
        )

        assert session.is_reversible() is False


class TestDetectedIdentifier:
    """Tests for DetectedIdentifier value object."""

    def test_create_detected_identifier(self):
        """Should create DetectedIdentifier with all fields."""
        identifier = DetectedIdentifier(
            text="John Smith",
            category=PseudonymCategory.PERSON,
            positions=((0, 10), (100, 110)),
            confidence=0.95,
            suggested_alias="Participant A",
        )

        assert identifier.text == "John Smith"
        assert identifier.category == PseudonymCategory.PERSON
        assert len(identifier.positions) == 2
        assert identifier.confidence == 0.95
        assert identifier.suggested_alias == "Participant A"

    def test_detected_identifier_without_suggestion(self):
        """Should create DetectedIdentifier without suggested alias."""
        identifier = DetectedIdentifier(
            text="Acme Corp",
            category=PseudonymCategory.ORGANIZATION,
            positions=((20, 29),),
            confidence=0.8,
            suggested_alias=None,
        )

        assert identifier.suggested_alias is None
