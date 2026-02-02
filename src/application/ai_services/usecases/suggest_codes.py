"""
Suggest Codes Use Case

Query use case for requesting AI-powered code suggestions.
This is a pure query - no database side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import SuggestCodesCommand
from src.contexts.ai_services.core.entities import CodeSuggestion
from src.contexts.ai_services.core.events import CodeSuggested
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.ai_services.core.protocols import CodeAnalyzerProtocol
    from src.contexts.coding.core.entities import Code


def suggest_codes(
    command: SuggestCodesCommand,
    code_analyzer: CodeAnalyzerProtocol,
    existing_codes: tuple[Code, ...],
    event_bus: EventBus,
) -> Result[list[CodeSuggestion], str]:
    """
    Request AI-powered code suggestions for text.

    This is a query use case - no database persistence.
    Suggestions are returned to the caller (typically ViewModel)
    for user review before approval.

    Args:
        command: Command with text to analyze and parameters
        code_analyzer: AI service for generating suggestions
        existing_codes: Current codes to avoid duplicates
        event_bus: Event bus for publishing suggestion events

    Returns:
        Success with list of suggestions, or Failure with error message
    """
    # Step 1: Validate
    if not command.text or not command.text.strip():
        return Failure("Text cannot be empty")

    if command.max_suggestions < 1:
        return Failure("Max suggestions must be at least 1")

    # Step 2: Call AI service (infrastructure)
    source_id = SourceId(value=command.source_id)

    result = code_analyzer.suggest_codes(
        text=command.text,
        existing_codes=existing_codes,
        source_id=source_id,
        max_suggestions=command.max_suggestions,
    )

    if isinstance(result, Failure):
        return result

    suggestions = result.unwrap()

    # Step 3: Publish events for each suggestion
    for suggestion in suggestions:
        event = CodeSuggested.create(
            suggestion_id=suggestion.id,
            name=suggestion.name,
            color=suggestion.color,
            rationale=suggestion.rationale,
            contexts=suggestion.contexts,
            confidence=suggestion.confidence,
            source_id=source_id,
        )
        event_bus.publish(event)

    return Success(suggestions)
