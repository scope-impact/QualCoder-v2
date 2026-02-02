"""
Case Repository Tests.

Tests for SQLiteCaseRepository including source linking functionality.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.contexts.cases.core.entities import Case
from src.contexts.shared.core.types import CaseId, SourceId

pytestmark = pytest.mark.integration


class TestCaseRepositorySourceLinking:
    """Tests for source linking functionality in CaseRepository."""

    def test_link_source_to_case(self, case_repo):
        """Should link a source to a case."""
        # Create a case first
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Link source to case
        case_repo.link_source(CaseId(value=1), SourceId(value=10))

        # Verify link exists
        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert 10 in source_ids

    def test_link_multiple_sources_to_case(self, case_repo):
        """Should link multiple sources to a case."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Link multiple sources
        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.link_source(CaseId(value=1), SourceId(value=20))
        case_repo.link_source(CaseId(value=1), SourceId(value=30))

        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert len(source_ids) == 3
        assert set(source_ids) == {10, 20, 30}

    def test_link_source_is_idempotent(self, case_repo):
        """Should not create duplicate links."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Link same source twice
        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.link_source(CaseId(value=1), SourceId(value=10))

        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert source_ids.count(10) == 1

    def test_unlink_source_from_case(self, case_repo):
        """Should unlink a source from a case."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Link then unlink
        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.unlink_source(CaseId(value=1), SourceId(value=10))

        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert 10 not in source_ids

    def test_unlink_preserves_other_links(self, case_repo):
        """Should only unlink the specified source."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Link multiple sources
        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.link_source(CaseId(value=1), SourceId(value=20))
        case_repo.link_source(CaseId(value=1), SourceId(value=30))

        # Unlink one
        case_repo.unlink_source(CaseId(value=1), SourceId(value=20))

        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert 10 in source_ids
        assert 20 not in source_ids
        assert 30 in source_ids

    def test_unlink_nonexistent_is_noop(self, case_repo):
        """Should not fail when unlinking a non-linked source."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Unlink source that was never linked - should not raise
        case_repo.unlink_source(CaseId(value=1), SourceId(value=999))

        # No error means test passed

    def test_get_source_ids_returns_empty_for_no_links(self, case_repo):
        """Should return empty list when no sources linked."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert source_ids == []

    def test_get_source_ids_for_nonexistent_case(self, case_repo):
        """Should return empty list for non-existent case."""
        source_ids = case_repo.get_source_ids(CaseId(value=999))
        assert source_ids == []

    def test_is_source_linked(self, case_repo):
        """Should check if a source is linked to a case."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.link_source(CaseId(value=1), SourceId(value=10))

        assert case_repo.is_source_linked(CaseId(value=1), SourceId(value=10)) is True
        assert case_repo.is_source_linked(CaseId(value=1), SourceId(value=20)) is False

    def test_delete_case_removes_source_links(self, case_repo):
        """Should remove all source links when case is deleted."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.link_source(CaseId(value=1), SourceId(value=20))

        # Delete case
        case_repo.delete(CaseId(value=1))

        # Verify links are removed
        source_ids = case_repo.get_source_ids(CaseId(value=1))
        assert source_ids == []

    def test_get_case_includes_source_ids(self, case_repo):
        """Should include source_ids when retrieving a case."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.link_source(CaseId(value=1), SourceId(value=10))
        case_repo.link_source(CaseId(value=1), SourceId(value=20))

        retrieved = case_repo.get_by_id(CaseId(value=1))

        assert retrieved is not None
        assert 10 in retrieved.source_ids
        assert 20 in retrieved.source_ids


class TestCaseRepositoryAttributes:
    """Tests for case attribute functionality in CaseRepository."""

    def test_save_attribute_to_case(self, case_repo):
        """Should save an attribute to a case."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Save attribute
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )

        # Verify attribute is saved
        retrieved = case_repo.get_by_id(CaseId(value=1))
        assert retrieved is not None
        assert len(retrieved.attributes) == 1
        assert retrieved.attributes[0].name == "age"
        assert retrieved.attributes[0].value == 25

    def test_save_multiple_attributes(self, case_repo):
        """Should save multiple attributes to a case."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
        )
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="employed", attr_type=AttributeType.BOOLEAN, value=True),
        )

        retrieved = case_repo.get_by_id(CaseId(value=1))
        assert retrieved is not None
        assert len(retrieved.attributes) == 3

    def test_update_existing_attribute(self, case_repo):
        """Should update an existing attribute with the same name."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        # Save initial attribute
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )

        # Update attribute
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=26),
        )

        retrieved = case_repo.get_by_id(CaseId(value=1))
        assert retrieved is not None
        assert len(retrieved.attributes) == 1
        assert retrieved.attributes[0].value == 26

    def test_delete_attribute(self, case_repo):
        """Should delete an attribute from a case."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )
        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
        )

        # Delete one attribute
        case_repo.delete_attribute(CaseId(value=1), "age")

        retrieved = case_repo.get_by_id(CaseId(value=1))
        assert retrieved is not None
        assert len(retrieved.attributes) == 1
        assert retrieved.attributes[0].name == "gender"

    def test_get_attribute(self, case_repo):
        """Should get a specific attribute by name."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )

        attr = case_repo.get_attribute(CaseId(value=1), "age")
        assert attr is not None
        assert attr.name == "age"
        assert attr.value == 25

    def test_get_attribute_returns_none_for_nonexistent(self, case_repo):
        """Should return None for non-existent attribute."""
        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        attr = case_repo.get_attribute(CaseId(value=1), "nonexistent")
        assert attr is None

    def test_delete_case_removes_attributes(self, case_repo):
        """Should remove all attributes when case is deleted."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )

        case_repo.delete(CaseId(value=1))

        # Trying to get attribute should return None
        attr = case_repo.get_attribute(CaseId(value=1), "age")
        assert attr is None

    def test_get_all_cases_includes_attributes(self, case_repo):
        """Should include attributes when getting all cases."""
        from src.contexts.cases.core.entities import AttributeType, CaseAttribute

        case = Case(
            id=CaseId(value=1),
            name="Participant A",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(case)

        case_repo.save_attribute(
            CaseId(value=1),
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
        )

        cases = case_repo.get_all()
        assert len(cases) == 1
        assert len(cases[0].attributes) == 1
        assert cases[0].attributes[0].name == "age"
