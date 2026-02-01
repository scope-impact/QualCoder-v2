"""
References ViewModel

Connects the ReferencesScreen to the references repository.
Handles data transformation between domain entities and UI DTOs.

Implements QC-041.02 presentation layer:
- AC #1: I can see list of all references
- AC #2: I can edit reference metadata
- AC #3: I can delete references

Architecture:
    User Action → ViewModel → Repository → Domain
                                              ↓
    UI Update ← ViewModel ← EventBus ←───────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.references.entities import Reference
from src.domain.shared.types import ReferenceId
from src.presentation.dto import ReferenceDTO

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.references.repositories import SQLiteReferenceRepository


class ReferencesViewModel:
    """
    ViewModel for the References screen.

    Responsibilities:
    - Transform domain Reference entities to UI DTOs
    - Handle user actions by calling repository methods
    - React to domain events via EventBus
    - Provide filtering and search capabilities
    - Track selection state

    This is a pure Python class (no Qt dependency) so it can be
    tested without a Qt event loop.
    """

    def __init__(
        self,
        ref_repo: SQLiteReferenceRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            ref_repo: The reference repository for data access
            event_bus: The event bus for reactive updates
        """
        self._ref_repo = ref_repo
        self._event_bus = event_bus

        # Selection state
        self._selected_reference_id: int | None = None

        # Connect to events
        self._connect_events()

    def _connect_events(self) -> None:
        """Connect to relevant domain events."""
        pass

    # =========================================================================
    # Load Data (AC #1)
    # =========================================================================

    def load_references(self) -> list[ReferenceDTO]:
        """
        Load all references and return as DTOs.

        Returns:
            List of ReferenceDTO objects for UI display
        """
        refs = self._ref_repo.get_all()
        return [self._reference_to_dto(r) for r in refs]

    def get_reference(self, reference_id: int) -> ReferenceDTO | None:
        """
        Get a reference by ID and return as DTO.

        Args:
            reference_id: ID of reference to retrieve

        Returns:
            ReferenceDTO if found, None otherwise
        """
        ref = self._ref_repo.get_by_id(ReferenceId(value=reference_id))
        return self._reference_to_dto(ref) if ref else None

    # =========================================================================
    # Add Reference
    # =========================================================================

    def add_reference(
        self,
        title: str,
        authors: str,
        year: int | None = None,
        source: str | None = None,
        doi: str | None = None,
        url: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Add a new reference.

        Args:
            title: Reference title
            authors: Reference authors
            year: Publication year
            source: Journal/publisher
            doi: Digital Object Identifier
            url: URL
            memo: Notes

        Returns:
            True if successful, False otherwise
        """
        if not title or not authors:
            return False

        # Generate new ID
        all_refs = self._ref_repo.get_all()
        new_id = max((r.id.value for r in all_refs), default=0) + 1

        ref = Reference(
            id=ReferenceId(value=new_id),
            title=title,
            authors=authors,
            year=year,
            source=source,
            doi=doi,
            url=url,
            memo=memo,
        )

        self._ref_repo.save(ref)
        return True

    # =========================================================================
    # Update Reference (AC #2)
    # =========================================================================

    def update_reference(
        self,
        reference_id: int,
        title: str,
        authors: str,
        year: int | None = None,
        source: str | None = None,
        doi: str | None = None,
        url: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Update a reference.

        Args:
            reference_id: ID of reference to update
            title: New title
            authors: New authors
            year: New year
            source: New source
            doi: New DOI
            url: New URL
            memo: New memo

        Returns:
            True if successful, False otherwise
        """
        ref = self._ref_repo.get_by_id(ReferenceId(value=reference_id))
        if ref is None:
            return False

        # Build updated reference (immutable entity pattern)
        updated = Reference(
            id=ref.id,
            title=title,
            authors=authors,
            year=year,
            source=source,
            doi=doi,
            url=url,
            memo=memo,
            segment_ids=ref.segment_ids,
            created_at=ref.created_at,
        )

        self._ref_repo.save(updated)
        return True

    # =========================================================================
    # Delete Reference (AC #3)
    # =========================================================================

    def delete_reference(self, reference_id: int) -> bool:
        """
        Delete a reference.

        Args:
            reference_id: ID of reference to delete

        Returns:
            True if successful, False otherwise
        """
        ref = self._ref_repo.get_by_id(ReferenceId(value=reference_id))
        if ref is None:
            return False

        self._ref_repo.delete(ReferenceId(value=reference_id))

        # Clear selection if deleted reference was selected
        if self._selected_reference_id == reference_id:
            self._selected_reference_id = None

        return True

    # =========================================================================
    # Selection
    # =========================================================================

    def select_reference(self, reference_id: int) -> None:
        """
        Set the selected reference.

        Args:
            reference_id: ID of reference to select
        """
        self._selected_reference_id = reference_id

    def get_selected_reference_id(self) -> int | None:
        """Get the ID of the selected reference."""
        return self._selected_reference_id

    def clear_selection(self) -> None:
        """Clear reference selection."""
        self._selected_reference_id = None

    # =========================================================================
    # Search
    # =========================================================================

    def search_references(self, query: str) -> list[ReferenceDTO]:
        """
        Search references by title or author.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching ReferenceDTO objects
        """
        refs = self._ref_repo.get_all()
        query_lower = query.lower()

        matching = [
            r
            for r in refs
            if query_lower in r.title.lower() or query_lower in r.authors.lower()
        ]

        return [self._reference_to_dto(r) for r in matching]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _reference_to_dto(self, ref: Reference) -> ReferenceDTO:
        """Convert a Reference entity to DTO."""
        return ReferenceDTO(
            id=str(ref.id.value),
            title=ref.title,
            authors=ref.authors,
            year=ref.year,
            source=ref.source,
            doi=ref.doi,
            url=ref.url,
            memo=ref.memo,
            segment_count=len(ref.segment_ids),
            segment_ids=list(ref.segment_ids),
        )
