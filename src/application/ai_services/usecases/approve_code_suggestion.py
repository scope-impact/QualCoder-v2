"""
Approve Code Suggestion Use Case

Command use case for approving an AI-suggested code.
Creates a new Code entity in the database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import ApproveCodeSuggestionCommand
from src.contexts.ai_services.core.entities import CodeSuggestion, SuggestionId
from src.contexts.ai_services.core.events import CodeSuggestionApproved
from src.contexts.coding.core.entities import Code, Color
from src.contexts.coding.core.events import CodeCreated
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.coding.infra.repositories import SQLiteCodeRepository


def approve_code_suggestion(
    command: ApproveCodeSuggestionCommand,
    suggestion: CodeSuggestion,
    code_repo: SQLiteCodeRepository,
    event_bus: EventBus,
) -> Result[Code, str]:
    """
    Approve a code suggestion and create the code.

    Command use case following 5-step pattern:
    1. Validate input
    2. Build Code entity
    3. Persist to database
    4. Publish events
    5. Return result

    Args:
        command: Command with suggestion ID and final values
        suggestion: The CodeSuggestion to approve (from ViewModel state)
        code_repo: Repository for persisting the new code
        event_bus: Event bus for publishing events

    Returns:
        Success with created Code, or Failure with error message
    """
    # Step 1: Validate
    if command.suggestion_id != suggestion.id.value:
        return Failure(f"Suggestion ID mismatch: {command.suggestion_id}")

    if not command.name or not command.name.strip():
        return Failure("Code name cannot be empty")

    # Check for duplicate name
    existing = code_repo.get_by_name(command.name.strip())
    if existing is not None:
        return Failure(f"Code with name '{command.name}' already exists")

    # Step 2: Build Code entity
    try:
        color = Color.from_hex(command.color)
    except ValueError as e:
        return Failure(f"Invalid color: {e}")

    # Generate new code ID
    all_codes = code_repo.get_all()
    max_id = max((c.id.value for c in all_codes), default=0)
    new_code_id = CodeId(value=max_id + 1)

    code = Code(
        id=new_code_id,
        name=command.name.strip(),
        color=color,
        memo=command.memo,
        category_id=None,
        owner=None,
    )

    # Step 3: Persist
    code_repo.save(code)

    # Step 4: Publish events
    # AI-specific event
    modified = suggestion.name != code.name
    approved_event = CodeSuggestionApproved.create(
        suggestion_id=SuggestionId(value=command.suggestion_id),
        created_code_id=code.id,
        original_name=suggestion.name,
        final_name=code.name,
        modified=modified,
    )
    event_bus.publish(approved_event)

    # Coding context event for other listeners
    code_created_event = CodeCreated.create(
        code_id=code.id,
        name=code.name,
        color=code.color,
        memo=code.memo,
        category_id=code.category_id,
        owner=code.owner,
    )
    event_bus.publish(code_created_event)

    # Step 5: Return result
    return Success(code)
