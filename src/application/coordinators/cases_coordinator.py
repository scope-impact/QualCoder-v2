"""
Cases Coordinator - Case Management.

Handles all case-related CRUD and linking operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case


class CasesCoordinator(BaseCoordinator):
    """
    Coordinator for case operations.

    Manages:
    - Creating cases
    - Updating cases
    - Removing cases
    - Linking/unlinking sources to cases
    - Setting case attributes
    - Case queries

    Requires an open project for all operations.
    """

    # =========================================================================
    # Case Commands
    # =========================================================================

    def create_case(self, command) -> Result:
        """Create a new case in the current project."""
        from src.application.cases.usecases import create_case

        return create_case(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    def update_case(self, command) -> Result:
        """Update an existing case."""
        from src.application.cases.usecases import update_case

        return update_case(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    def remove_case(self, command) -> Result:
        """Remove a case from the current project."""
        from src.application.cases.usecases import remove_case

        return remove_case(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    def link_source_to_case(self, command) -> Result:
        """Link a source to a case."""
        from src.application.cases.usecases import link_source_to_case

        return link_source_to_case(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    def unlink_source_from_case(self, command) -> Result:
        """Unlink a source from a case."""
        from src.application.cases.usecases import unlink_source_from_case

        return unlink_source_from_case(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    def set_case_attribute(self, command) -> Result:
        """Set an attribute on a case."""
        from src.application.cases.usecases import set_case_attribute

        return set_case_attribute(
            command=command,
            state=self.state,
            cases_ctx=self.cases_context,
            event_bus=self.event_bus,
        )

    # =========================================================================
    # Case Queries
    # =========================================================================

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        return list(self.state.cases)

    def get_case(self, case_id: int) -> Any | None:
        """Get a specific case by ID."""
        return self.state.get_case(case_id)
