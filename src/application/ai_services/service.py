"""
AI Coding Service

Service implementing AICodingProvider protocol.
Wraps functional use cases and manages suggestion caching.

This service bridges the presentation layer (ViewModels) to
the application layer (use cases) without exposing infrastructure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import (
    ApproveCodeSuggestionCommand,
    ApproveMergeCommand,
    DetectDuplicatesCommand,
    SuggestCodesCommand,
)
from src.application.ai_services.usecases import (
    approve_code_suggestion,
    approve_merge,
    detect_duplicates,
    suggest_codes,
)

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.ai_services.core.entities import (
        CodeSuggestion,
        DuplicateCandidate,
    )
    from src.contexts.ai_services.core.protocols import (
        CodeAnalyzerProtocol,
        CodeComparatorProtocol,
    )
    from src.contexts.coding.core.entities import Code
    from src.contexts.coding.infra.repositories import (
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )


class AICodingService:
    """
    Service for AI-powered coding operations.

    Implements the AICodingProvider protocol for use by AICodingViewModel.

    Responsibilities:
    - Call functional use cases with injected dependencies
    - Cache suggestions for approval/rejection
    - Manage duplicate detection state

    Example:
        service = AICodingService(
            code_analyzer=analyzer,
            code_comparator=comparator,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        # Request suggestions
        result = service.suggest_codes(text, source_id)
        if isinstance(result, Success):
            suggestions = result.unwrap()

        # Approve a suggestion
        result = service.approve_suggestion(
            suggestion_id="sug-123",
            name="Theme",
            color="#FF0000",
        )
    """

    def __init__(
        self,
        code_analyzer: CodeAnalyzerProtocol,
        code_comparator: CodeComparatorProtocol,
        code_repo: SQLiteCodeRepository,
        segment_repo: SQLiteSegmentRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the service.

        Args:
            code_analyzer: AI service for generating code suggestions
            code_comparator: AI service for comparing codes
            code_repo: Repository for code operations
            segment_repo: Repository for segment operations
            event_bus: Event bus for publishing events
        """
        self._code_analyzer = code_analyzer
        self._code_comparator = code_comparator
        self._code_repo = code_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus

        # State: cached suggestions and duplicates
        self._suggestions: dict[str, CodeSuggestion] = {}
        self._duplicates: list[DuplicateCandidate] = []

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

        Caches suggestions for later approval/rejection.

        Args:
            text: Text to analyze
            source_id: ID of the source document
            max_suggestions: Maximum suggestions to return

        Returns:
            Success with list of suggestions, or Failure with error
        """
        # Get existing codes for context
        existing_codes = tuple(self._code_repo.get_all())

        # Create command and call use case
        command = SuggestCodesCommand(
            text=text,
            source_id=source_id,
            max_suggestions=max_suggestions,
        )

        result = suggest_codes(
            command=command,
            code_analyzer=self._code_analyzer,
            existing_codes=existing_codes,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            suggestions = result.unwrap()
            # Cache suggestions
            self._suggestions.clear()
            for suggestion in suggestions:
                self._suggestions[suggestion.id.value] = suggestion

        return result

    def get_suggestion(self, suggestion_id: str) -> CodeSuggestion | None:
        """
        Get a suggestion by ID from cache.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            The suggestion if found, None otherwise
        """
        return self._suggestions.get(suggestion_id)

    def approve_suggestion(
        self,
        suggestion_id: str,
        name: str,
        color: str,
        memo: str | None = None,
    ) -> Result[Code, str]:
        """
        Approve a suggestion and create the code.

        Removes suggestion from cache on success.

        Args:
            suggestion_id: ID of suggestion to approve
            name: Final name for the code
            color: Final color for the code
            memo: Optional memo for the new code

        Returns:
            Success with created Code, or Failure with error
        """
        suggestion = self._suggestions.get(suggestion_id)
        if suggestion is None:
            return Failure(f"Suggestion not found: {suggestion_id}")

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion_id,
            name=name,
            color=color,
            memo=memo,
        )

        result = approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=self._code_repo,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            # Remove from cache on success
            del self._suggestions[suggestion_id]

        return result

    def reject_suggestion(self, suggestion_id: str) -> None:
        """
        Reject a suggestion (removes from cache).

        Args:
            suggestion_id: ID of suggestion to reject
        """
        self._suggestions.pop(suggestion_id, None)

    def dismiss_all_suggestions(self) -> None:
        """Dismiss all current suggestions."""
        self._suggestions.clear()

    def has_suggestions(self) -> bool:
        """Check if there are any current suggestions."""
        return len(self._suggestions) > 0

    # =========================================================================
    # Duplicate Detection Operations
    # =========================================================================

    def detect_duplicates(
        self,
        threshold: float = 0.8,
    ) -> Result[list[DuplicateCandidate], str]:
        """
        Detect duplicate codes in the scheme.

        Caches duplicates for later merge approval.

        Args:
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            Success with list of duplicate candidates, or Failure with error
        """
        # Get existing codes
        existing_codes = tuple(self._code_repo.get_all())

        command = DetectDuplicatesCommand(threshold=threshold)

        result = detect_duplicates(
            command=command,
            code_comparator=self._code_comparator,
            existing_codes=existing_codes,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            self._duplicates = result.unwrap()

        return result

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
        command = ApproveMergeCommand(
            source_code_id=source_code_id,
            target_code_id=target_code_id,
        )

        result = approve_merge(
            command=command,
            code_repo=self._code_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            # Remove the merged pair from cached duplicates
            self._duplicates = [
                d
                for d in self._duplicates
                if not (
                    (
                        d.code_a_id.value == source_code_id
                        and d.code_b_id.value == target_code_id
                    )
                    or (
                        d.code_a_id.value == target_code_id
                        and d.code_b_id.value == source_code_id
                    )
                )
            ]

        return result

    def get_duplicates(self) -> list[DuplicateCandidate]:
        """Get cached duplicate candidates."""
        return list(self._duplicates)

    def dismiss_duplicate(self, code_a_id: int, code_b_id: int) -> None:
        """
        Dismiss a duplicate pair (removes from cache).

        Args:
            code_a_id: First code ID
            code_b_id: Second code ID
        """
        self._duplicates = [
            d
            for d in self._duplicates
            if not (
                (d.code_a_id.value == code_a_id and d.code_b_id.value == code_b_id)
                or (d.code_a_id.value == code_b_id and d.code_b_id.value == code_a_id)
            )
        ]

    def dismiss_all_duplicates(self) -> None:
        """Dismiss all cached duplicates."""
        self._duplicates.clear()

    def has_duplicates(self) -> bool:
        """Check if there are any cached duplicates."""
        return len(self._duplicates) > 0
