"""
Case Manager ViewModel

Connects the CaseManagerScreen to the case repository.
Handles data transformation between domain entities and UI DTOs.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Architecture:
    User Action → ViewModel → Repository → Domain
                                              ↓
    UI Update ← ViewModel ← EventBus ←───────┘
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.domain.cases.entities import AttributeType, Case, CaseAttribute
from src.domain.shared.types import CaseId, SourceId
from src.presentation.dto import CaseAttributeDTO, CaseDTO, CaseSummaryDTO

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.projects.repositories import SQLiteCaseRepository


class CaseManagerViewModel:
    """
    ViewModel for the Case Manager screen.

    Responsibilities:
    - Transform domain Case entities to UI DTOs
    - Handle user actions by calling repository methods
    - React to domain events via EventBus
    - Provide filtering and search capabilities
    - Track selection state

    This is a pure Python class (no Qt dependency) so it can be
    tested without a Qt event loop.
    """

    def __init__(
        self,
        case_repo: SQLiteCaseRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            case_repo: The case repository for data access
            event_bus: The event bus for reactive updates
        """
        self._case_repo = case_repo
        self._event_bus = event_bus

        # Selection state
        self._selected_case_id: int | None = None

        # Connect to events
        self._connect_events()

    def _connect_events(self) -> None:
        """Connect to relevant domain events."""
        # Events will trigger UI updates via callbacks
        # For now, this is a placeholder - actual connections
        # would be made when using Qt signals
        pass

    # =========================================================================
    # Load Data (AC #4)
    # =========================================================================

    def load_cases(self) -> list[CaseDTO]:
        """
        Load all cases and return as DTOs.

        Returns:
            List of CaseDTO objects for UI display
        """
        cases = self._case_repo.get_all()
        return [self._case_to_dto(c) for c in cases]

    def get_case(self, case_id: int) -> CaseDTO | None:
        """
        Get a case by ID and return as DTO.

        Args:
            case_id: ID of case to retrieve

        Returns:
            CaseDTO if found, None otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        return self._case_to_dto(case) if case else None

    def get_summary(self) -> CaseSummaryDTO:
        """
        Get case summary statistics.

        Returns:
            CaseSummaryDTO with counts
        """
        cases = self._case_repo.get_all()

        # Collect unique attribute names
        unique_attrs: set[str] = set()
        cases_with_sources = 0

        for case in cases:
            for attr in case.attributes:
                unique_attrs.add(attr.name)
            if case.source_ids:
                cases_with_sources += 1

        return CaseSummaryDTO(
            total_cases=len(cases),
            cases_with_sources=cases_with_sources,
            total_attributes=sum(len(c.attributes) for c in cases),
            unique_attribute_names=sorted(unique_attrs),
        )

    # =========================================================================
    # Create Case (AC #1)
    # =========================================================================

    def create_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Create a new case.

        Args:
            name: Name of the case
            description: Optional description
            memo: Optional memo

        Returns:
            True if successful, False otherwise
        """
        # Check for duplicate name
        existing = self._case_repo.get_by_name(name)
        if existing is not None:
            return False

        # Generate new ID (count + 1 as simple strategy)
        new_id = self._case_repo.count() + 1

        case = Case(
            id=CaseId(value=new_id),
            name=name,
            description=description,
            memo=memo,
            attributes=(),
            source_ids=(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        self._case_repo.save(case)
        return True

    # =========================================================================
    # Update Case
    # =========================================================================

    def update_case(
        self,
        case_id: int,
        name: str | None = None,
        description: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Update a case.

        Args:
            case_id: ID of case to update
            name: New name (if provided)
            description: New description (if provided)
            memo: New memo (if provided)

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        # Build updated case
        updated = Case(
            id=case.id,
            name=name if name is not None else case.name,
            description=description if description is not None else case.description,
            memo=memo if memo is not None else case.memo,
            attributes=case.attributes,
            source_ids=case.source_ids,
            created_at=case.created_at,
            updated_at=datetime.now(UTC),
        )

        self._case_repo.save(updated)
        return True

    # =========================================================================
    # Delete Case
    # =========================================================================

    def delete_case(self, case_id: int) -> bool:
        """
        Delete a case.

        Args:
            case_id: ID of case to delete

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        self._case_repo.delete(CaseId(value=case_id))

        # Clear selection if deleted case was selected
        if self._selected_case_id == case_id:
            self._selected_case_id = None

        return True

    # =========================================================================
    # Link Source (AC #2)
    # =========================================================================

    def link_source(self, case_id: int, source_id: int) -> bool:
        """
        Link a source to a case.

        Args:
            case_id: ID of case
            source_id: ID of source to link

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        self._case_repo.link_source(CaseId(value=case_id), SourceId(value=source_id))
        return True

    def unlink_source(self, case_id: int, source_id: int) -> bool:
        """
        Unlink a source from a case.

        Args:
            case_id: ID of case
            source_id: ID of source to unlink

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        self._case_repo.unlink_source(CaseId(value=case_id), SourceId(value=source_id))
        return True

    # =========================================================================
    # Add Attribute (AC #3)
    # =========================================================================

    def add_attribute(
        self,
        case_id: int,
        name: str,
        attr_type: str,
        value: str | int | float | bool | None = None,
    ) -> bool:
        """
        Add or update an attribute on a case.

        Args:
            case_id: ID of case
            name: Attribute name
            attr_type: Attribute type (text, number, boolean, date)
            value: Attribute value

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        # Map string type to enum
        type_map = {
            "text": AttributeType.TEXT,
            "number": AttributeType.NUMBER,
            "boolean": AttributeType.BOOLEAN,
            "date": AttributeType.DATE,
        }
        attr_type_enum = type_map.get(attr_type, AttributeType.TEXT)

        attribute = CaseAttribute(
            name=name,
            attr_type=attr_type_enum,
            value=value,
        )

        self._case_repo.save_attribute(CaseId(value=case_id), attribute)
        return True

    def remove_attribute(self, case_id: int, name: str) -> bool:
        """
        Remove an attribute from a case.

        Args:
            case_id: ID of case
            name: Attribute name to remove

        Returns:
            True if successful, False otherwise
        """
        case = self._case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return False

        self._case_repo.delete_attribute(CaseId(value=case_id), name)
        return True

    # =========================================================================
    # Selection
    # =========================================================================

    def select_case(self, case_id: int) -> None:
        """
        Set the selected case.

        Args:
            case_id: ID of case to select
        """
        self._selected_case_id = case_id

    def get_selected_case_id(self) -> int | None:
        """Get the ID of the selected case."""
        return self._selected_case_id

    def clear_selection(self) -> None:
        """Clear case selection."""
        self._selected_case_id = None

    # =========================================================================
    # Search
    # =========================================================================

    def search_cases(self, query: str) -> list[CaseDTO]:
        """
        Search cases by name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching CaseDTO objects
        """
        cases = self._case_repo.get_all()
        query_lower = query.lower()

        matching = [c for c in cases if query_lower in c.name.lower()]

        return [self._case_to_dto(c) for c in matching]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _case_to_dto(self, case: Case) -> CaseDTO:
        """Convert a Case entity to DTO."""
        return CaseDTO(
            id=str(case.id.value),
            name=case.name,
            description=case.description,
            memo=case.memo,
            attributes=[
                CaseAttributeDTO(
                    name=attr.name,
                    attr_type=attr.attr_type.value,
                    value=attr.value,
                )
                for attr in case.attributes
            ],
            source_ids=[str(sid) for sid in case.source_ids],
            source_count=len(case.source_ids),
            created_at=case.created_at.isoformat() if case.created_at else None,
            updated_at=case.updated_at.isoformat() if case.updated_at else None,
        )
