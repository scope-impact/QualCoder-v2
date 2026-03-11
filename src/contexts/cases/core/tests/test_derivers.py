"""
Cases Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
Derivers return success events or failure events directly (per SKILL.md).
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.cases.core.derivers import CaseState, derive_create_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseCreated
from src.contexts.cases.core.failure_events import CaseCreationFailed
from src.shared import CaseId, SourceId

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-034 Manage Cases"),
]


@allure.story("QC-034.03 Case Attributes")
class TestDeriveCreateCase:
    """Tests for derive_create_case deriver."""

    @allure.title("Creates case with valid inputs")
    def test_creates_case_with_valid_inputs(self):
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

    @allure.title("Fails with invalid or duplicate names")
    @pytest.mark.parametrize(
        "name, existing_cases, expected_reason",
        [
            pytest.param("", (), "EMPTY_NAME", id="empty-name"),
            pytest.param("   ", (), "EMPTY_NAME", id="whitespace-name"),
            pytest.param("a" * 101, (), "NAME_TOO_LONG", id="name-too-long"),
            pytest.param(
                "Participant A",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                "DUPLICATE_NAME",
                id="duplicate-name",
            ),
        ],
    )
    def test_fails_with_invalid_name(self, name, existing_cases, expected_reason):
        state = CaseState(existing_cases=existing_cases)
        result = derive_create_case(name=name, description=None, memo=None, state=state)

        assert isinstance(result, CaseCreationFailed)
        assert result.reason == expected_reason


@allure.story("QC-034.03 Case Attributes")
class TestDeriveUpdateCase:
    """Tests for derive_update_case deriver."""

    @allure.title("Updates case or fails with invalid input")
    @pytest.mark.parametrize(
        "case_id, name, existing_cases, expect_success, expected_reason",
        [
            pytest.param(
                "1", "Participant A - Updated",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                True, None, id="rename",
            ),
            pytest.param(
                "1", "Participant A",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                True, None, id="same-name",
            ),
            pytest.param("999", "New Name", (), False, "NOT_FOUND", id="not-found"),
            pytest.param(
                "1", "Participant B",
                (
                    Case(id=CaseId(value="1"), name="Participant A"),
                    Case(id=CaseId(value="2"), name="Participant B"),
                ),
                False, "DUPLICATE_NAME", id="duplicate-on-rename",
            ),
        ],
    )
    def test_update_case(self, case_id, name, existing_cases, expect_success, expected_reason):
        from src.contexts.cases.core.derivers import derive_update_case
        from src.contexts.cases.core.events import CaseUpdated
        from src.contexts.cases.core.failure_events import CaseUpdateFailed

        state = CaseState(existing_cases=existing_cases)
        result = derive_update_case(
            case_id=CaseId(value=case_id), name=name, description="desc", memo=None, state=state
        )

        if expect_success:
            assert isinstance(result, CaseUpdated)
            assert result.case_id == CaseId(value=case_id)
            assert result.name == name
        else:
            assert isinstance(result, CaseUpdateFailed)
            assert result.reason == expected_reason


@allure.story("QC-034.03 Case Attributes")
class TestDeriveRemoveCase:
    """Tests for derive_remove_case deriver."""

    @allure.title("Removes existing case or fails when not found")
    @pytest.mark.parametrize(
        "case_id, existing_cases, success",
        [
            pytest.param(
                "1",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                True,
                id="existing-case",
            ),
            pytest.param("999", (), False, id="not-found"),
        ],
    )
    def test_remove_case(self, case_id, existing_cases, success):
        from src.contexts.cases.core.derivers import derive_remove_case
        from src.contexts.cases.core.events import CaseRemoved
        from src.contexts.cases.core.failure_events import CaseDeletionFailed

        state = CaseState(existing_cases=existing_cases)
        result = derive_remove_case(case_id=CaseId(value=case_id), state=state)

        if success:
            assert isinstance(result, CaseRemoved)
            assert result.case_id == CaseId(value=case_id)
        else:
            assert isinstance(result, CaseDeletionFailed)
            assert result.reason == "NOT_FOUND"


@allure.story("QC-034.03 Case Attributes")
class TestDeriveSetCaseAttribute:
    """Tests for derive_set_case_attribute deriver."""

    @allure.title("Sets attribute on existing case or fails with invalid input")
    @pytest.mark.parametrize(
        "case_id, attr_name, attr_type, attr_value, has_case, expect_success, reason",
        [
            pytest.param("1", "age", "number", 25, True, True, None, id="valid"),
            pytest.param("999", "age", "number", 25, False, False, "CASE_NOT_FOUND", id="case-not-found"),
            pytest.param("1", "age", "unknown_type", 25, True, False, "INVALID_TYPE", id="invalid-type"),
            pytest.param("1", "age", "number", "not-a-number", True, False, "INVALID_VALUE", id="invalid-value"),
            pytest.param("1", "", "text", "value", True, False, "INVALID_NAME", id="empty-name"),
        ],
    )
    def test_set_case_attribute(self, case_id, attr_name, attr_type, attr_value, has_case, expect_success, reason):
        from src.contexts.cases.core.derivers import derive_set_case_attribute
        from src.contexts.cases.core.events import CaseAttributeSet
        from src.contexts.cases.core.failure_events import AttributeSetFailed

        existing = (Case(id=CaseId(value="1"), name="Participant A"),) if has_case else ()
        state = CaseState(existing_cases=existing)

        result = derive_set_case_attribute(
            case_id=CaseId(value=case_id),
            attr_name=attr_name,
            attr_type=attr_type,
            attr_value=attr_value,
            state=state,
        )

        if expect_success:
            assert isinstance(result, CaseAttributeSet)
            assert result.case_id == CaseId(value=case_id)
            assert result.attr_name == attr_name
            assert result.attr_type == attr_type
            assert result.attr_value == attr_value
        else:
            assert isinstance(result, AttributeSetFailed)
            assert result.reason == reason


@allure.story("QC-034.03 Case Attributes")
class TestDeriveLinkUnlinkSource:
    """Tests for derive_link_source_to_case and derive_unlink_source_from_case derivers."""

    @allure.title("Links source to case or fails")
    @pytest.mark.parametrize(
        "case_id, existing_cases, expect_success, reason",
        [
            pytest.param(
                "1",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                True, None, id="success",
            ),
            pytest.param("999", (), False, "CASE_NOT_FOUND", id="case-not-found"),
            pytest.param(
                "1",
                (Case(id=CaseId(value="1"), name="Participant A", source_ids=("10",)),),
                False, "ALREADY_LINKED", id="already-linked",
            ),
        ],
    )
    def test_link_source_to_case(self, case_id, existing_cases, expect_success, reason):
        from src.contexts.cases.core.derivers import derive_link_source_to_case
        from src.contexts.cases.core.events import SourceLinkedToCase
        from src.contexts.cases.core.failure_events import SourceLinkFailed

        state = CaseState(existing_cases=existing_cases)
        result = derive_link_source_to_case(
            case_id=CaseId(value=case_id), source_id=SourceId(value="10"), state=state
        )

        if expect_success:
            assert isinstance(result, SourceLinkedToCase)
            assert result.case_id == CaseId(value=case_id)
            assert result.source_id == "10"
        else:
            assert isinstance(result, SourceLinkFailed)
            assert result.reason == reason

    @allure.title("Unlinks source from case or fails")
    @pytest.mark.parametrize(
        "case_id, existing_cases, expect_success, reason",
        [
            pytest.param(
                "1",
                (Case(id=CaseId(value="1"), name="Participant A", source_ids=("10",)),),
                True, None, id="success",
            ),
            pytest.param("999", (), False, "CASE_NOT_FOUND", id="case-not-found"),
            pytest.param(
                "1",
                (Case(id=CaseId(value="1"), name="Participant A"),),
                False, "NOT_LINKED", id="not-linked",
            ),
        ],
    )
    def test_unlink_source_from_case(self, case_id, existing_cases, expect_success, reason):
        from src.contexts.cases.core.derivers import derive_unlink_source_from_case
        from src.contexts.cases.core.events import SourceUnlinkedFromCase
        from src.contexts.cases.core.failure_events import SourceUnlinkFailed

        state = CaseState(existing_cases=existing_cases)
        result = derive_unlink_source_from_case(
            case_id=CaseId(value=case_id), source_id=SourceId(value="10"), state=state
        )

        if expect_success:
            assert isinstance(result, SourceUnlinkedFromCase)
            assert result.case_id == CaseId(value=case_id)
            assert result.source_id == "10"
        else:
            assert isinstance(result, SourceUnlinkFailed)
            assert result.reason == reason
