"""
References Controller Tests.

Integration tests for ReferencesControllerImpl.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest
from returns.result import Failure, Success

pytestmark = pytest.mark.integration


class TestAddReference:
    """Tests for add_reference command."""

    def test_adds_reference_successfully(self, ref_controller, event_bus):
        """Should add a reference and publish event."""
        from src.application.references.commands import AddReferenceCommand

        command = AddReferenceCommand(
            title="The Logic of Scientific Discovery",
            authors="Karl Popper",
            year=1959,
        )

        result = ref_controller.add_reference(command)

        assert isinstance(result, Success)
        reference = result.unwrap()
        assert reference.title == "The Logic of Scientific Discovery"
        assert reference.authors == "Karl Popper"
        assert reference.year == 1959

        # Verify event was published
        history = event_bus.get_history()
        assert len(history) == 1
        assert "reference_added" in history[0].event_type

    def test_adds_reference_with_all_fields(self, ref_controller):
        """Should add a reference with all optional fields."""
        from src.application.references.commands import AddReferenceCommand

        command = AddReferenceCommand(
            title="Test Reference",
            authors="Test Author",
            year=2023,
            source="Journal of Testing",
            doi="10.1234/test",
            url="https://example.com",
            memo="Test memo",
        )

        result = ref_controller.add_reference(command)

        assert isinstance(result, Success)
        reference = result.unwrap()
        assert reference.source == "Journal of Testing"
        assert reference.doi == "10.1234/test"

    def test_fails_with_empty_title(self, ref_controller):
        """Should fail when title is empty."""
        from src.application.references.commands import AddReferenceCommand

        command = AddReferenceCommand(
            title="",
            authors="Author",
        )

        result = ref_controller.add_reference(command)

        assert isinstance(result, Failure)

    def test_fails_with_empty_authors(self, ref_controller):
        """Should fail when authors is empty."""
        from src.application.references.commands import AddReferenceCommand

        command = AddReferenceCommand(
            title="Valid Title",
            authors="",
        )

        result = ref_controller.add_reference(command)

        assert isinstance(result, Failure)


class TestUpdateReference:
    """Tests for update_reference command."""

    def test_updates_reference_successfully(self, ref_controller, event_bus):
        """Should update a reference and publish event."""
        from src.application.references.commands import (
            AddReferenceCommand,
            UpdateReferenceCommand,
        )

        # Add a reference first
        add_cmd = AddReferenceCommand(
            title="Original Title",
            authors="Original Author",
        )
        add_result = ref_controller.add_reference(add_cmd)
        ref = add_result.unwrap()

        # Update it
        update_cmd = UpdateReferenceCommand(
            reference_id=ref.id.value,
            title="Updated Title",
            authors="Updated Author",
            year=2024,
        )

        result = ref_controller.update_reference(update_cmd)

        assert isinstance(result, Success)
        updated = result.unwrap()
        assert updated.title == "Updated Title"
        assert updated.year == 2024

        # Verify event was published
        history = event_bus.get_history()
        assert len(history) == 2  # add + update
        assert "reference_updated" in history[1].event_type

    def test_fails_when_reference_not_found(self, ref_controller):
        """Should fail when reference doesn't exist."""
        from src.application.references.commands import UpdateReferenceCommand

        command = UpdateReferenceCommand(
            reference_id=999,
            title="New Title",
            authors="Author",
        )

        result = ref_controller.update_reference(command)

        assert isinstance(result, Failure)


class TestRemoveReference:
    """Tests for remove_reference command."""

    def test_removes_reference_successfully(self, ref_controller, event_bus):
        """Should remove a reference and publish event."""
        from src.application.references.commands import (
            AddReferenceCommand,
            RemoveReferenceCommand,
        )

        # Add a reference first
        add_cmd = AddReferenceCommand(
            title="To Delete",
            authors="Author",
        )
        add_result = ref_controller.add_reference(add_cmd)
        ref = add_result.unwrap()

        # Remove it
        remove_cmd = RemoveReferenceCommand(reference_id=ref.id.value)
        result = ref_controller.remove_reference(remove_cmd)

        assert isinstance(result, Success)

        # Verify removed from list
        references = ref_controller.get_references()
        assert len(references) == 0

        # Verify event was published
        history = event_bus.get_history()
        assert "reference_removed" in history[-1].event_type

    def test_fails_when_reference_not_found(self, ref_controller):
        """Should fail when reference doesn't exist."""
        from src.application.references.commands import RemoveReferenceCommand

        command = RemoveReferenceCommand(reference_id=999)

        result = ref_controller.remove_reference(command)

        assert isinstance(result, Failure)


