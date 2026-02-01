"""
Tests for Privacy context SQLAlchemy repositories.

TDD tests written BEFORE implementation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from src.domain.privacy.entities import (
    AnonymizationSession,
    AnonymizationSessionId,
    Pseudonym,
    PseudonymCategory,
    PseudonymId,
    TextReplacement,
)
from src.domain.shared.types import SourceId
from src.infrastructure.privacy.schema import create_all, drop_all


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine with privacy schema."""
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
    """Create an anonymization session repository."""
    from src.infrastructure.privacy.repositories import (
        SQLiteAnonymizationSessionRepository,
    )

    return SQLiteAnonymizationSessionRepository(db_connection)


# =============================================================================
# Pseudonym Repository Tests
# =============================================================================


class TestSQLitePseudonymRepository:
    """Tests for SQLitePseudonymRepository."""

    def test_save_and_get_by_id(self, pseudonym_repo):
        """Test saving and retrieving a pseudonym."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant A",
            category=PseudonymCategory.PERSON,
            notes="Interview subject",
        )
        pseudonym_repo.save(pseudonym)

        retrieved = pseudonym_repo.get_by_id(PseudonymId(value=1))
        assert retrieved is not None
        assert retrieved.real_name == "John Smith"
        assert retrieved.alias == "Participant A"
        assert retrieved.category == PseudonymCategory.PERSON
        assert retrieved.notes == "Interview subject"

    def test_get_by_id_not_found(self, pseudonym_repo):
        """Test getting a non-existent pseudonym returns None."""
        result = pseudonym_repo.get_by_id(PseudonymId(value=999))
        assert result is None

    def test_get_all(self, pseudonym_repo):
        """Test getting all pseudonyms."""
        p1 = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        p2 = Pseudonym(
            id=PseudonymId(value=2),
            real_name="Acme Corp",
            alias="Company X",
            category=PseudonymCategory.ORGANIZATION,
        )
        pseudonym_repo.save(p1)
        pseudonym_repo.save(p2)

        pseudonyms = pseudonym_repo.get_all()
        assert len(pseudonyms) == 2

    def test_get_by_real_name(self, pseudonym_repo):
        """Test getting pseudonym by real name."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        # Exact match
        result = pseudonym_repo.get_by_real_name("John Smith")
        assert result is not None
        assert result.alias == "P1"

        # Case insensitive
        result = pseudonym_repo.get_by_real_name("john smith")
        assert result is not None

    def test_get_by_alias(self, pseudonym_repo):
        """Test getting pseudonym by alias."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant A",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        result = pseudonym_repo.get_by_alias("Participant A")
        assert result is not None
        assert result.real_name == "John Smith"

    def test_get_by_category(self, pseudonym_repo):
        """Test getting pseudonyms by category."""
        p1 = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        p2 = Pseudonym(
            id=PseudonymId(value=2),
            real_name="Jane Doe",
            alias="P2",
            category=PseudonymCategory.PERSON,
        )
        p3 = Pseudonym(
            id=PseudonymId(value=3),
            real_name="Acme Corp",
            alias="Company X",
            category=PseudonymCategory.ORGANIZATION,
        )
        pseudonym_repo.save(p1)
        pseudonym_repo.save(p2)
        pseudonym_repo.save(p3)

        persons = pseudonym_repo.get_by_category(PseudonymCategory.PERSON)
        assert len(persons) == 2

        orgs = pseudonym_repo.get_by_category(PseudonymCategory.ORGANIZATION)
        assert len(orgs) == 1

    def test_update_existing_pseudonym(self, pseudonym_repo):
        """Test updating an existing pseudonym."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        updated = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant Alpha",
            category=PseudonymCategory.PERSON,
            notes="Updated notes",
        )
        pseudonym_repo.save(updated)

        retrieved = pseudonym_repo.get_by_id(PseudonymId(value=1))
        assert retrieved.alias == "Participant Alpha"
        assert retrieved.notes == "Updated notes"

    def test_delete(self, pseudonym_repo):
        """Test deleting a pseudonym."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)
        assert pseudonym_repo.exists(PseudonymId(value=1))

        pseudonym_repo.delete(PseudonymId(value=1))
        assert not pseudonym_repo.exists(PseudonymId(value=1))

    def test_real_name_exists(self, pseudonym_repo):
        """Test checking if real name exists."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        assert pseudonym_repo.real_name_exists("John Smith")
        assert pseudonym_repo.real_name_exists("john smith")  # case insensitive
        assert not pseudonym_repo.real_name_exists("Jane Doe")

    def test_alias_exists(self, pseudonym_repo):
        """Test checking if alias exists."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        assert pseudonym_repo.alias_exists("P1")
        assert not pseudonym_repo.alias_exists("P2")

    def test_alias_exists_with_exclude(self, pseudonym_repo):
        """Test alias_exists excludes specified ID."""
        pseudonym = Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="P1",
            category=PseudonymCategory.PERSON,
        )
        pseudonym_repo.save(pseudonym)

        # Same alias exists, but excluding its own ID should return False
        assert not pseudonym_repo.alias_exists("P1", exclude_id=PseudonymId(value=1))
        assert pseudonym_repo.alias_exists("P1", exclude_id=PseudonymId(value=2))


# =============================================================================
# Anonymization Session Repository Tests
# =============================================================================


class TestSQLiteAnonymizationSessionRepository:
    """Tests for SQLiteAnonymizationSessionRepository."""

    def test_save_and_get_by_id(self, session_repo):
        """Test saving and retrieving a session."""
        session = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_test123"),
            source_id=SourceId(value=100),
            original_text="The original text with John Smith.",
            pseudonym_ids=(PseudonymId(value=1),),
            replacements=(
                TextReplacement(
                    original_text="John Smith",
                    replacement_text="P1",
                    positions=((24, 34),),
                ),
            ),
        )
        session_repo.save(session)

        retrieved = session_repo.get_by_id(AnonymizationSessionId(value="anon_test123"))
        assert retrieved is not None
        assert retrieved.source_id.value == 100
        assert retrieved.original_text == "The original text with John Smith."
        assert len(retrieved.pseudonym_ids) == 1
        assert len(retrieved.replacements) == 1

    def test_get_by_id_not_found(self, session_repo):
        """Test getting a non-existent session returns None."""
        result = session_repo.get_by_id(AnonymizationSessionId(value="anon_notfound"))
        assert result is None

    def test_get_by_source(self, session_repo):
        """Test getting sessions by source."""
        s1 = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_s1"),
            source_id=SourceId(value=100),
            original_text="Text 1",
            pseudonym_ids=(),
            replacements=(),
        )
        s2 = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_s2"),
            source_id=SourceId(value=100),
            original_text="Text 2",
            pseudonym_ids=(),
            replacements=(),
        )
        s3 = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_s3"),
            source_id=SourceId(value=200),
            original_text="Text 3",
            pseudonym_ids=(),
            replacements=(),
        )
        session_repo.save(s1)
        session_repo.save(s2)
        session_repo.save(s3)

        sessions = session_repo.get_by_source(SourceId(value=100))
        assert len(sessions) == 2

    def test_get_active_session(self, session_repo):
        """Test getting the most recent non-reverted session."""
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        s1 = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_old"),
            source_id=SourceId(value=100),
            original_text="Old text",
            pseudonym_ids=(),
            replacements=(),
            created_at=now - timedelta(hours=2),
            reverted_at=now - timedelta(hours=1),  # Reverted
        )
        s2 = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_new"),
            source_id=SourceId(value=100),
            original_text="New text",
            pseudonym_ids=(),
            replacements=(),
            created_at=now,
            reverted_at=None,  # Active
        )
        session_repo.save(s1)
        session_repo.save(s2)

        active = session_repo.get_active_session(SourceId(value=100))
        assert active is not None
        assert active.id.value == "anon_new"
        assert active.is_reversible()

    def test_mark_reverted(self, session_repo):
        """Test marking a session as reverted."""
        session = AnonymizationSession(
            id=AnonymizationSessionId(value="anon_test"),
            source_id=SourceId(value=100),
            original_text="Test",
            pseudonym_ids=(),
            replacements=(),
        )
        session_repo.save(session)

        session_repo.mark_reverted(AnonymizationSessionId(value="anon_test"))

        retrieved = session_repo.get_by_id(AnonymizationSessionId(value="anon_test"))
        assert retrieved.reverted_at is not None
        assert not retrieved.is_reversible()
