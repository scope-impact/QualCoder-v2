"""
Cases Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
Derivers return success events or failure events directly (per SKILL.md).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestDeriveCreateCase:
    """Tests for derive_create_case deriver."""

    def test_creates_case_with_valid_inputs(self):
        """Should create CaseCreated event with valid inputs."""
        from src.contexts.cases.core.derivers import CaseState, derive_create_case
        from src.contexts.cases.core.events import CaseCreated

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
        """Should fail with CaseCreationFailed for empty case names."""
        from src.contexts.cases.core.derivers import CaseState, derive_create_case
        from src.contexts.cases.core.failure_events import CaseCreationFailed

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, CaseCreationFailed)
        assert result.reason == "EMPTY_NAME"
        assert "empty" in result.message.lower()

    def test_fails_with_whitespace_name(self):
        """Should fail with CaseCreationFailed for whitespace-only names."""
        from src.contexts.cases.core.derivers import CaseState, derive_create_case
        from src.contexts.cases.core.failure_events import CaseCreationFailed

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="   ",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, CaseCreationFailed)
        assert result.reason == "EMPTY_NAME"

    def test_fails_with_duplicate_name(self):
        """Should fail with CaseCreationFailed for existing case name."""
        from src.contexts.cases.core.derivers import CaseState, derive_create_case
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import CaseCreationFailed
        from src.shared import CaseId

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

        assert isinstance(result, CaseCreationFailed)
        assert result.reason == "DUPLICATE_NAME"
        assert "Participant A" in result.message

    def test_fails_with_name_too_long(self):
        """Should fail with CaseCreationFailed for names exceeding 100 chars."""
        from src.contexts.cases.core.derivers import CaseState, derive_create_case
        from src.contexts.cases.core.failure_events import CaseCreationFailed

        state = CaseState(existing_cases=())

        result = derive_create_case(
            name="a" * 101,
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, CaseCreationFailed)
        assert result.reason == "NAME_TOO_LONG"


class TestDeriveUpdateCase:
    """Tests for derive_update_case deriver."""

    def test_updates_case_with_valid_inputs(self):
        """Should create CaseUpdated event with valid inputs."""
        from src.contexts.cases.core.derivers import CaseState, derive_update_case
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import CaseUpdated
        from src.shared import CaseId

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
        """Should fail with CaseUpdateFailed for non-existent case."""
        from src.contexts.cases.core.derivers import CaseState, derive_update_case
        from src.contexts.cases.core.failure_events import CaseUpdateFailed
        from src.shared import CaseId

        state = CaseState(existing_cases=())

        result = derive_update_case(
            case_id=CaseId(value=999),
            name="New Name",
            description=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, CaseUpdateFailed)
        assert result.reason == "NOT_FOUND"

    def test_fails_with_duplicate_name_on_rename(self):
        """Should fail when renaming to existing case name."""
        from src.contexts.cases.core.derivers import CaseState, derive_update_case
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import CaseUpdateFailed
        from src.shared import CaseId

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

        assert isinstance(result, CaseUpdateFailed)
        assert result.reason == "DUPLICATE_NAME"

    def test_allows_same_name_on_update(self):
        """Should allow keeping the same name when updating other fields."""
        from src.contexts.cases.core.derivers import CaseState, derive_update_case
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import CaseUpdated
        from src.shared import CaseId

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
        from src.contexts.cases.core.derivers import CaseState, derive_remove_case
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import CaseRemoved
        from src.shared import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_remove_case(
            case_id=CaseId(value=1),
            state=state,
        )

        assert isinstance(result, CaseRemoved)
        assert result.case_id == CaseId(value=1)

    def test_fails_when_case_not_found(self):
        """Should fail with CaseDeletionFailed for non-existent case."""
        from src.contexts.cases.core.derivers import CaseState, derive_remove_case
        from src.contexts.cases.core.failure_events import CaseDeletionFailed
        from src.shared import CaseId

        state = CaseState(existing_cases=())

        result = derive_remove_case(
            case_id=CaseId(value=999),
            state=state,
        )

        assert isinstance(result, CaseDeletionFailed)
        assert result.reason == "NOT_FOUND"


class TestDeriveSetCaseAttribute:
    """Tests for derive_set_case_attribute deriver."""

    def test_sets_attribute_on_existing_case(self):
        """Should create CaseAttributeSet event with valid inputs."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_set_case_attribute,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import CaseAttributeSet
        from src.shared import CaseId

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
        """Should fail with AttributeSetFailed for non-existent case."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_set_case_attribute,
        )
        from src.contexts.cases.core.failure_events import AttributeSetFailed
        from src.shared import CaseId

        state = CaseState(existing_cases=())

        result = derive_set_case_attribute(
            case_id=CaseId(value=999),
            attr_name="age",
            attr_type="number",
            attr_value=25,
            state=state,
        )

        assert isinstance(result, AttributeSetFailed)
        assert result.reason == "CASE_NOT_FOUND"

    def test_fails_with_invalid_attribute_type(self):
        """Should fail with AttributeSetFailed for unknown types."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_set_case_attribute,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import AttributeSetFailed
        from src.shared import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="age",
            attr_type="unknown_type",
            attr_value=25,
            state=state,
        )

        assert isinstance(result, AttributeSetFailed)
        assert result.reason == "INVALID_TYPE"

    def test_fails_with_invalid_attribute_value(self):
        """Should fail with AttributeSetFailed for type mismatch."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_set_case_attribute,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import AttributeSetFailed
        from src.shared import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="age",
            attr_type="number",
            attr_value="not-a-number",
            state=state,
        )

        assert isinstance(result, AttributeSetFailed)
        assert result.reason == "INVALID_VALUE"

    def test_fails_with_empty_attribute_name(self):
        """Should fail with AttributeSetFailed for empty names."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_set_case_attribute,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import AttributeSetFailed
        from src.shared import CaseId

        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=1),
            attr_name="",
            attr_type="text",
            attr_value="value",
            state=state,
        )

        assert isinstance(result, AttributeSetFailed)
        assert result.reason == "INVALID_NAME"


