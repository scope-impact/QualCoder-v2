"""
Tests for Privacy domain derivers.

TDD tests written BEFORE implementation.
Derivers are pure functions that validate and produce domain events.
"""

from __future__ import annotations

import pytest

from src.domain.shared.types import Failure


class TestDeriveCreatePseudonym:
    """Tests for derive_create_pseudonym deriver."""

    def test_creates_pseudonym_with_valid_inputs(self, empty_privacy_state):
        """Should create PseudonymCreated event with valid inputs."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.events import PseudonymCreated

        result = derive_create_pseudonym(
            real_name="John Smith",
            alias="Participant A",
            category="person",
            notes="Interview subject",
            state=empty_privacy_state,
        )

        assert isinstance(result, PseudonymCreated)
        assert result.real_name == "John Smith"
        assert result.alias == "Participant A"
        assert result.category == "person"

    def test_fails_with_empty_real_name(self, empty_privacy_state):
        """Should fail with empty real name."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.types import EmptyRealName

        result = derive_create_pseudonym(
            real_name="",
            alias="Participant A",
            category="person",
            notes=None,
            state=empty_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyRealName)

    def test_fails_with_empty_alias(self, empty_privacy_state):
        """Should fail with empty alias."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.types import EmptyAlias

        result = derive_create_pseudonym(
            real_name="John Smith",
            alias="",
            category="person",
            notes=None,
            state=empty_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyAlias)

    def test_fails_with_duplicate_real_name(self, populated_privacy_state):
        """Should fail with duplicate real name."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.types import DuplicateRealName

        result = derive_create_pseudonym(
            real_name="John Smith",  # Already exists
            alias="New Alias",
            category="person",
            notes=None,
            state=populated_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateRealName)

    def test_fails_with_duplicate_alias(self, populated_privacy_state):
        """Should fail with duplicate alias."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.types import DuplicateAlias

        result = derive_create_pseudonym(
            real_name="New Person",
            alias="Participant A",  # Already exists
            category="person",
            notes=None,
            state=populated_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateAlias)

    def test_creates_with_all_categories(self, empty_privacy_state):
        """Should create pseudonyms for all category types."""
        from src.domain.privacy.derivers import derive_create_pseudonym
        from src.domain.privacy.events import PseudonymCreated

        categories = ["person", "organization", "location", "date", "other"]

        for category in categories:
            result = derive_create_pseudonym(
                real_name=f"Test {category}",
                alias=f"Alias {category}",
                category=category,
                notes=None,
                state=empty_privacy_state,
            )
            assert isinstance(result, PseudonymCreated), f"Failed for {category}"


class TestDeriveUpdatePseudonym:
    """Tests for derive_update_pseudonym deriver."""

    def test_updates_alias(self, populated_privacy_state):
        """Should update pseudonym alias."""
        from src.domain.privacy.derivers import derive_update_pseudonym
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymUpdated

        result = derive_update_pseudonym(
            pseudonym_id=PseudonymId(value=1),
            new_alias="Updated Alias",
            new_notes=None,
            state=populated_privacy_state,
        )

        assert isinstance(result, PseudonymUpdated)
        assert result.new_alias == "Updated Alias"

    def test_fails_for_nonexistent_pseudonym(self, populated_privacy_state):
        """Should fail for nonexistent pseudonym."""
        from src.domain.privacy.derivers import derive_update_pseudonym
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.types import PseudonymNotFound

        result = derive_update_pseudonym(
            pseudonym_id=PseudonymId(value=999),
            new_alias="New Alias",
            new_notes=None,
            state=populated_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), PseudonymNotFound)

    def test_fails_with_duplicate_alias(self, populated_privacy_state):
        """Should fail when updating to existing alias."""
        from src.domain.privacy.derivers import derive_update_pseudonym
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.types import DuplicateAlias

        result = derive_update_pseudonym(
            pseudonym_id=PseudonymId(value=1),
            new_alias="Participant B",  # Already used by pseudonym 2
            new_notes=None,
            state=populated_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateAlias)


class TestDeriveDeletePseudonym:
    """Tests for derive_delete_pseudonym deriver."""

    def test_deletes_existing_pseudonym(self, populated_privacy_state):
        """Should delete existing pseudonym."""
        from src.domain.privacy.derivers import derive_delete_pseudonym
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.events import PseudonymDeleted

        result = derive_delete_pseudonym(
            pseudonym_id=PseudonymId(value=1),
            state=populated_privacy_state,
        )

        assert isinstance(result, PseudonymDeleted)
        assert result.pseudonym_id.value == 1

    def test_fails_for_nonexistent_pseudonym(self, populated_privacy_state):
        """Should fail for nonexistent pseudonym."""
        from src.domain.privacy.derivers import derive_delete_pseudonym
        from src.domain.privacy.entities import PseudonymId
        from src.domain.privacy.types import PseudonymNotFound

        result = derive_delete_pseudonym(
            pseudonym_id=PseudonymId(value=999),
            state=populated_privacy_state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), PseudonymNotFound)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def empty_privacy_state():
    """Create empty PrivacyState for testing."""
    from src.domain.privacy.derivers import PrivacyState

    return PrivacyState(
        existing_pseudonyms=(),
        existing_sessions=(),
    )


@pytest.fixture
def populated_privacy_state():
    """Create PrivacyState with sample data."""
    from src.domain.privacy.derivers import PrivacyState
    from src.domain.privacy.entities import (
        Pseudonym,
        PseudonymCategory,
        PseudonymId,
    )

    pseudonyms = (
        Pseudonym(
            id=PseudonymId(value=1),
            real_name="John Smith",
            alias="Participant A",
            category=PseudonymCategory.PERSON,
        ),
        Pseudonym(
            id=PseudonymId(value=2),
            real_name="Acme Corp",
            alias="Participant B",
            category=PseudonymCategory.ORGANIZATION,
        ),
    )

    return PrivacyState(
        existing_pseudonyms=pseudonyms,
        existing_sessions=(),
    )
