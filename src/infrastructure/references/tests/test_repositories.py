"""
Reference Repository Tests.

Tests for SQLiteReferenceRepository including segment linking functionality.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.references.entities import Reference
from src.domain.shared.types import ReferenceId, SegmentId

pytestmark = pytest.mark.integration


class TestReferenceRepositoryBasic:
    """Tests for basic CRUD operations in ReferenceRepository."""

    def test_save_and_retrieve_reference(self, ref_repo):
        """Should save and retrieve a reference."""
        reference = Reference(
            id=ReferenceId(value=1),
            title="The Logic of Scientific Discovery",
            authors="Karl Popper",
            year=1959,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        ref_repo.save(reference)
        retrieved = ref_repo.get_by_id(ReferenceId(value=1))

        assert retrieved is not None
        assert retrieved.title == "The Logic of Scientific Discovery"
        assert retrieved.authors == "Karl Popper"
        assert retrieved.year == 1959

    def test_save_reference_with_all_fields(self, ref_repo):
        """Should save reference with all optional fields."""
        reference = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Test Author",
            year=2023,
            source="Journal of Testing",
            doi="10.1234/test",
            url="https://example.com",
            memo="This is a test reference",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        ref_repo.save(reference)
        retrieved = ref_repo.get_by_id(ReferenceId(value=1))

        assert retrieved is not None
        assert retrieved.source == "Journal of Testing"
        assert retrieved.doi == "10.1234/test"
        assert retrieved.url == "https://example.com"
        assert retrieved.memo == "This is a test reference"

    def test_get_all_references(self, ref_repo):
        """Should get all saved references."""
        ref1 = Reference(
            id=ReferenceId(value=1),
            title="Reference A",
            authors="Author A",
        )
        ref2 = Reference(
            id=ReferenceId(value=2),
            title="Reference B",
            authors="Author B",
        )

        ref_repo.save(ref1)
        ref_repo.save(ref2)

        all_refs = ref_repo.get_all()
        assert len(all_refs) == 2
        titles = {r.title for r in all_refs}
        assert "Reference A" in titles
        assert "Reference B" in titles

    def test_update_reference(self, ref_repo):
        """Should update an existing reference."""
        reference = Reference(
            id=ReferenceId(value=1),
            title="Original Title",
            authors="Original Author",
        )
        ref_repo.save(reference)

        updated = Reference(
            id=ReferenceId(value=1),
            title="Updated Title",
            authors="Updated Author",
            year=2024,
        )
        ref_repo.save(updated)

        retrieved = ref_repo.get_by_id(ReferenceId(value=1))
        assert retrieved is not None
        assert retrieved.title == "Updated Title"
        assert retrieved.year == 2024

    def test_delete_reference(self, ref_repo):
        """Should delete a reference."""
        reference = Reference(
            id=ReferenceId(value=1),
            title="To Delete",
            authors="Author",
        )
        ref_repo.save(reference)
        assert ref_repo.exists(ReferenceId(value=1)) is True

        ref_repo.delete(ReferenceId(value=1))
        assert ref_repo.exists(ReferenceId(value=1)) is False

    def test_get_nonexistent_reference(self, ref_repo):
        """Should return None for non-existent reference."""
        retrieved = ref_repo.get_by_id(ReferenceId(value=999))
        assert retrieved is None

    def test_exists(self, ref_repo):
        """Should check if reference exists."""
        reference = Reference(
            id=ReferenceId(value=1),
            title="Test",
            authors="Author",
        )
        ref_repo.save(reference)

        assert ref_repo.exists(ReferenceId(value=1)) is True
        assert ref_repo.exists(ReferenceId(value=999)) is False


class TestReferenceRepositorySearch:
    """Tests for search functionality in ReferenceRepository."""

    def test_search_by_title(self, ref_repo):
        """Should search references by title."""
        ref1 = Reference(
            id=ReferenceId(value=1),
            title="Machine Learning Basics",
            authors="Author A",
        )
        ref2 = Reference(
            id=ReferenceId(value=2),
            title="Deep Learning Advanced",
            authors="Author B",
        )
        ref3 = Reference(
            id=ReferenceId(value=3),
            title="Statistics 101",
            authors="Author C",
        )

        ref_repo.save(ref1)
        ref_repo.save(ref2)
        ref_repo.save(ref3)

        results = ref_repo.search_by_title("Learning")
        assert len(results) == 2
        titles = {r.title for r in results}
        assert "Machine Learning Basics" in titles
        assert "Deep Learning Advanced" in titles

    def test_search_by_title_case_insensitive(self, ref_repo):
        """Should search case-insensitively."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Machine Learning",
            authors="Author",
        )
        ref_repo.save(ref)

        results = ref_repo.search_by_title("machine learning")
        assert len(results) == 1

    def test_search_by_title_no_results(self, ref_repo):
        """Should return empty list when no matches."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Machine Learning",
            authors="Author",
        )
        ref_repo.save(ref)

        results = ref_repo.search_by_title("Statistics")
        assert len(results) == 0

    def test_get_by_doi(self, ref_repo):
        """Should get reference by DOI."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
            doi="10.1234/test",
        )
        ref_repo.save(ref)

        retrieved = ref_repo.get_by_doi("10.1234/test")
        assert retrieved is not None
        assert retrieved.title == "Test Reference"

    def test_get_by_doi_not_found(self, ref_repo):
        """Should return None for non-existent DOI."""
        retrieved = ref_repo.get_by_doi("10.9999/nonexistent")
        assert retrieved is None