class TestDeriveLinkSourceToCase:
    """Tests for derive_link_source_to_case deriver."""

    def test_links_source_to_case(self):
        """Should create SourceLinkedToCase event with valid inputs."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_link_source_to_case,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import SourceLinkedToCase
        from src.shared import CaseId, SourceId

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
        """Should fail with SourceLinkFailed for non-existent case."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_link_source_to_case,
        )
        from src.contexts.cases.core.failure_events import SourceLinkFailed
        from src.shared import CaseId, SourceId

        state = CaseState(existing_cases=())

        result = derive_link_source_to_case(
            case_id=CaseId(value=999),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceLinkFailed)
        assert result.reason == "CASE_NOT_FOUND"

    def test_fails_when_source_already_linked(self):
        """Should fail when source is already linked to case."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_link_source_to_case,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import SourceLinkFailed
        from src.shared import CaseId, SourceId

        # Case with source already linked
        existing = (Case(id=CaseId(value=1), name="Participant A", source_ids=(10,)),)
        state = CaseState(existing_cases=existing)

        result = derive_link_source_to_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceLinkFailed)
        assert result.reason == "ALREADY_LINKED"


class TestDeriveUnlinkSourceFromCase:
    """Tests for derive_unlink_source_from_case deriver."""

    def test_unlinks_source_from_case(self):
        """Should create SourceUnlinkedFromCase event with valid inputs."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_unlink_source_from_case,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.events import SourceUnlinkedFromCase
        from src.shared import CaseId, SourceId

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
        """Should fail with SourceUnlinkFailed for non-existent case."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_unlink_source_from_case,
        )
        from src.contexts.cases.core.failure_events import SourceUnlinkFailed
        from src.shared import CaseId, SourceId

        state = CaseState(existing_cases=())

        result = derive_unlink_source_from_case(
            case_id=CaseId(value=999),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceUnlinkFailed)
        assert result.reason == "CASE_NOT_FOUND"

    def test_fails_when_source_not_linked(self):
        """Should fail when source is not linked to case."""
        from src.contexts.cases.core.derivers import (
            CaseState,
            derive_unlink_source_from_case,
        )
        from src.contexts.cases.core.entities import Case
        from src.contexts.cases.core.failure_events import SourceUnlinkFailed
        from src.shared import CaseId, SourceId

        # Case without source linked
        existing = (Case(id=CaseId(value=1), name="Participant A"),)
        state = CaseState(existing_cases=existing)

        result = derive_unlink_source_from_case(
            case_id=CaseId(value=1),
            source_id=SourceId(value=10),
            state=state,
        )

        assert isinstance(result, SourceUnlinkFailed)
        assert result.reason == "NOT_LINKED"
