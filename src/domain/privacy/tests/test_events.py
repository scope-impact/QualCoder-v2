"""
Tests for Privacy domain events.

TDD tests written BEFORE implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.shared.types import SourceId


class TestPseudonymCreated:
    """Tests for PseudonymCreated event."""

    def test_create_event_with_required_fields(self):
        """Should create PseudonymCreated event."""
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymCreated

        event = PseudonymCreated(
            event_id="evt_123",
            occurred_at=datetime.now(UTC),
            pseudonym_id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant A",
            category="person",
        )

        assert event.event_type == "privacy.pseudonym_created"
        assert event.pseudonym_id.value == 1
        assert event.real_name == "John Smith"
        assert event.alias == "Participant A"
        assert event.category == "person"

    def test_event_is_immutable(self):
        """PseudonymCreated should be frozen."""
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymCreated

        event = PseudonymCreated(
            event_id="evt_123",
            occurred_at=datetime.now(UTC),
            pseudonym_id=PseudonymId(value=1),
            real_name="Test",
            alias="Alias",
            category="person",
        )

        with pytest.raises((AttributeError, TypeError)):
            event.alias = "New Alias"


class TestPseudonymUpdated:
    """Tests for PseudonymUpdated event."""

    def test_create_event(self):
        """Should create PseudonymUpdated event."""
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymUpdated

        event = PseudonymUpdated(
            event_id="evt_456",
            occurred_at=datetime.now(UTC),
            pseudonym_id=PseudonymId(value=1),
            old_alias="P1",
            new_alias="Participant Alpha",
        )

        assert event.event_type == "privacy.pseudonym_updated"
        assert event.old_alias == "P1"
        assert event.new_alias == "Participant Alpha"


class TestPseudonymDeleted:
    """Tests for PseudonymDeleted event."""

    def test_create_event(self):
        """Should create PseudonymDeleted event."""
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymDeleted

        event = PseudonymDeleted(
            event_id="evt_789",
            occurred_at=datetime.now(UTC),
            pseudonym_id=PseudonymId(value=1),
            alias="Participant A",
        )

        assert event.event_type == "privacy.pseudonym_deleted"
        assert event.alias == "Participant A"


class TestPseudonymsApplied:
    """Tests for PseudonymsApplied event."""

    def test_create_event(self):
        """Should create PseudonymsApplied event."""
        from src.domain.privacy.entities import AnonymizationSessionId
        from src.domain.privacy.events import PseudonymsApplied

        event = PseudonymsApplied(
            event_id="evt_apply",
            occurred_at=datetime.now(UTC),
            session_id=AnonymizationSessionId(value="anon_123"),
            source_id=SourceId(value=100),
            pseudonym_count=3,
            replacement_count=15,
        )

        assert event.event_type == "privacy.pseudonyms_applied"
        assert event.pseudonym_count == 3
        assert event.replacement_count == 15


class TestAnonymizationReverted:
    """Tests for AnonymizationReverted event."""

    def test_create_event(self):
        """Should create AnonymizationReverted event."""
        from src.domain.privacy.entities import AnonymizationSessionId
        from src.domain.privacy.events import AnonymizationReverted

        event = AnonymizationReverted(
            event_id="evt_revert",
            occurred_at=datetime.now(UTC),
            session_id=AnonymizationSessionId(value="anon_123"),
            source_id=SourceId(value=100),
        )

        assert event.event_type == "privacy.anonymization_reverted"
        assert event.session_id.value == "anon_123"