class TestLinkReferenceToSegment:
    """Tests for link_reference_to_segment command."""

    def test_links_reference_to_segment(self, ref_controller, event_bus):
        """Should link reference to segment and publish event."""
        from src.application.references.commands import (
            AddReferenceCommand,
            LinkReferenceToSegmentCommand,
        )

        # Add a reference first
        add_cmd = AddReferenceCommand(
            title="Test Reference",
            authors="Author",
        )
        add_result = ref_controller.add_reference(add_cmd)
        ref = add_result.unwrap()

        # Link to segment
        link_cmd = LinkReferenceToSegmentCommand(
            reference_id=ref.id.value,
            segment_id=100,
        )
        result = ref_controller.link_reference_to_segment(link_cmd)

        assert isinstance(result, Success)

        # Verify event was published
        history = event_bus.get_history()
        assert "reference_linked_to_segment" in history[-1].event_type

    def test_fails_when_reference_not_found(self, ref_controller):
        """Should fail when reference doesn't exist."""
        from src.application.references.commands import LinkReferenceToSegmentCommand

        command = LinkReferenceToSegmentCommand(
            reference_id=999,
            segment_id=100,
        )

        result = ref_controller.link_reference_to_segment(command)

        assert isinstance(result, Failure)


class TestUnlinkReferenceFromSegment:
    """Tests for unlink_reference_from_segment command."""

    def test_unlinks_reference_from_segment(self, ref_controller, event_bus):
        """Should unlink reference from segment and publish event."""
        from src.application.references.commands import (
            AddReferenceCommand,
            LinkReferenceToSegmentCommand,
            UnlinkReferenceFromSegmentCommand,
        )

        # Add a reference and link it
        add_cmd = AddReferenceCommand(
            title="Test Reference",
            authors="Author",
        )
        add_result = ref_controller.add_reference(add_cmd)
        ref = add_result.unwrap()

        link_cmd = LinkReferenceToSegmentCommand(
            reference_id=ref.id.value,
            segment_id=100,
        )
        ref_controller.link_reference_to_segment(link_cmd)

        # Unlink
        unlink_cmd = UnlinkReferenceFromSegmentCommand(
            reference_id=ref.id.value,
            segment_id=100,
        )
        result = ref_controller.unlink_reference_from_segment(unlink_cmd)

        assert isinstance(result, Success)

        # Verify event was published
        history = event_bus.get_history()
        assert "reference_unlinked_from_segment" in history[-1].event_type


class TestQueries:
    """Tests for controller query methods."""

    def test_get_references(self, ref_controller):
        """Should get all references."""
        from src.application.references.commands import AddReferenceCommand

        # Add some references
        ref_controller.add_reference(
            AddReferenceCommand(title="Ref 1", authors="Author 1")
        )
        ref_controller.add_reference(
            AddReferenceCommand(title="Ref 2", authors="Author 2")
        )

        references = ref_controller.get_references()

        assert len(references) == 2

    def test_get_reference_by_id(self, ref_controller):
        """Should get a specific reference by ID."""
        from src.application.references.commands import AddReferenceCommand

        result = ref_controller.add_reference(
            AddReferenceCommand(title="Test", authors="Author")
        )
        ref = result.unwrap()

        retrieved = ref_controller.get_reference(ref.id.value)

        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_get_reference_returns_none_for_nonexistent(self, ref_controller):
        """Should return None for non-existent reference."""
        retrieved = ref_controller.get_reference(999)

        assert retrieved is None

    def test_search_references(self, ref_controller):
        """Should search references by title."""
        from src.application.references.commands import AddReferenceCommand

        ref_controller.add_reference(
            AddReferenceCommand(title="Machine Learning Basics", authors="Author 1")
        )
        ref_controller.add_reference(
            AddReferenceCommand(title="Deep Learning Advanced", authors="Author 2")
        )
        ref_controller.add_reference(
            AddReferenceCommand(title="Statistics 101", authors="Author 3")
        )

        results = ref_controller.search_references("Learning")

        assert len(results) == 2
