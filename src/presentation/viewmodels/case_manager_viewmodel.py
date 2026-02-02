"""
Case Manager ViewModel

Connects the CaseManagerScreen to the case management service.
Handles data transformation between domain entities and UI DTOs.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Architecture:
    User Action → ViewModel → Provider (Service) → Use Cases → Domain → Events
                                                                          ↓
    UI Update ← ViewModel ← (refresh data) ←──────────────────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Success

from src.presentation.dto import CaseAttributeDTO, CaseDTO, CaseSummaryDTO

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case
    from src.presentation.viewmodels.protocols import CaseManagerProvider


class CaseManagerViewModel:
    """
    ViewModel for the Case Manager screen.

    Responsibilities:
    - Transform domain Case entities to UI DTOs
    - Handle user actions by calling provider methods
    - Provide filtering and search capabilities
    - Track selection state

    Uses CaseManagerProvider protocol for decoupled service access.

    This is a pure Python class (no Qt dependency) so it can be
    tested without a Qt event loop.
    """

    def __init__(
        self,
        provider: CaseManagerProvider,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            provider: Case management service implementing CaseManagerProvider protocol
        """
        self._provider = provider

        # Selection state
        self._selected_case_id: int | None = None

    # =========================================================================
    # Load Data (AC #4)
    # =========================================================================

    def load_cases(self) -> list[CaseDTO]:
        """
        Load all cases and return as DTOs.

        Returns:
            List of CaseDTO objects for UI display
        """
        cases = self._provider.get_all_cases()
        return [self._case_to_dto(c) for c in cases]

    def get_case(self, case_id: int) -> CaseDTO | None:
        """
        Get a case by ID and return as DTO.

        Args:
            case_id: ID of case to retrieve

        Returns:
            CaseDTO if found, None otherwise
        """
        case = self._provider.get_case(case_id)
        return self._case_to_dto(case) if case else None

    def get_summary(self) -> CaseSummaryDTO:
        """
        Get case summary statistics.

        Returns:
            CaseSummaryDTO with counts
        """
        return self._provider.get_summary()

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
        result = self._provider.create_case(
            name=name,
            description=description,
            memo=memo,
        )
        return isinstance(result, Success)

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
        result = self._provider.update_case(
            case_id=case_id,
            name=name,
            description=description,
            memo=memo,
        )
        return isinstance(result, Success)

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
        result = self._provider.delete_case(case_id)

        if isinstance(result, Success):
            # Clear selection if deleted case was selected
            if self._selected_case_id == case_id:
                self._selected_case_id = None
            return True

        return False

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
        result = self._provider.link_source(case_id, source_id)
        return isinstance(result, Success)

    def unlink_source(self, case_id: int, source_id: int) -> bool:
        """
        Unlink a source from a case.

        Args:
            case_id: ID of case
            source_id: ID of source to unlink

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.unlink_source(case_id, source_id)
        return isinstance(result, Success)

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
        result = self._provider.add_attribute(
            case_id=case_id,
            name=name,
            attr_type=attr_type,
            value=value,
        )
        return isinstance(result, Success)

    def remove_attribute(self, case_id: int, name: str) -> bool:
        """
        Remove an attribute from a case.

        Args:
            case_id: ID of case
            name: Attribute name to remove

        Returns:
            True if successful, False otherwise
        """
        result = self._provider.remove_attribute(case_id, name)
        return isinstance(result, Success)

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
        cases = self._provider.search_cases(query)
        return [self._case_to_dto(c) for c in cases]

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