class TestReferenceRepositorySegmentLinking:
    """Tests for segment linking functionality in ReferenceRepository."""

    def test_link_segment_to_reference(self, ref_repo):
        """Should link a segment to a reference."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert 100 in segment_ids

    def test_link_multiple_segments_to_reference(self, ref_repo):
        """Should link multiple segments to a reference."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=200))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=300))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert len(segment_ids) == 3
        assert set(segment_ids) == {100, 200, 300}

    def test_link_segment_is_idempotent(self, ref_repo):
        """Should not create duplicate links."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert segment_ids.count(100) == 1

    def test_unlink_segment_from_reference(self, ref_repo):
        """Should unlink a segment from a reference."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.unlink_segment(ReferenceId(value=1), SegmentId(value=100))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert 100 not in segment_ids

    def test_unlink_preserves_other_links(self, ref_repo):
        """Should only unlink the specified segment."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=200))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=300))

        ref_repo.unlink_segment(ReferenceId(value=1), SegmentId(value=200))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert 100 in segment_ids
        assert 200 not in segment_ids
        assert 300 in segment_ids

    def test_get_segment_ids_returns_empty_for_no_links(self, ref_repo):
        """Should return empty list when no segments linked."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert segment_ids == []

    def test_delete_reference_removes_segment_links(self, ref_repo):
        """Should remove all segment links when reference is deleted."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=200))

        ref_repo.delete(ReferenceId(value=1))

        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=1))
        assert segment_ids == []

    def test_get_reference_includes_segment_ids(self, ref_repo):
        """Should include segment_ids when retrieving a reference."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))
        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=200))

        retrieved = ref_repo.get_by_id(ReferenceId(value=1))
        assert retrieved is not None
        assert 100 in retrieved.segment_ids
        assert 200 in retrieved.segment_ids

    def test_is_segment_linked(self, ref_repo):
        """Should check if a segment is linked to a reference."""
        ref = Reference(
            id=ReferenceId(value=1),
            title="Test Reference",
            authors="Author",
        )
        ref_repo.save(ref)

        ref_repo.link_segment(ReferenceId(value=1), SegmentId(value=100))

        assert ref_repo.is_segment_linked(ReferenceId(value=1), SegmentId(value=100)) is True
        assert ref_repo.is_segment_linked(ReferenceId(value=1), SegmentId(value=200)) is False
