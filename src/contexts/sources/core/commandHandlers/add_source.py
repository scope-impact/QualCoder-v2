"""
Add Source Use Case

Functional use case for adding a source file to the project.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Success

from src.contexts.projects.core.commands import AddSourceCommand, RemoveSourceCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_add_source
from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.projects.core.events import SourceAdded
from src.contexts.projects.core.failure_events import SourceNotAdded
from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.contexts.sources.infra.pdf_extractor import PdfExtractor
from src.contexts.sources.infra.text_extractor import TextExtractor
from src.shared.common.operation_result import OperationResult
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def add_source(
    command: AddSourceCommand,
    state: ProjectState,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Add a source file to the current project.

    Functional use case following 5-step pattern:
    1. Validate project is open
    2. Derive SourceAdded event (pure)
    3. Extract text content if applicable
    4. Persist to repository and update state
    5. Publish event

    Args:
        command: Command with source path and metadata
        state: Project state cache
        sources_ctx: Sources context with repository
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Source entity on success, or error details on failure
    """
    # Step 1: Validate
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_ADDED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    source_path = Path(command.source_path)

    # Step 2: Build domain state and derive event
    # Get existing sources from repo (source of truth) instead of state cache
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    domain_state = DomainProjectState(
        path_exists=lambda p: p.exists(),
        parent_writable=lambda _p: True,
        existing_sources=existing_sources,
    )

    result = derive_add_source(
        source_path=source_path,
        origin=command.origin,
        memo=command.memo,
        owner=None,
        state=domain_state,
    )

    if isinstance(result, SourceNotAdded):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"SOURCE_NOT_ADDED/{result.event_type.upper()}",
        )

    event: SourceAdded = result

    # Step 3: Extract text content for text/PDF sources
    fulltext: str | None = None
    file_size = event.file_size

    if event.source_type == SourceType.TEXT:
        extractor = TextExtractor()
        if extractor.supports(event.file_path):
            extraction_result = extractor.extract(event.file_path)
            if isinstance(extraction_result, Success):
                extracted = extraction_result.unwrap()
                fulltext = extracted.content
                file_size = extracted.file_size

    elif event.source_type == SourceType.PDF:
        pdf_extractor = PdfExtractor()
        if pdf_extractor.supports(event.file_path):
            extraction_result = pdf_extractor.extract(event.file_path)
            if isinstance(extraction_result, Success):
                extracted = extraction_result.unwrap()
                fulltext = extracted.content
                file_size = extracted.file_size

    # Create source entity
    source = Source(
        id=event.source_id,
        name=event.name,
        source_type=event.source_type,
        status=SourceStatus.IMPORTED,
        file_path=event.file_path,
        file_size=file_size,
        origin=event.origin,
        memo=event.memo,
        fulltext=fulltext,
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
