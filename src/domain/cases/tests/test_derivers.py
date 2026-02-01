"""
Cases Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestDeriveCreateCase:
    """Tests for derive_create_case deriver."""

    def test_creates_case_with_valid_inputs(self):
        """Should create CaseCreated event with valid inputs."""
        from src.domain.cases.derivers import CaseState, derive_create_case
        from src.domain.cases.events import CaseCreated

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="Participant A",
            description="First interview subject",
            memo="Recruited from university",
            state=state,
        )

        assert isinstance(result, CaseCreated)
        assert result.name == "Participant A"
        assert result.description == "First interview subject"
        assert result.memo == "Recruited from university"

    def test_fails_with_empty_name(self):
        """Should fail with EmptyCaseName for empty case names."""
        from src.domain.cases.derivers import (
            CaseState,
            EmptyCaseName,
            derive_create_case,
        )
        from src.domain.shared.types import Failure

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyCaseName)

    def test_fails_with_whitespace_name(self):
        """Should fail with EmptyCaseName for whitespace-only names."""
        from src.domain.cases.derivers import (
            CaseState,
            EmptyCaseName,
            derive_create_case,
        )
        from src.domain.shared.types import Failure

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="   ",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyCaseName)

    def test_fails_with_duplicate_name(self):
        """Should fail with DuplicateCaseName for existing case name."""
        from src.domain.cases.derivers import (
            CaseState,
            DuplicateCaseName,
            derive_create_case,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure

        existing = (
            Case(
                id=CaseId(value=1),
                name="Participant A",
            ),
        )

        state = CaseState(existing_cases=existing)

        result = derive_create_case(
            name="Participant A",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateCaseName)

    def test_fails_with_name_too_long(self):
        """Should fail with CaseNameTooLong for names exceeding 100 chars."""
        from src.domain.cases.derivers import (
            CaseNameTooLong,
            CaseState,
            derive_create_case,
        )
        from src.domain.shared.types import Failure

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="a" * 101,
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNameTooLong)


class TestDeriveUpdateCase:
    """Tests for derive_update_case deriver."""

    def test_updates_case_with_valid_inputs(self):
        """Should create CaseUpdated event with valid inputs."""
        from src.domain.cases.derivers import CaseState, derive_update_case
        from src.domain.cases.entities import Case
        from src.domain.cases.events import CaseUpdated
        from src.domain.shared.types import CaseId

        existing = (
            Case(
                id=CaseId(value=1),
                name="Participant A",
            ),
        )
        state = CaseState(existing_cases=existing)

        result = derive_update_case(
            case_id=CaseId(value=1),
            name="Participant A - Updated",
            description="Updated description",
            memo="New memo",
            state=state,
        )

        assert isinstance(result, CaseUpdated)
        assert result.case_id == CaseId(value=1)
        assert result.name == "Participant A - Updated"
        assert result.description == "Updated description"

    def test_fails_when_case_not_found(self):
        """Should fail with CaseNotFound for non-existent case."""
        from src.domain.cases.derivers import (
            CaseNotFound,
            CaseState,
            derive_update_case,
        )
        from src.domain.shared.types import CaseId, Failure

        state = CaseState(existing_cases=())

        result = derive_update_case(
            case_id=CaseId(value=999),
            name="New Name",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNotFound)

    def test_fails_with_duplicate_name_on_rename(self):
        """Should fail when renaming to existing case name."""
        from src.domain.cases.derivers import (
            CaseState,
            DuplicateCaseName,
            derive_update_case,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure

        existing = (
            Case(id=CaseId(value=1), name="Participant A"),
            Case(id=CaseId(value=2), name="Participant B"),
        )
        state = CaseState(existing_cases=existing)

        result = derive_update_case(
            case_id=CaseId(value=1),
            name="Participant B",  # Conflicts with case 2
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateCaseName)

    def test_allows_same_name_on_update(self):
        """Should allow keeping the same name when updating other fields."""
        from src.domain.cases.derivers import CaseState, derive_update_case
        from src.domain.cases.entities import Case
        from src.domain.cases.events import CaseUpdated
        from src.domain.shared.types import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_update_case(
            case_id=CaseId(value=1),
            name="Participant A",  # Same name is OK
            description="New description",
            memo=None,
            state=state,
        )

        assert isinstance(result, CaseUpdated)


class TestDeriveRemoveCase:
    """Tests for derive_remove_case deriver."""

    def test_removes_existing_case(self):
        """Should create CaseRemoved event for existing case."""
        from src.domain.cases.derivers import CaseState, derive_remove_case
        from src.domain.cases.entities import Case
        from src.domain.cases.events import CaseRemoved
        from src.domain.shared.types import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_remove_case(
            case_id=CaseId(value=1),
            state=state,
        )

        assert isinstance(result, CaseRemoved)
        assert result.case_id == CaseId(value=1)

    def test_fails_when_case_not_found(self):
        """Should fail with CaseNotFound for non-existent case."""
        from src.domain.cases.derivers import (
            CaseNotFound,
            CaseState,
            derive_remove_case,
        )
        from src.domain.shared.types import CaseId, Failure

        state = CaseState(existing_cases=())

        result = derive_remove_case(
            case_id=CaseId(value=999),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNotFound)


class TestDeriveSetCaseAttribute:
    """Tests for derive_set_case_attribute deriver."""

    def test_sets_attribute_on_existing_case(self):
        """Should create CaseAttributeSet event with valid inputs."""
        from src.domain.cases.derivers import CaseState, derive_set_case_attribute
        from src.domain.cases.entities import Case
        from src.domain.cases.events import CaseAttributeSet
        from src.domain.shared.types import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="age",
            attr_type="number",
            attr_value=25,
            state=state,
        )

        assert isinstance(result, CaseAttributeSet)
        assert result.case_id == CaseId(value=1)
        assert result.attr_name == "age"
        assert result.attr_type == "number"
        assert result.attr_value == 25

    def test_fails_when_case_not_found(self):
        """Should fail with CaseNotFound for non-existent case."""
        from src.domain.cases.derivers import (
            CaseNotFound,
            CaseState,
            derive_set_case_attribute,
        )
        from src.domain.shared.types import CaseId, Failure

        state = CaseState(existing_cases=())

        result = derive_set_case_attribute(
            case_id=CaseId(value=999),
            attr_name="age",
            attr_type="number",
            attr_value=25,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNotFound)

    def test_fails_with_invalid_attribute_type(self):
        """Should fail with InvalidAttributeType for unknown types."""
        from src.domain.cases.derivers import (
            CaseState,
            InvalidAttributeType,
            derive_set_case_attribute,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="age",
            attr_type="unknown_type",
            attr_value=25,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidAttributeType)

    def test_fails_with_invalid_attribute_value(self):
        """Should fail with InvalidAttributeValue for type mismatch."""
        from src.domain.cases.derivers import (
            CaseState,
            InvalidAttributeValue,
            derive_set_case_attribute,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="age",
            attr_type="number",
            attr_value="not-a-number",
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidAttributeValue)

    def test_fails_with_empty_attribute_name(self):
        """Should fail with InvalidAttributeName for empty names."""
        from src.domain.cases.derivers import (
            CaseState,
            InvalidAttributeName,
            derive_set_case_attribute,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="",
            attr_type="text",
            attr_value="value",
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidAttributeName)


class TestDeriveLinkSourceToCase:
    """Tests for derive_link_source_to_case deriver."""

    def test_links_source_to_case(self):
        """Should create SourceLinkedToCase event with valid inputs."""
        from src.domain.cases.derivers import CaseState, derive_link_source_to_case
        from src.domain.cases.entities import Case
        from src.domain.cases.events import SourceLinkedToCase
        from src.domain.shared.types import CaseId, SourceId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_link_source_to_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceLinkedToCase)
        assert result.case_id == CaseId(value=1)
        assert result.source_id == 10

    def test_fails_when_case_not_found(self):
        """Should fail with CaseNotFound for non-existent case."""
        from src.domain.cases.derivers import (
            CaseNotFound,
            CaseState,
            derive_link_source_to_case,
        )
        from src.domain.shared.types import CaseId, Failure, SourceId

        state = CaseState(existing_cases=())

        result = derive_link_source_to_case(
            case_id=CaseId(value=999),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNotFound)

    def test_fails_when_source_already_linked(self):
        """Should fail when source is already linked to case."""
        from src.domain.cases.derivers import (
            CaseState,
            SourceAlreadyLinked,
            derive_link_source_to_case,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure, SourceId

        # Case with source already linked
        existing = (Case(id=CaseId(value=1), name="Participant A", source_ids=(10,)),)
        state = CaseState(existing_cases=existing)

        result = derive_link_source_to_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), SourceAlreadyLinked)


class TestDeriveUnlinkSourceFromCase:
    """Tests for derive_unlink_source_from_case deriver."""

    def test_unlinks_source_from_case(self):
        """Should create SourceUnlinkedFromCase event with valid inputs."""
        from src.domain.cases.derivers import CaseState, derive_unlink_source_from_case
        from src.domain.cases.entities import Case
        from src.domain.cases.events import SourceUnlinkedFromCase
        from src.domain.shared.types import CaseId, SourceId

        # Case with source linked
        existing = (Case(id=CaseId(value=1), name="Participant A", source_ids=(10,)),)
        state = CaseState(existing_cases=existing)

        result = derive_unlink_source_from_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceUnlinkedFromCase)
        assert result.case_id == CaseId(value=1)
        assert result.source_id == 10

    def test_fails_when_case_not_found(self):
        """Should fail with CaseNotFound for non-existent case."""
        from src.domain.cases.derivers import (
            CaseNotFound,
            CaseState,
            derive_unlink_source_from_case,
        )
        from src.domain.shared.types import CaseId, Failure, SourceId

        state = CaseState(existing_cases=())

        result = derive_unlink_source_from_case(
            case_id=CaseId(value=999),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), CaseNotFound)

    def test_fails_when_source_not_linked(self):
        """Should fail when source is not linked to case."""
        from src.domain.cases.derivers import (
            CaseState,
            SourceNotLinked,
            derive_unlink_source_from_case,
        )
        from src.domain.cases.entities import Case
        from src.domain.shared.types import CaseId, Failure, SourceId

        # Case without source linked
        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_unlink_source_from_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), SourceNotLinked)
