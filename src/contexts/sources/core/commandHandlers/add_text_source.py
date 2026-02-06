"""
Add Text Source Use Case

Functional use case for adding a text source directly (no file import).
Used by AI agents to programmatically add text content to the project.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.projects.core.commands import (
    AddTextSourceCommand,
    RemoveSourceCommand,
)
from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.projects.core.events import SourceAdded
from src.contexts.projects.core.invariants import is_source_name_unique
from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def add_text_source(
    command: AddTextSourceCommand,
    state: ProjectState,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Add a text source directly to the current project (no file import).

    Functional use case following 5-step pattern:
    1. Validate project is open and inputs are valid
    2. Validate name uniqueness (invariant)
    3. Create Source entity with TEXT type
    4. Persist to repository
    5. Publish SourceAdded event

    Args:
        command: Command with source name, content, and optional metadata
        state: Project state cache
        source_repo: Repository for source operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Source entity on success, or error details on failure
    """
    # Step 1: Validate project is open
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_ADDED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Validate name
    name = command.name.strip() if command.name else ""
    if not name:
        return OperationResult.fail(
            error="Source name cannot be empty",
            error_code="SOURCE_NOT_ADDED/EMPTY_NAME",
            suggestions=("Provide a non-empty source name",),
        )

    # Validate content
    if not command.content:
        return OperationResult.fail(
            error="Source content cannot be empty",
            error_code="SOURCE_NOT_ADDED/EMPTY_CONTENT",
            suggestions=("Provide non-empty text content",),
        )

    # Step 2: Check name uniqueness (invariant)
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    if not is_source_name_unique(name, existing_sources):
        return OperationResult.fail(
            error=f"Source with name '{name}' already exists",
            error_code="SOURCE_NOT_ADDED/DUPLICATE_NAME",
            suggestions=(
                "Use a different name",
                "Check existing sources with list_sources",
            ),
        )

    # Step 3: Create Source entity
    source_id = SourceId(value=hash(name) % 1_000_000)

    # Derive SourceAdded event
    event = SourceAdded.create(
        source_id=source_id,
        name=name,
        source_type=SourceType.TEXT,
        file_path=Path(f"agent://{name}"),
        file_size=len(command.content),
        origin=command.origin,
        memo=command.memo,
        owner=None,
    )

    source = Source(
        id=source_id,
        name=name,
        source_type=SourceType.TEXT,
        status=SourceStatus.IMPORTED,
        file_path=Path(f"agent://{name}"),
        file_size=len(command.content),
        origin=command.origin,
        memo=command.memo,
        fulltext=command.content,
    )

    # Step 4: Persist to repository (source of truth)
    if source_repo:
        source_repo.save(source)

    # Step 5: Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=source,
        rollback=RemoveSourceCommand(source_id=source.id.value),
    )
