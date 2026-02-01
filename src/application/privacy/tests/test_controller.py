"""
Tests for PrivacyController - Application Service.

TDD tests written BEFORE implementation.
Follows the 5-step controller pattern.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from returns.result import Failure, Success
from sqlalchemy import create_engine

from src.domain.privacy.entities import Pseudonym, PseudonymCategory, PseudonymId
from src.domain.shared.types import SourceId
from src.infrastructure.privacy.schema import create_all, drop_all


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all(engine)
    yield engine
    drop_all(engine)
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
def event_bus():
    """Create a mock event bus."""
    bus = Mock()
    bus.publish = Mock()
    return bus


@pytest.fixture
def controller(pseudonym_repo, session_repo, event_bus):
    """Create a PrivacyController with dependencies."""
    from src.application.privacy.controller import PrivacyController

    return PrivacyController(
        pseudonym_repo=pseudonym_repo,
        session_repo=session_repo,
        event_bus=event_bus,
    )


# =============================================================================
# Create Pseudonym Tests
# =============================================================================


class TestCreatePseudonym:
    """Tests for create_pseudonym command."""

    def test_creates_pseudonym_with_valid_inputs(self, controller, pseudonym_repo):
        """Should create pseudonym and persist to repository."""
        from src.application.privacy.commands import CreatePseudonymCommand

        command = CreatePseudonymCommand(
            real_name="John Smith",
            alias="Participant A",
            category="person",
            notes="Interview subject",
        )

        result = controller.create_pseudonym(command)

        assert isinstance(result, Success)
        pseudonym = result.unwrap()
        assert pseudonym.real_name == "John Smith"
        assert pseudonym.alias == "Participant A"

        # Verify persisted
        saved = pseudonym_repo.get_by_id(pseudonym.id)
        assert saved is not None
        assert saved.alias == "Participant A"

    def test_creates_pseudonym_publishes_event(self, controller, event_bus):
        """Should publish PseudonymCreated event."""
        from src.application.privacy.commands import CreatePseudonymCommand

        command = CreatePseudonymCommand(
            real_name="Jane Doe",
            alias="Participant B",
            category="person",
        )

        controller.create_pseudonym(command)

        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert event.event_type == "privacy.pseudonym_created"
        assert event.alias == "Participant B"

    def test_fails_with_empty_real_name(self, controller):
        """Should fail with empty real name."""
        from src.application.privacy.commands import CreatePseudonymCommand

        command = CreatePseudonymCommand(
            real_name="",
            alias="Participant A",
            category="person",
        )

        result = controller.create_pseudonym(command)

        assert isinstance(result, Failure)

    def test_fails_with_duplicate_real_name(self, controller):
        """Should fail when real name already mapped."""
        from src.application.privacy.commands import CreatePseudonymCommand

        # Create first
        controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P1",
                category="person",
            )
        )

        # Try duplicate
        result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P2",
                category="person",
            )
        )

        assert isinstance(result, Failure)

    def test_fails_with_duplicate_alias(self, controller):
        """Should fail when alias already used."""
        from src.application.privacy.commands import CreatePseudonymCommand

        # Create first
        controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="Participant A",
                category="person",
            )
        )

        # Try duplicate alias
        result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="Jane Doe",
                alias="Participant A",
                category="person",
            )
        )

        assert isinstance(result, Failure)


# =============================================================================
# Update Pseudonym Tests
# =============================================================================


class TestUpdatePseudonym:
    """Tests for update_pseudonym command."""

    def test_updates_pseudonym_alias(self, controller, pseudonym_repo):
        """Should update pseudonym alias."""
        from src.application.privacy.commands import (
            CreatePseudonymCommand,
            UpdatePseudonymCommand,
        )

        # Create first
        create_result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P1",
                category="person",
            )
        )
        pseudonym_id = create_result.unwrap().id.value

        # Update
        result = controller.update_pseudonym(
            UpdatePseudonymCommand(
                pseudonym_id=pseudonym_id,
                new_alias="Participant Alpha",
            )
        )

        assert isinstance(result, Success)
        updated = pseudonym_repo.get_by_id(PseudonymId(value=pseudonym_id))
        assert updated.alias == "Participant Alpha"

    def test_update_publishes_event(self, controller, event_bus):
        """Should publish PseudonymUpdated event."""
        from src.application.privacy.commands import (
            CreatePseudonymCommand,
            UpdatePseudonymCommand,
        )

        create_result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P1",
                category="person",
            )
        )
        event_bus.reset_mock()

        controller.update_pseudonym(
            UpdatePseudonymCommand(
                pseudonym_id=create_result.unwrap().id.value,
                new_alias="P2",
            )
        )

        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert event.event_type == "privacy.pseudonym_updated"

    def test_fails_for_nonexistent_pseudonym(self, controller):
        """Should fail for non-existent pseudonym."""
        from src.application.privacy.commands import UpdatePseudonymCommand

        result = controller.update_pseudonym(
            UpdatePseudonymCommand(
                pseudonym_id=999,
                new_alias="New Alias",
            )
        )

        assert isinstance(result, Failure)


# =============================================================================
# Delete Pseudonym Tests
# =============================================================================


class TestDeletePseudonym:
    """Tests for delete_pseudonym command."""

    def test_deletes_pseudonym(self, controller, pseudonym_repo):
        """Should delete pseudonym from repository."""
        from src.application.privacy.commands import (
            CreatePseudonymCommand,
            DeletePseudonymCommand,
        )

        create_result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P1",
                category="person",
            )
        )
        pseudonym_id = create_result.unwrap().id.value

        result = controller.delete_pseudonym(
            DeletePseudonymCommand(pseudonym_id=pseudonym_id)
        )

        assert isinstance(result, Success)
        assert pseudonym_repo.get_by_id(PseudonymId(value=pseudonym_id)) is None

    def test_delete_publishes_event(self, controller, event_bus):
        """Should publish PseudonymDeleted event."""
        from src.application.privacy.commands import (
            CreatePseudonymCommand,
            DeletePseudonymCommand,
        )

        create_result = controller.create_pseudonym(
            CreatePseudonymCommand(
                real_name="John Smith",
                alias="P1",
                category="person",
            )
        )
        event_bus.reset_mock()

        controller.delete_pseudonym(
            DeletePseudonymCommand(pseudonym_id=create_result.unwrap().id.value)
        )

        event_bus.publish.assert_called_once()
        event = event_bus.publish.call_args[0][0]
        assert event.event_type == "privacy.pseudonym_deleted"


# =============================================================================
# Get Pseudonyms Tests
# =============================================================================


class TestGetPseudonyms:
    """Tests for pseudonym queries."""

    def test_get_all_pseudonyms(self, controller):
        """Should return all pseudonyms."""
        from src.application.privacy.commands import CreatePseudonymCommand

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="A", alias="P1", category="person")
        )
        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="B", alias="P2", category="person")
        )

        result = controller.get_all_pseudonyms()

        assert len(result) == 2

    def test_get_pseudonyms_by_category(self, controller):
        """Should filter pseudonyms by category."""
        from src.application.privacy.commands import CreatePseudonymCommand

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John", alias="P1", category="person")
        )
        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="Acme", alias="C1", category="organization")
        )

        persons = controller.get_pseudonyms_by_category(PseudonymCategory.PERSON)
        orgs = controller.get_pseudonyms_by_category(PseudonymCategory.ORGANIZATION)

        assert len(persons) == 1
        assert len(orgs) == 1
        assert persons[0].alias == "P1"


# =============================================================================
# Apply Pseudonyms Tests
# =============================================================================


class TestApplyPseudonyms:
    """Tests for apply_pseudonyms command."""

    def test_applies_pseudonyms_to_text(self, controller):
        """Should apply pseudonyms and return anonymized result."""
        from src.application.privacy.commands import (
            ApplyPseudonymsCommand,
            CreatePseudonymCommand,
        )

        # Create pseudonyms
        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John Smith", alias="P1", category="person")
        )

        # Apply to text
        result = controller.apply_pseudonyms(
            ApplyPseudonymsCommand(
                source_id=100,
                source_text="John Smith said hello.",
            )
        )

        assert isinstance(result, Success)
        apply_result = result.unwrap()
        assert apply_result.anonymized_text == "P1 said hello."

    def test_apply_creates_session_for_reversal(self, controller, session_repo):
        """Should create anonymization session for undo."""
        from src.application.privacy.commands import (
            ApplyPseudonymsCommand,
            CreatePseudonymCommand,
        )

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John Smith", alias="P1", category="person")
        )

        result = controller.apply_pseudonyms(
            ApplyPseudonymsCommand(
                source_id=100,
                source_text="John Smith was here.",
            )
        )

        apply_result = result.unwrap()
        session = session_repo.get_by_id(apply_result.session_id)
        assert session is not None
        assert session.original_text == "John Smith was here."

    def test_apply_publishes_event(self, controller, event_bus):
        """Should publish PseudonymsApplied event."""
        from src.application.privacy.commands import (
            ApplyPseudonymsCommand,
            CreatePseudonymCommand,
        )

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John", alias="P1", category="person")
        )
        event_bus.reset_mock()

        controller.apply_pseudonyms(
            ApplyPseudonymsCommand(
                source_id=100,
                source_text="John spoke.",
            )
        )

        # Find the PseudonymsApplied event
        calls = event_bus.publish.call_args_list
        applied_events = [c for c in calls if c[0][0].event_type == "privacy.pseudonyms_applied"]
        assert len(applied_events) == 1


# =============================================================================
# Revert Anonymization Tests
# =============================================================================


class TestRevertAnonymization:
    """Tests for revert_anonymization command."""

    def test_reverts_to_original_text(self, controller):
        """Should revert to original text."""
        from src.application.privacy.commands import (
            ApplyPseudonymsCommand,
            CreatePseudonymCommand,
            RevertAnonymizationCommand,
        )

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John Smith", alias="P1", category="person")
        )

        apply_result = controller.apply_pseudonyms(
            ApplyPseudonymsCommand(
                source_id=100,
                source_text="John Smith was here.",
            )
        )

        revert_result = controller.revert_anonymization(
            RevertAnonymizationCommand(
                source_id=100,
                session_id=apply_result.unwrap().session_id.value,
            )
        )

        assert isinstance(revert_result, Success)
        assert revert_result.unwrap().original_text == "John Smith was here."

    def test_revert_marks_session_as_reverted(self, controller, session_repo):
        """Should mark session as reverted."""
        from src.application.privacy.commands import (
            ApplyPseudonymsCommand,
            CreatePseudonymCommand,
            RevertAnonymizationCommand,
        )

        controller.create_pseudonym(
            CreatePseudonymCommand(real_name="John", alias="P1", category="person")
        )

        apply_result = controller.apply_pseudonyms(
            ApplyPseudonymsCommand(source_id=100, source_text="John here.")
        )
        session_id = apply_result.unwrap().session_id

        controller.revert_anonymization(
            RevertAnonymizationCommand(source_id=100, session_id=session_id.value)
        )

        session = session_repo.get_by_id(session_id)
        assert session.reverted_at is not None
        assert not session.is_reversible()
