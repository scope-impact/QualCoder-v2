"""
Case Manager Service

Service implementing CaseManagerProvider protocol.
Wraps functional use cases for case management operations.

This service bridges the presentation layer (ViewModels) to
the application layer (use cases) without exposing infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.cases.usecases import (
    create_case,
    link_source_to_case,
    remove_case,
    set_case_attribute,
    unlink_source_from_case,
    update_case,
)
from src.application.projects.commands import (
    CreateCaseCommand,
    LinkSourceToCaseCommand,
    RemoveCaseCommand,
    SetCaseAttributeCommand,
    UnlinkSourceFromCaseCommand,
    UpdateCaseCommand,
)
from src.contexts.shared.core.types import CaseId
from src.presentation.dto import CaseSummaryDTO

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus
    from src.application.state import ProjectState
    from src.contexts.cases.core.entities import Case


class CaseManagerService:
    """
    Service for case management operations.

    Implements the CaseManagerProvider protocol for use by CaseManagerViewModel.

    Responsibilities:
    - Call functional use cases with injected dependencies
    - Transform use case results to protocol return types
    - Handle case search and filtering

    Example:
        service = CaseManagerService(
            state=project_state,
            cases_ctx=cases_context,
            event_bus=event_bus,
        )

        # Create a case
        result = service.create_case("Interview 1", "First participant")
        if isinstance(result, Success):
            case = result.unwrap()

        # Link a source
        result = service.link_source(case_id=1, source_id=5)
    """

    def __init__(
        self,
        state: ProjectState,
        cases_ctx: CasesContext,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the service.

        Args:
            state: Project state cache
            cases_ctx: Cases bounded context
            event_bus: Event bus for publishing events
        """
        self._state = state
        self._cases_ctx = cases_ctx
        self._event_bus = event_bus

    # =========================================================================
    # Load Operations
    # =========================================================================

    def get_all_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        if self._cases_ctx and self._cases_ctx.case_repo:
            return self._cases_ctx.case_repo.get_all()
        return list(self._state.cases)

    def get_case(self, case_id: int) -> Case | None:
        """
        Get a case by ID.

        Args:
            case_id: ID of case to retrieve

        Returns:
            Case if found, None otherwise
        """
        if self._cases_ctx and self._cases_ctx.case_repo:
            return self._cases_ctx.case_repo.get_by_id(CaseId(value=case_id))
        return None

    def get_summary(self) -> CaseSummaryDTO:
        """
        Get case summary statistics.

        Returns:
            CaseSummaryDTO with counts
        """
        cases = self.get_all_cases()

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
    # CRUD Operations
    # =========================================================================

    def create_case(
        self,
        name: str,
        description: str | None = None,
        memo: str | None = None,
    ) -> Result[Case, str]:
        """
        Create a new case.

        Args:
            name: Name of the case
            description: Optional description
            memo: Optional memo

        Returns:
            Success with created Case, or Failure with error
        """
        command = CreateCaseCommand(
            name=name,
            description=description,
            memo=memo,
        )

        return create_case(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

    def update_case(
        self,
        case_id: int,
        name: str | None = None,
        description: str | None = None,
        memo: str | None = None,
    ) -> Result[Case, str]:
        """
        Update a case.

        Args:
            case_id: ID of case to update
            name: New name (if provided)
            description: New description (if provided)
            memo: New memo (if provided)

        Returns:
            Success with updated Case, or Failure with error
        """
        command = UpdateCaseCommand(
            case_id=case_id,
            name=name,
            description=description,
            memo=memo,
        )

        return update_case(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

    def delete_case(self, case_id: int) -> Result[None, str]:
        """
        Delete a case.

        Args:
            case_id: ID of case to delete

        Returns:
            Success with None, or Failure with error
        """
        command = RemoveCaseCommand(case_id=case_id)

        result = remove_case(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            return Success(None)
        return result

    # =========================================================================
    # Source Link Operations
    # =========================================================================

    def link_source(self, case_id: int, source_id: int) -> Result[None, str]:
        """
        Link a source to a case.

        Args:
            case_id: ID of case
            source_id: ID of source to link

        Returns:
            Success with None, or Failure with error
        """
        command = LinkSourceToCaseCommand(
            case_id=case_id,
            source_id=source_id,
        )

        result = link_source_to_case(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            return Success(None)
        return result

    def unlink_source(self, case_id: int, source_id: int) -> Result[None, str]:
        """
        Unlink a source from a case.

        Args:
            case_id: ID of case
            source_id: ID of source to unlink

        Returns:
            Success with None, or Failure with error
        """
        command = UnlinkSourceFromCaseCommand(
            case_id=case_id,
            source_id=source_id,
        )

        result = unlink_source_from_case(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            return Success(None)
        return result

    # =========================================================================
    # Attribute Operations
    # =========================================================================

    def add_attribute(
        self,
        case_id: int,
        name: str,
        attr_type: str,
        value: str | int | float | bool | None = None,
    ) -> Result[None, str]:
        """
        Add or update an attribute on a case.

        Args:
            case_id: ID of case
            name: Attribute name
            attr_type: Attribute type (text, number, boolean, date)
            value: Attribute value

        Returns:
            Success with None, or Failure with error
        """
        command = SetCaseAttributeCommand(
            case_id=case_id,
            attr_name=name,
            attr_type=attr_type,
            attr_value=value,
        )

        result = set_case_attribute(
            command=command,
            state=self._state,
            cases_ctx=self._cases_ctx,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            return Success(None)
        return result

    def remove_attribute(self, case_id: int, name: str) -> Result[None, str]:
        """
        Remove an attribute from a case.

        Args:
            case_id: ID of case
            name: Attribute name to remove

        Returns:
            Success with None, or Failure with error
        """
        if not self._cases_ctx or not self._cases_ctx.case_repo:
            return Failure("No case repository available")

        case = self._cases_ctx.case_repo.get_by_id(CaseId(value=case_id))
        if case is None:
            return Failure(f"Case {case_id} not found")

        deleted = self._cases_ctx.case_repo.delete_attribute(
            CaseId(value=case_id), name
        )

        if not deleted:
            return Failure(f"Attribute '{name}' not found on case {case_id}")

        # Refresh state
        self._state.cases = self._cases_ctx.case_repo.get_all()

        return Success(None)

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search_cases(self, query: str) -> list[Case]:
        """
        Search cases by name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching cases
        """
        cases = self.get_all_cases()
        query_lower = query.lower()

        return [c for c in cases if query_lower in c.name.lower()]
