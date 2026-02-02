"""
AI Coding ViewModel

Manages state for AI-powered coding features:
- Code suggestions
- Duplicate detection

Connects the presentation layer to the AI services via AICodingProvider protocol.

Architecture:
    User Action → ViewModel → Provider (Service) → Use Cases → Domain → Events
                                                                          ↓
    UI Update ← ViewModel ← (direct return or events) ←─────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from returns.result import Success

if TYPE_CHECKING:
    from src.contexts.ai_services.core.entities import (
        CodeSuggestion,
        DuplicateCandidate,
    )
    from src.presentation.viewmodels.protocols import AICodingProvider


@dataclass
class SuggestionDTO:
    """DTO for displaying a suggestion in the UI."""

    suggestion_id: str
    name: str
    color: str
    rationale: str
    confidence: float
    context_preview: str


@dataclass
class DuplicateDTO:
    """DTO for displaying a duplicate candidate in the UI."""

    code_a_id: int
    code_a_name: str
    code_b_id: int
    code_b_name: str
    similarity: float
    reason: str


class AICodingViewModel(QObject):
    """
    ViewModel for AI coding features.

    Manages:
    - Code suggestion requests and results
    - Suggestion approval/rejection
    - Duplicate detection and merge approval
    - Loading and error states

    Uses AICodingProvider protocol for decoupled service access.

    Signals:
        suggestions_loading: Analysis started
        suggestions_received(list): Suggestions ready to display
        suggestion_approved(str, int): Suggestion approved (suggestion_id, code_id)
        suggestion_rejected(str): Suggestion rejected
        duplicates_loading: Duplicate detection started
        duplicates_received(list): Duplicates ready to display
        merge_approved(int, int): Merge approved (source_id, target_id)
        error_occurred(str, str): Error occurred (operation, message)
    """

    # Suggestion signals
    suggestions_loading = Signal()
    suggestions_received = Signal(list)  # list[SuggestionDTO]
    suggestion_approved = Signal(str, int)  # suggestion_id, created_code_id
    suggestion_rejected = Signal(str)  # suggestion_id

    # Duplicate signals
    duplicates_loading = Signal()
    duplicates_received = Signal(list)  # list[DuplicateDTO]
    merge_approved = Signal(int, int)  # source_code_id, target_code_id

    # Error signal
    error_occurred = Signal(str, str)  # operation, message

    def __init__(
        self,
        provider: AICodingProvider,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            provider: AI coding service implementing AICodingProvider protocol
            parent: Optional Qt parent
        """
        super().__init__(parent)
        self._provider = provider
        self._current_source_id: int | None = None

    # =========================================================================
    # Suggestion Operations
    # =========================================================================

    def request_suggestions(
        self,
        text: str,
        source_id: int,
        max_suggestions: int = 5,
    ) -> None:
        """
        Request AI code suggestions for text.

        Args:
            text: Text to analyze
            source_id: ID of the source document
            max_suggestions: Maximum suggestions to return
        """
        self._current_source_id = source_id
        self.suggestions_loading.emit()

        result = self._provider.suggest_codes(text, source_id, max_suggestions)

        if isinstance(result, Success):
            suggestions = result.unwrap()
            dtos = [self._suggestion_to_dto(s) for s in suggestions]
            self.suggestions_received.emit(dtos)
        else:
            error_msg = str(result.failure())
            self.error_occurred.emit("suggest_codes", error_msg)

    def approve_suggestion(
        self,
        suggestion_id: str,
        name: str | None = None,
        color: str | None = None,
        memo: str | None = None,
    ) -> None:
        """
        Approve a suggestion and create the code.

        Args:
            suggestion_id: ID of suggestion to approve
            name: Override name (uses suggestion name if None)
            color: Override color (uses suggestion color if None)
            memo: Optional memo for the new code
        """
        # Get suggestion for defaults
        suggestion = self._provider.get_suggestion(suggestion_id)
        if not suggestion:
            self.error_occurred.emit(
                "approve", f"Suggestion not found: {suggestion_id}"
            )
            return

        # Use suggestion values as defaults
        final_name = name or suggestion.name
        final_color = color or suggestion.color.to_hex()

        result = self._provider.approve_suggestion(
            suggestion_id=suggestion_id,
            name=final_name,
            color=final_color,
            memo=memo,
        )

        if isinstance(result, Success):
            code = result.unwrap()
            self.suggestion_approved.emit(suggestion_id, code.id.value)
        else:
            error_msg = str(result.failure())
            self.error_occurred.emit("approve", error_msg)

    def reject_suggestion(self, suggestion_id: str) -> None:
        """
        Reject a suggestion.

        Args:
            suggestion_id: ID of suggestion to reject
        """
        self._provider.reject_suggestion(suggestion_id)
        self.suggestion_rejected.emit(suggestion_id)

    def dismiss_all_suggestions(self) -> None:
        """Dismiss all current suggestions."""
        self._provider.dismiss_all_suggestions()

    def get_suggestion(self, suggestion_id: str) -> CodeSuggestion | None:
        """
        Get a suggestion by ID.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            The suggestion if found, None otherwise
        """
        return self._provider.get_suggestion(suggestion_id)

    def get_all_suggestions(self) -> list[SuggestionDTO]:
        """
        Get all current suggestions as DTOs.

        Returns:
            List of suggestion DTOs
        """
        # Get suggestions from provider cache
        # Note: Provider maintains the cache, we just transform to DTOs
        if not self._provider.has_suggestions():
            return []

        # We need to get the actual suggestions - this requires a method
        # For now, return empty (the UI uses the signal-based flow)
        return []

    def has_suggestions(self) -> bool:
        """Check if there are any current suggestions."""
        return self._provider.has_suggestions()

    # =========================================================================
    # Duplicate Detection Operations
    # =========================================================================

    def request_duplicate_detection(self, threshold: float = 0.8) -> None:
        """
        Request duplicate code detection.

        Args:
            threshold: Minimum similarity threshold (0.0-1.0)
        """
        self.duplicates_loading.emit()

        result = self._provider.detect_duplicates(threshold)

        if isinstance(result, Success):
            candidates = result.unwrap()
            dtos = [self._duplicate_to_dto(c) for c in candidates]
            self.duplicates_received.emit(dtos)
        else:
            error_msg = str(result.failure())
            self.error_occurred.emit("detect_duplicates", error_msg)

    def approve_merge(self, source_code_id: int, target_code_id: int) -> None:
        """
        Approve merging duplicate codes.

        Args:
            source_code_id: ID of code to delete (segments moved to target)
            target_code_id: ID of code to keep
        """
        result = self._provider.approve_merge(source_code_id, target_code_id)

        if isinstance(result, Success):
            self.merge_approved.emit(source_code_id, target_code_id)
        else:
            error_msg = str(result.failure())
            self.error_occurred.emit("approve_merge", error_msg)

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _suggestion_to_dto(self, suggestion: CodeSuggestion) -> SuggestionDTO:
        """Convert a CodeSuggestion to DTO."""
        # Get first context preview if available
        context_preview = ""
        if suggestion.contexts:
            first_context = suggestion.contexts[0]
            context_preview = first_context.text[:100] if first_context.text else ""

        return SuggestionDTO(
            suggestion_id=suggestion.id.value,
            name=suggestion.name,
            color=suggestion.color.to_hex(),
            rationale=suggestion.rationale,
            confidence=suggestion.confidence,
            context_preview=context_preview,
        )

    def _duplicate_to_dto(self, candidate: DuplicateCandidate) -> DuplicateDTO:
        """Convert a DuplicateCandidate to DTO."""
        return DuplicateDTO(
            code_a_id=candidate.code_a_id.value,
            code_a_name=candidate.code_a_name,
            code_b_id=candidate.code_b_id.value,
            code_b_name=candidate.code_b_name,
            similarity=candidate.similarity,
            reason=candidate.reason or "",
        )
