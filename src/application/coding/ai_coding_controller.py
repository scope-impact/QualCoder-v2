"""
AI Coding Controller - Application Service

Orchestrates AI-powered code suggestion and duplicate detection by:
1. Loading state from repositories
2. Calling AI services (code analyzer, code comparator)
3. Calling pure domain derivers
4. Persisting changes on success
5. Publishing domain events

This is the "Imperative Shell" for AI coding features.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.domain.ai_services.derivers import (
    AISuggestionState,
    derive_approve_merge,
    derive_approve_suggestion,
    derive_detect_duplicates,
    derive_dismiss_merge,
    derive_reject_suggestion,
    derive_suggest_code,
)
from src.domain.ai_services.entities import (
    CodeSuggestion,
    DuplicateCandidate,
    SuggestionId,
)
from src.domain.ai_services.events import (
    CodeSuggested,
    CodeSuggestionApproved,
    CodeSuggestionRejected,
    DuplicatesDetected,
    MergeSuggestionApproved,
    MergeSuggestionDismissed,
)
from src.domain.coding.entities import Code, Color
from src.domain.coding.events import CodeCreated, CodesMerged
from src.domain.shared.types import CodeId, SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.ai.code_analyzer import LLMCodeAnalyzer
    from src.infrastructure.ai.code_comparator import LLMCodeComparator
    from src.infrastructure.coding.repositories import (
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )


class AICodingController:
    """
    Controller for AI-powered coding operations.

    Coordinates between:
    - AI services (code analyzer, code comparator)
    - Domain derivers (pure business logic)
    - Repositories (data persistence)
    - Event bus (event publishing)
    """

    def __init__(
        self,
        code_repo: SQLiteCodeRepository,
        segment_repo: SQLiteSegmentRepository,
        event_bus: EventBus,
        code_analyzer: LLMCodeAnalyzer | None = None,
        code_comparator: LLMCodeComparator | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            code_repo: Repository for Code entities
            segment_repo: Repository for Segment entities
            event_bus: Event bus for publishing domain events
            code_analyzer: AI service for code suggestions (optional)
            code_comparator: AI service for duplicate detection (optional)
        """
        self._code_repo = code_repo
        self._segment_repo = segment_repo
        self._event_bus = event_bus
        self._code_analyzer = code_analyzer
        self._code_comparator = code_comparator

        # In-memory storage for pending suggestions
        self._pending_suggestions: dict[str, CodeSuggestion] = {}
        self._pending_duplicates: dict[tuple[int, int], DuplicateCandidate] = {}

    # =========================================================================
    # Code Suggestion Operations
    # =========================================================================

    def suggest_codes(
        self,
        text: str,
        source_id: int,
        max_suggestions: int | None = None,
    ) -> Result[list[CodeSuggestion], str]:
        """
        Analyze text and suggest new codes.

        Args:
            text: The uncoded text to analyze
            source_id: ID of the source being analyzed
            max_suggestions: Maximum number of suggestions

        Returns:
            Success with list of suggestions, or Failure with error message
        """
        if self._code_analyzer is None:
            return Failure("Code analyzer not configured")

        # Build state
        existing_codes = tuple(self._code_repo.get_all())
        source = SourceId(value=source_id)

        # Call AI service
        result = self._code_analyzer.suggest_codes(
            text=text,
            existing_codes=existing_codes,
            source_id=source,
            max_suggestions=max_suggestions,
        )

        if isinstance(result, Failure):
            return result

        suggestions = result.unwrap()

        # Store pending suggestions and publish events
        for suggestion in suggestions:
            self._pending_suggestions[suggestion.id.value] = suggestion

            # Derive and publish event
            state = self._build_suggestion_state()
            event_result = derive_suggest_code(
                name=suggestion.name,
                color=suggestion.color,
                rationale=suggestion.rationale,
                contexts=suggestion.contexts,
                confidence=suggestion.confidence,
                source_id=source,
                state=state,
            )

            if isinstance(event_result, CodeSuggested):
                self._event_bus.publish(event_result)

        return Success(suggestions)

    def approve_suggestion(
        self,
        suggestion_id: str,
        modified_name: str | None = None,
        modified_color: str | None = None,
        modified_memo: str | None = None,
    ) -> Result[Code, str]:
        """
        Approve a code suggestion and create the code.

        Args:
            suggestion_id: ID of the suggestion to approve
            modified_name: Optional modified name
            modified_color: Optional modified color (hex)
            modified_memo: Optional memo for the new code

        Returns:
            Success with created Code, or Failure with error message
        """
        # Find pending suggestion
        suggestion = self._pending_suggestions.get(suggestion_id)
        if suggestion is None:
            return Failure(f"Suggestion {suggestion_id} not found")

        # Determine final values
        final_name = modified_name or suggestion.name
        final_color = (
            Color.from_hex(modified_color) if modified_color else suggestion.color
        )

        # Build state and derive event
        state = self._build_suggestion_state()
        result = derive_approve_suggestion(
            suggestion_id=SuggestionId(value=suggestion_id),
            final_name=final_name,
            final_color=final_color,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeSuggestionApproved = result

        # Create the code entity
        code = Code(
            id=event.created_code_id,
            name=event.final_name,
            color=final_color,
            memo=modified_memo,
            owner=None,
        )

        # Persist the code
        self._code_repo.save(code)

        # Remove from pending
        del self._pending_suggestions[suggestion_id]

        # Publish events
        self._event_bus.publish(event)

        # Also publish CodeCreated for other listeners
        code_created = CodeCreated.create(
            code_id=code.id,
            name=code.name,
            color=code.color,
            memo=code.memo,
            category_id=code.category_id,
            owner=code.owner,
        )
        self._event_bus.publish(code_created)

        return Success(code)

    def reject_suggestion(
        self,
        suggestion_id: str,
        reason: str | None = None,
    ) -> Result[None, str]:
        """
        Reject a code suggestion.

        Args:
            suggestion_id: ID of the suggestion to reject
            reason: Optional rejection reason

        Returns:
            Success with None, or Failure with error message
        """
        # Find pending suggestion
        suggestion = self._pending_suggestions.get(suggestion_id)
        if suggestion is None:
            return Failure(f"Suggestion {suggestion_id} not found")

        # Build state and derive event
        state = self._build_suggestion_state()
        result = derive_reject_suggestion(
            suggestion_id=SuggestionId(value=suggestion_id),
            reason=reason,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CodeSuggestionRejected = result

        # Remove from pending
        del self._pending_suggestions[suggestion_id]

        # Publish event
        self._event_bus.publish(event)

        return Success(None)

    def get_pending_suggestions(self) -> list[CodeSuggestion]:
        """Get all pending code suggestions."""
        return list(self._pending_suggestions.values())

    # =========================================================================
    # Duplicate Detection Operations
    # =========================================================================

    def detect_duplicates(
        self,
        threshold: float | None = None,
    ) -> Result[list[DuplicateCandidate], str]:
        """
        Detect potentially duplicate codes.

        Args:
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            Success with list of duplicate candidates, or Failure with error
        """
        if self._code_comparator is None:
            return Failure("Code comparator not configured")

        # Get all codes
        existing_codes = tuple(self._code_repo.get_all())

        if len(existing_codes) < 2:
            return Success([])

        # Call AI service
        result = self._code_comparator.find_duplicates(
            codes=existing_codes,
            threshold=threshold,
        )

        if isinstance(result, Failure):
            return result

        candidates = result.unwrap()

        # Store pending duplicates and publish event
        for candidate in candidates:
            key = (candidate.code_a_id.value, candidate.code_b_id.value)
            self._pending_duplicates[key] = candidate

        # Derive and publish detection event
        state = self._build_suggestion_state()
        event_result = derive_detect_duplicates(
            candidates=tuple(candidates),
            threshold=threshold or 0.8,
            codes_analyzed=len(existing_codes),
            state=state,
        )

        if isinstance(event_result, DuplicatesDetected):
            self._event_bus.publish(event_result)

        return Success(candidates)

    def approve_merge(
        self,
        source_code_id: int,
        target_code_id: int,
    ) -> Result[Code, str]:
        """
        Approve a merge suggestion and merge the codes.

        Args:
            source_code_id: ID of code to merge from (will be deleted)
            target_code_id: ID of code to merge into (will remain)

        Returns:
            Success with target Code, or Failure with error message
        """
        # Get codes
        source_code = self._code_repo.get_by_id(CodeId(value=source_code_id))
        target_code = self._code_repo.get_by_id(CodeId(value=target_code_id))

        if source_code is None:
            return Failure(f"Source code {source_code_id} not found")
        if target_code is None:
            return Failure(f"Target code {target_code_id} not found")

        # Count segments to move
        source_segments = self._segment_repo.get_by_code(CodeId(value=source_code_id))
        segments_to_move = len(source_segments)

        # Build state and derive event
        state = self._build_suggestion_state()
        result = derive_approve_merge(
            source_code_id=CodeId(value=source_code_id),
            target_code_id=CodeId(value=target_code_id),
            segments_to_move=segments_to_move,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: MergeSuggestionApproved = result

        # Perform the merge: reassign segments and delete source code
        self._segment_repo.reassign_code(
            CodeId(value=source_code_id),
            CodeId(value=target_code_id),
        )
        self._code_repo.delete(CodeId(value=source_code_id))

        # Remove from pending duplicates
        key = (source_code_id, target_code_id)
        self._pending_duplicates.pop(key, None)
        # Also check reverse key
        key_reverse = (target_code_id, source_code_id)
        self._pending_duplicates.pop(key_reverse, None)

        # Publish events
        self._event_bus.publish(event)

        # Also publish CodesMerged for other listeners
        codes_merged = CodesMerged.create(
            source_code_id=source_code.id,
            source_code_name=source_code.name,
            target_code_id=target_code.id,
            target_code_name=target_code.name,
            segments_moved=segments_to_move,
        )
        self._event_bus.publish(codes_merged)

        return Success(target_code)

    def dismiss_merge(
        self,
        code_a_id: int,
        code_b_id: int,
        reason: str | None = None,
    ) -> Result[None, str]:
        """
        Dismiss a merge suggestion (mark as not duplicates).

        Args:
            code_a_id: First code ID
            code_b_id: Second code ID
            reason: Optional reason for dismissal

        Returns:
            Success with None, or Failure with error message
        """
        # Build state and derive event
        state = self._build_suggestion_state()
        result = derive_dismiss_merge(
            source_code_id=CodeId(value=code_a_id),
            target_code_id=CodeId(value=code_b_id),
            reason=reason,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: MergeSuggestionDismissed = result

        # Remove from pending duplicates
        key = (code_a_id, code_b_id)
        self._pending_duplicates.pop(key, None)
        # Also check reverse key
        key_reverse = (code_b_id, code_a_id)
        self._pending_duplicates.pop(key_reverse, None)

        # Publish event
        self._event_bus.publish(event)

        return Success(None)

    def get_pending_duplicates(self) -> list[DuplicateCandidate]:
        """Get all pending duplicate candidates."""
        return list(self._pending_duplicates.values())

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _build_suggestion_state(self) -> AISuggestionState:
        """Build the current state for AI suggestion derivers."""
        return AISuggestionState(
            existing_codes=tuple(self._code_repo.get_all()),
            pending_suggestions=tuple(self._pending_suggestions.values()),
            pending_duplicates=tuple(self._pending_duplicates.values()),
        )
