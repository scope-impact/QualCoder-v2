"""
References Controller - Application Service

Orchestrates domain operations for reference management by:
1. Loading state from repositories
2. Calling pure domain derivers
3. Persisting changes on success
4. Publishing domain events

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.application.references.commands import (
    AddReferenceCommand,
    LinkReferenceToSegmentCommand,
    RemoveReferenceCommand,
    UnlinkReferenceFromSegmentCommand,
    UpdateReferenceCommand,
)
from src.domain.references.derivers import (
    ReferenceState,
    derive_add_reference,
    derive_link_reference_to_segment,
    derive_remove_reference,
    derive_unlink_reference_from_segment,
    derive_update_reference,
)
from src.domain.references.entities import Reference
from src.domain.references.events import (
    ReferenceAdded,
    ReferenceLinkedToSegment,
    ReferenceRemoved,
    ReferenceUnlinkedFromSegment,
    ReferenceUpdated,
)
from src.domain.shared.types import ReferenceId, SegmentId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.references.repositories import SQLiteReferenceRepository


class ReferencesControllerImpl:
    """
    Implementation of the References Controller.

    Coordinates between:
    - Domain derivers (pure business logic)
    - Repository (data persistence)
    - Event bus (event publishing)
    """

    def __init__(
        self,
        event_bus: EventBus,
        ref_repo: SQLiteReferenceRepository | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            event_bus: Event bus for publishing domain events
            ref_repo: Optional repository for Reference entities
        """
        self._event_bus = event_bus
        self._ref_repo = ref_repo

        # Internal state cache
        self._references: list[Reference] = []

    # =========================================================================
    # Reference Commands
    # =========================================================================

    def add_reference(self, command: AddReferenceCommand) -> Result:
        """
        Add a new reference.

        Args:
            command: AddReferenceCommand with reference data

        Returns:
            Success(Reference) on success, Failure on error
        """
        # Step 1: Build current state
        state = ReferenceState(existing_references=tuple(self._references))

        # Step 2: Derive event using pure function
        result = derive_add_reference(
            title=command.title,
            authors=command.authors,
            year=command.year,
            doi=command.doi,
            source=command.source,
            url=command.url,
            memo=command.memo,
            state=state,
        )

        # Step 3: Handle failure
        if isinstance(result, Failure):
            return result

        # Step 4: Create entity and persist
        event: ReferenceAdded = result
        reference = Reference(
            id=event.reference_id,
            title=event.title,
            authors=event.authors,
            year=event.year,
            source=event.source,
            doi=event.doi,
            url=event.url,
            memo=event.memo,
        )

        if self._ref_repo:
            self._ref_repo.save(reference)

        # Step 5: Update internal state and publish event
        self._references.append(reference)
        self._event_bus.publish(event)

        return Success(reference)

    def update_reference(self, command: UpdateReferenceCommand) -> Result:
        """
        Update an existing reference.

        Args:
            command: UpdateReferenceCommand with updated data

        Returns:
            Success(Reference) on success, Failure on error
        """
        ref_id = ReferenceId(value=command.reference_id)

        # Step 1: Build current state
        state = ReferenceState(existing_references=tuple(self._references))

        # Step 2: Derive event using pure function
        result = derive_update_reference(
            reference_id=ref_id,
            title=command.title,
            authors=command.authors,
            year=command.year,
            doi=command.doi,
            source=command.source,
            url=command.url,
            memo=command.memo,
            state=state,
        )

        # Step 3: Handle failure
        if isinstance(result, Failure):
            return result

        # Step 4: Create entity and persist
        event: ReferenceUpdated = result
        updated_ref = Reference(
            id=ref_id,
            title=event.title,
            authors=event.authors,
            year=event.year,
            source=event.source,
            doi=event.doi,
            url=event.url,
            memo=event.memo,
        )

        if self._ref_repo:
            self._ref_repo.save(updated_ref)

        # Step 5: Update internal state and publish event
        self._references = [
            r if r.id != ref_id else updated_ref for r in self._references
        ]
        self._event_bus.publish(event)

        return Success(updated_ref)

    def remove_reference(self, command: RemoveReferenceCommand) -> Result:
        """
        Remove a reference.

        Args:
            command: RemoveReferenceCommand with reference ID

        Returns:
            Success(ReferenceRemoved) on success, Failure on error
        """
        ref_id = ReferenceId(value=command.reference_id)

        # Step 1: Build current state
        state = ReferenceState(existing_references=tuple(self._references))

        # Step 2: Derive event using pure function
        result = derive_remove_reference(
            reference_id=ref_id,
            state=state,
        )

        # Step 3: Handle failure
        if isinstance(result, Failure):
            return result

        event: ReferenceRemoved = result

        # Step 4: Delete from repository
        if self._ref_repo:
            self._ref_repo.delete(ref_id)

        # Step 5: Update internal state and publish event
        self._references = [r for r in self._references if r.id != ref_id]
        self._event_bus.publish(event)

        return Success(event)

    def link_reference_to_segment(
        self, command: LinkReferenceToSegmentCommand
    ) -> Result:
        """
        Link a reference to a coded segment.

        Args:
            command: LinkReferenceToSegmentCommand with IDs

        Returns:
            Success(ReferenceLinkedToSegment) on success, Failure on error
        """
        ref_id = ReferenceId(value=command.reference_id)
        segment_id = SegmentId(value=command.segment_id)

        # Step 1: Refresh state from repository if available
        if self._ref_repo:
            self._references = self._ref_repo.get_all()

        state = ReferenceState(existing_references=tuple(self._references))

        # Step 2: Derive event using pure function
        result = derive_link_reference_to_segment(
            reference_id=ref_id,
            segment_id=segment_id,
            state=state,
        )

        # Step 3: Handle failure
        if isinstance(result, Failure):
            return result

        event: ReferenceLinkedToSegment = result

        # Step 4: Persist link
        if self._ref_repo:
            self._ref_repo.link_segment(ref_id, segment_id)
            # Refresh to get updated segment_ids
            self._references = self._ref_repo.get_all()

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(event)

    def unlink_reference_from_segment(
        self, command: UnlinkReferenceFromSegmentCommand
    ) -> Result:
        """
        Unlink a reference from a coded segment.

        Args:
            command: UnlinkReferenceFromSegmentCommand with IDs

        Returns:
            Success(ReferenceUnlinkedFromSegment) on success, Failure on error
        """
        ref_id = ReferenceId(value=command.reference_id)
        segment_id = SegmentId(value=command.segment_id)

        # Step 1: Refresh state from repository if available
        if self._ref_repo:
            self._references = self._ref_repo.get_all()

        state = ReferenceState(existing_references=tuple(self._references))

        # Step 2: Derive event using pure function
        result = derive_unlink_reference_from_segment(
            reference_id=ref_id,
            segment_id=segment_id,
            state=state,
        )

        # Step 3: Handle failure
        if isinstance(result, Failure):
            return result

        event: ReferenceUnlinkedFromSegment = result

        # Step 4: Remove link
        if self._ref_repo:
            self._ref_repo.unlink_segment(ref_id, segment_id)
            # Refresh to get updated segment_ids
            self._references = self._ref_repo.get_all()

        # Step 5: Publish event
        self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Queries
    # =========================================================================

    def get_references(self) -> list[Reference]:
        """Get all references."""
        return list(self._references)

    def get_reference(self, reference_id: int) -> Reference | None:
        """Get a specific reference by ID."""
        ref_id = ReferenceId(value=reference_id)
        return next((r for r in self._references if r.id == ref_id), None)

    def search_references(self, query: str) -> list[Reference]:
        """Search references by title."""
        if self._ref_repo:
            return self._ref_repo.search_by_title(query)
        # Fallback to in-memory search
        query_lower = query.lower()
        return [r for r in self._references if query_lower in r.title.lower()]

    def get_references_for_segment(self, segment_id: int) -> list[Reference]:
        """Get all references linked to a segment."""
        return [r for r in self._references if segment_id in r.segment_ids]

    def load_references(self) -> None:
        """Load references from repository into internal cache."""
        if self._ref_repo:
            self._references = self._ref_repo.get_all()

    # =========================================================================
    # Agent API (for AI context queries)
    # =========================================================================

    def get_references_context(self) -> dict[str, Any]:
        """
        Get the references context for AI agent.

        Returns dict with:
        - reference_count
        - references list with basic info
        """
        return {
            "reference_count": len(self._references),
            "references": [
                {
                    "id": r.id.value,
                    "title": r.title,
                    "authors": r.authors,
                    "year": r.year,
                    "doi": r.doi,
                    "segment_count": len(r.segment_ids),
                }
                for r in self._references
            ],
        }
