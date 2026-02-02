"""
ViewModel Protocols

Defines the interfaces that ViewModels expect from their controllers/services.
This allows ViewModels to be decoupled from specific implementations.

Naming convention:
- Protocol: Defines WHAT is needed (interface)
- Service: Provides HOW (implementation)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from returns.result import Result

if TYPE_CHECKING:
    from src.application.projects.commands import (
        AddSourceCommand,
        CreateFolderCommand,
        DeleteFolderCommand,
        MoveSourceToFolderCommand,
        OpenSourceCommand,
        RemoveSourceCommand,
        RenameFolderCommand,
        UpdateSourceCommand,
    )
    from src.contexts.ai_services.core.entities import (
        CodeSuggestion,
        DuplicateCandidate,
    )
    from src.contexts.cases.core.entities import Case
    from src.contexts.coding.core.entities import Code
    from src.contexts.projects.core.entities import Folder, ProjectSummary, Source
    from src.presentation.dto import CaseSummaryDTO


class FileManagerController(Protocol):
    """
    Protocol for FileManagerViewModel's controller.

    Defines the exact interface that FileManagerViewModel needs.
    This can be implemented by FileManagerService, mock objects for testing,
    or any other class that provides these methods.

    Naming convention:
    - Protocol (this): FileManagerController - defines WHAT is needed (interface)
    - Service: FileManagerService - provides HOW (implementation)
    """

    # =========================================================================
    # Source Operations
    # =========================================================================

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        ...

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        ...

    def add_source(self, command: AddSourceCommand) -> Result:
        """Add a source file to the current project."""
        ...

    def remove_source(self, command: RemoveSourceCommand) -> Result:
        """Remove a source from the current project."""
        ...

    def open_source(self, command: OpenSourceCommand) -> Result:
        """Open a source for viewing/coding."""
        ...

    def update_source(self, command: UpdateSourceCommand) -> Result:
        """Update source metadata."""
        ...

    def get_segment_count_for_source(self, source_id: int) -> int:
        """Get the count of coded segments for a source."""
        ...

    # =========================================================================
    # Folder Operations
    # =========================================================================

    def get_folders(self) -> list[Folder]:
        """Get all folders in the current project."""
        ...

    def create_folder(self, command: CreateFolderCommand) -> Result:
        """Create a new folder."""
        ...

    def rename_folder(self, command: RenameFolderCommand) -> Result:
        """Rename a folder."""
        ...

    def delete_folder(self, command: DeleteFolderCommand) -> Result:
        """Delete an empty folder."""
        ...

    def move_source_to_folder(self, command: MoveSourceToFolderCommand) -> Result:
        """Move a source to a folder."""
        ...

    # =========================================================================
    # Case Operations
    # =========================================================================

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        ...

    # =========================================================================
    # Project Operations
    # =========================================================================

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        ...


# =============================================================================
# AI Coding Provider Protocol
# =============================================================================


class AICodingProvider(Protocol):
    """
    Protocol for AI-powered coding operations.

    Used by AICodingViewModel to interact with AI services
    without direct dependency on infrastructure.

    Implementations:
    - AICodingService: Production implementation
    - Mock objects: For testing
    """

    # =========================================================================
    # Suggestion Operations
    # =========================================================================

    def suggest_codes(
        self,
        text: str,
        source_id: int,
        max_suggestions: int = 5,
    ) -> Result[list[CodeSuggestion], str]:
        """
        Request AI code suggestions for text.

        Args:
            text: Text to analyze
            source_id: ID of the source document
            max_suggestions: Maximum suggestions to return

        Returns:
            Success with list of suggestions, or Failure with error
        """
        ...

    def get_suggestion(self, suggestion_id: str) -> CodeSuggestion | None:
        """
        Get a suggestion by ID from cache.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            The suggestion if found, None otherwise
        """
        ...

    def approve_suggestion(
        self,
        suggestion_id: str,
        name: str,
        color: str,
        memo: str | None = None,
    ) -> Result[Code, str]:
        """
        Approve a suggestion and create the code.

        Args:
            suggestion_id: ID of suggestion to approve
            name: Final name for the code
            color: Final color for the code
            memo: Optional memo for the new code

        Returns:
            Success with created Code, or Failure with error
        """
        ...

    def reject_suggestion(self, suggestion_id: str) -> None:
        """
        Reject a suggestion (removes from cache).

        Args:
            suggestion_id: ID of suggestion to reject
        """
        ...

    def dismiss_all_suggestions(self) -> None:
        """Dismiss all current suggestions."""
        ...

    def has_suggestions(self) -> bool:
        """Check if there are any current suggestions."""
        ...

    # =========================================================================
    # Duplicate Detection Operations
    # =========================================================================

    def detect_duplicates(
        self,
        threshold: float = 0.8,
    ) -> Result[list[DuplicateCandidate], str]:
        """
        Detect duplicate codes in the scheme.

        Args:
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            Success with list of duplicate candidates, or Failure with error
        """
        ...

    def approve_merge(
        self,
        source_code_id: int,
        target_code_id: int,
    ) -> Result[Code, str]:
        """
        Approve merging duplicate codes.

        Args:
            source_code_id: ID of code to delete (segments moved to target)
            target_code_id: ID of code to keep

        Returns:
            Success with merged Code, or Failure with error
        """
        ...


# =============================================================================
# Case Manager Provider Protocol
# =============================================================================


class CaseManagerProvider(Protocol):
    """
    Protocol for case management operations.

    Used by CaseManagerViewModel to interact with case repository
    without direct dependency on infrastructure.

    Implementations:
    - CaseManagerService: Production implementation
    - Mock objects: For testing
    """

    # =========================================================================
    # Load Operations
    # =========================================================================

    def get_all_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        ...

    def get_case(self, case_id: int) -> Case | None:
        """
        Get a case by ID.

        Args:
            case_id: ID of case to retrieve

        Returns:
            Case if found, None otherwise
        """
        ...

    def get_summary(self) -> CaseSummaryDTO:
        """
        Get case summary statistics.

        Returns:
            CaseSummaryDTO with counts
        """
        ...

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
        ...

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
        ...

    def delete_case(self, case_id: int) -> Result[None, str]:
        """
        Delete a case.

        Args:
            case_id: ID of case to delete

        Returns:
            Success with None, or Failure with error
        """
        ...

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
        ...

    def unlink_source(self, case_id: int, source_id: int) -> Result[None, str]:
        """
        Unlink a source from a case.

        Args:
            case_id: ID of case
            source_id: ID of source to unlink

        Returns:
            Success with None, or Failure with error
        """
        ...

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
        ...

    def remove_attribute(self, case_id: int, name: str) -> Result[None, str]:
        """
        Remove an attribute from a case.

        Args:
            case_id: ID of case
            name: Attribute name to remove

        Returns:
            Success with None, or Failure with error
        """
        ...

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
        ...
