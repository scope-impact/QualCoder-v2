"""
AI Coding ViewModel

Manages state for AI-powered coding features:
- Code suggestions
- Duplicate detection (future)

Connects the presentation layer to the AI use cases.

Architecture:
    User Action → ViewModel → Use Cases → Domain → Events
                                                      ↓
    UI Update ← ViewModel ← (direct return or events) ┘
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from returns.result import Success

from src.application.ai_services.commands import (
    ApproveCodeSuggestionCommand,
    SuggestCodesCommand,
)
from src.application.ai_services.usecases import (
    approve_code_suggestion,
    suggest_codes,
)

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.ai_services.core.entities import CodeSuggestion
    from src.contexts.ai_services.core.protocols import CodeAnalyzerProtocol
    from src.contexts.coding.infra.repositories import SQLiteCodeRepository


@dataclass
class SuggestionDTO:
    """DTO for displaying a suggestion in the UI."""

    suggestion_id: str
    name: str
    color: str
    rationale: str
    confidence: float
    context_preview: str


class AICodingViewModel(QObject):
    """
    ViewModel for AI coding features.

    Manages:
    - Code suggestion requests and results
    - Suggestion approval/rejection
    - Loading and error states

    Signals:
        suggestions_loading: Analysis started
        suggestions_received(list): Suggestions ready to display
        suggestion_approved(str, int): Suggestion approved (suggestion_id, code_id)
        suggestion_rejected(str): Suggestion rejected
        error_occurred(str, str): Error occurred (operation, message)
    """

    suggestions_loading = Signal()
    suggestions_received = Signal(list)  # list[SuggestionDTO]
    suggestion_approved = Signal(str, int)  # suggestion_id, created_code_id
    suggestion_rejected = Signal(str)  # suggestion_id
    error_occurred = Signal(str, str)  # operation, message

    def __init__(
        self,
        code_analyzer: CodeAnalyzerProtocol,
        code_repo: SQLiteCodeRepository,
        event_bus: EventBus,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            code_analyzer: AI service for generating suggestions
            code_repo: Repository for codes
            event_bus: Event bus for publishing events
            parent: Optional Qt parent
        """
        super().__init__(parent)
        self._code_analyzer = code_analyzer
        self._code_repo = code_repo
        self._event_bus = event_bus

        # State: current suggestions keyed by ID
        self._suggestions: dict[str, CodeSuggestion] = {}
        self._current_source_id: int | None = None

    # =========================================================================
    # Public API
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
            self._process_suggestions(suggestions)
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
        suggestion = self._suggestions.get(suggestion_id)
        if not suggestion:
            self.error_occurred.emit(
                "approve", f"Suggestion not found: {suggestion_id}"
            )
            return

        # Use suggestion values as defaults
        final_name = name or suggestion.name
        final_color = color or suggestion.color.to_hex()

        command = ApproveCodeSuggestionCommand(
            suggestion_id=suggestion_id,
            name=final_name,
            color=final_color,
            memo=memo,
        )

        result = approve_code_suggestion(
            command=command,
            suggestion=suggestion,
            code_repo=self._code_repo,
            event_bus=self._event_bus,
        )

        if isinstance(result, Success):
            code = result.unwrap()
            # Remove from local state
            del self._suggestions[suggestion_id]
            self.suggestion_approved.emit(suggestion_id, code.id.value)
        else:
            error_msg = str(result.failure())
            self.error_occurred.emit("approve", error_msg)

    def reject_suggestion(self, suggestion_id: str, _reason: str | None = None) -> None:
        """
        Reject a suggestion.

        Args:
            suggestion_id: ID of suggestion to reject
            _reason: Optional rejection reason (unused, reserved for future)
        """
        if suggestion_id not in self._suggestions:
            return

        # Remove from local state (no persistence for rejections)
        del self._suggestions[suggestion_id]
        self.suggestion_rejected.emit(suggestion_id)

    def dismiss_all_suggestions(self) -> None:
        """Dismiss all current suggestions."""
        suggestion_ids = list(self._suggestions.keys())
        self._suggestions.clear()
        for sid in suggestion_ids:
            self.suggestion_rejected.emit(sid)

    def get_suggestion(self, suggestion_id: str) -> CodeSuggestion | None:
        """
        Get a suggestion by ID.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            The suggestion if found, None otherwise
        """
        return self._suggestions.get(suggestion_id)

    def get_all_suggestions(self) -> list[SuggestionDTO]:
        """
        Get all current suggestions as DTOs.

        Returns:
            List of suggestion DTOs
        """
        return [self._to_dto(s) for s in self._suggestions.values()]

    def has_suggestions(self) -> bool:
        """Check if there are any current suggestions."""
        return len(self._suggestions) > 0

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _process_suggestions(self, suggestions: list[CodeSuggestion]) -> None:
        """Process and store suggestions."""
        self._suggestions.clear()
        for suggestion in suggestions:
            self._suggestions[suggestion.id.value] = suggestion

        # Convert to DTOs for UI
        dtos = [self._to_dto(s) for s in suggestions]
        self.suggestions_received.emit(dtos)

    def _to_dto(self, suggestion: CodeSuggestion) -> SuggestionDTO:
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
