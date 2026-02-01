"""
References Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestDeriveAddReference:
    """Tests for derive_add_reference deriver."""

    def test_creates_reference_with_valid_inputs(self):
        """Should create ReferenceAdded event with valid inputs."""
        from src.domain.references.derivers import ReferenceState, derive_add_reference
        from src.domain.references.events import ReferenceAdded

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="The Logic of Scientific Discovery",
            authors="Karl Popper",
            year=1959,
            doi="10.1234/example",
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, ReferenceAdded)
        assert result.title == "The Logic of Scientific Discovery"
        assert result.authors == "Karl Popper"
        assert result.year == 1959

    def test_creates_reference_without_optional_fields(self):
        """Should create ReferenceAdded event without optional fields."""
        from src.domain.references.derivers import ReferenceState, derive_add_reference
        from src.domain.references.events import ReferenceAdded

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="Minimal Reference",
            authors="Author Name",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, ReferenceAdded)
        assert result.title == "Minimal Reference"
        assert result.year is None

    def test_fails_with_empty_title(self):
        """Should fail with EmptyTitle for empty titles."""
        from src.domain.references.derivers import (
            EmptyTitle,
            ReferenceState,
            derive_add_reference,
        )
        from src.domain.shared.types import Failure

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="",
            authors="Author Name",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyTitle)

    def test_fails_with_empty_authors(self):
        """Should fail with EmptyAuthors for empty authors."""
        from src.domain.references.derivers import (
            EmptyAuthors,
            ReferenceState,
            derive_add_reference,
        )
        from src.domain.shared.types import Failure

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="Valid Title",
            authors="",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyAuthors)

    def test_fails_with_invalid_year(self):
        """Should fail with InvalidYear for future years."""
        from src.domain.references.derivers import (
            InvalidYear,
            ReferenceState,
            derive_add_reference,
        )
        from src.domain.shared.types import Failure

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="Some Title",
            authors="Some Author",
            year=2100,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidYear)

    def test_fails_with_invalid_doi(self):
        """Should fail with InvalidDoi for malformed DOI."""
        from src.domain.references.derivers import (
            InvalidDoi,
            ReferenceState,
            derive_add_reference,
        )
        from src.domain.shared.types import Failure

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="Some Title",
            authors="Some Author",
            year=2023,
            doi="invalid-doi-format",
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidDoi)

    def test_strips_whitespace_from_title(self):
        """Should strip whitespace from title."""
        from src.domain.references.derivers import ReferenceState, derive_add_reference
        from src.domain.references.events import ReferenceAdded

        state = ReferenceState(existing_references=())

        result = derive_add_reference(
            title="  Padded Title  ",
            authors="Author",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, ReferenceAdded)
        assert result.title == "Padded Title"


class TestDeriveUpdateReference:
    """Tests for derive_update_reference deriver."""

    def test_updates_reference_with_valid_inputs(self):
        """Should create ReferenceUpdated event with valid inputs."""
        from src.domain.references.derivers import ReferenceState, derive_update_reference
        from src.domain.references.entities import Reference
        from src.domain.references.events import ReferenceUpdated
        from src.domain.shared.types import ReferenceId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Original Title",
                authors="Original Author",
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_update_reference(
            reference_id=ReferenceId(value=1),
            title="Updated Title",
            authors="Updated Author",
            year=2024,
            doi=None,
            source=None,
            url=None,
            memo="New memo",
            state=state,
        )

        assert isinstance(result, ReferenceUpdated)
        assert result.reference_id == ReferenceId(value=1)
        assert result.title == "Updated Title"

    def test_fails_when_reference_not_found(self):
        """Should fail with ReferenceNotFound for non-existent reference."""
        from src.domain.references.derivers import (
            ReferenceNotFound,
            ReferenceState,
            derive_update_reference,
        )
        from src.domain.shared.types import Failure, ReferenceId

        state = ReferenceState(existing_references=())

        result = derive_update_reference(
            reference_id=ReferenceId(value=999),
            title="New Title",
            authors="Author",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceNotFound)

    def test_fails_with_empty_title(self):
        """Should fail with EmptyTitle for empty title."""
        from src.domain.references.derivers import (
            EmptyTitle,
            ReferenceState,
            derive_update_reference,
        )
        from src.domain.references.entities import Reference
        from src.domain.shared.types import Failure, ReferenceId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Original",
                authors="Author",
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_update_reference(
            reference_id=ReferenceId(value=1),
            title="",
            authors="Author",
            year=None,
            doi=None,
            source=None,
            url=None,
            memo=None,
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyTitle)


class TestDeriveRemoveReference:
    """Tests for derive_remove_reference deriver."""

    def test_removes_existing_reference(self):
        """Should create ReferenceRemoved event for existing reference."""
        from src.domain.references.derivers import ReferenceState, derive_remove_reference
        from src.domain.references.entities import Reference
        from src.domain.references.events import ReferenceRemoved
        from src.domain.shared.types import ReferenceId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="To Delete",
                authors="Author",
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_remove_reference(
            reference_id=ReferenceId(value=1),
            state=state,
        )

        assert isinstance(result, ReferenceRemoved)
        assert result.reference_id == ReferenceId(value=1)

    def test_fails_when_reference_not_found(self):
        """Should fail with ReferenceNotFound for non-existent reference."""
        from src.domain.references.derivers import (
            ReferenceNotFound,
            ReferenceState,
            derive_remove_reference,
        )
        from src.domain.shared.types import Failure, ReferenceId

        state = ReferenceState(existing_references=())

        result = derive_remove_reference(
            reference_id=ReferenceId(value=999),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceNotFound)


class TestDeriveLinkReferenceToSegment:
    """Tests for derive_link_reference_to_segment deriver."""

    def test_links_reference_to_segment(self):
        """Should create ReferenceLinkedToSegment event."""
        from src.domain.references.derivers import (
            ReferenceState,
            derive_link_reference_to_segment,
        )
        from src.domain.references.entities import Reference
        from src.domain.references.events import ReferenceLinkedToSegment
        from src.domain.shared.types import ReferenceId, SegmentId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Reference",
                authors="Author",
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_link_reference_to_segment(
            reference_id=ReferenceId(value=1),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, ReferenceLinkedToSegment)
        assert result.reference_id == ReferenceId(value=1)
        assert result.segment_id == SegmentId(value=100)

    def test_fails_when_reference_not_found(self):
        """Should fail with ReferenceNotFound for non-existent reference."""
        from src.domain.references.derivers import (
            ReferenceNotFound,
            ReferenceState,
            derive_link_reference_to_segment,
        )
        from src.domain.shared.types import Failure, ReferenceId, SegmentId

        state = ReferenceState(existing_references=())

        result = derive_link_reference_to_segment(
            reference_id=ReferenceId(value=999),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceNotFound)

    def test_fails_when_already_linked(self):
        """Should fail when reference is already linked to segment."""
        from src.domain.references.derivers import (
            ReferenceAlreadyLinked,
            ReferenceState,
            derive_link_reference_to_segment,
        )
        from src.domain.references.entities import Reference
        from src.domain.shared.types import Failure, ReferenceId, SegmentId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Reference",
                authors="Author",
                segment_ids=(100,),  # Already linked to segment 100
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_link_reference_to_segment(
            reference_id=ReferenceId(value=1),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceAlreadyLinked)


class TestDeriveUnlinkReferenceFromSegment:
    """Tests for derive_unlink_reference_from_segment deriver."""

    def test_unlinks_reference_from_segment(self):
        """Should create ReferenceUnlinkedFromSegment event."""
        from src.domain.references.derivers import (
            ReferenceState,
            derive_unlink_reference_from_segment,
        )
        from src.domain.references.entities import Reference
        from src.domain.references.events import ReferenceUnlinkedFromSegment
        from src.domain.shared.types import ReferenceId, SegmentId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Reference",
                authors="Author",
                segment_ids=(100,),  # Linked to segment 100
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_unlink_reference_from_segment(
            reference_id=ReferenceId(value=1),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, ReferenceUnlinkedFromSegment)
        assert result.reference_id == ReferenceId(value=1)
        assert result.segment_id == SegmentId(value=100)

    def test_fails_when_reference_not_found(self):
        """Should fail with ReferenceNotFound for non-existent reference."""
        from src.domain.references.derivers import (
            ReferenceNotFound,
            ReferenceState,
            derive_unlink_reference_from_segment,
        )
        from src.domain.shared.types import Failure, ReferenceId, SegmentId

        state = ReferenceState(existing_references=())

        result = derive_unlink_reference_from_segment(
            reference_id=ReferenceId(value=999),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceNotFound)

    def test_fails_when_not_linked(self):
        """Should fail when reference is not linked to segment."""
        from src.domain.references.derivers import (
            ReferenceNotLinked,
            ReferenceState,
            derive_unlink_reference_from_segment,
        )
        from src.domain.references.entities import Reference
        from src.domain.shared.types import Failure, ReferenceId, SegmentId

        existing = (
            Reference(
                id=ReferenceId(value=1),
                title="Reference",
                authors="Author",
                segment_ids=(),  # Not linked to any segment
            ),
        )
        state = ReferenceState(existing_references=existing)

        result = derive_unlink_reference_from_segment(
            reference_id=ReferenceId(value=1),
            segment_id=SegmentId(value=100),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ReferenceNotLinked)
