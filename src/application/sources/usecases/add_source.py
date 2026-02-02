"""
Add Source Use Case

Functional use case for adding a source file to the project.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import AddSourceCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_add_source
from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.projects.core.events import SourceAdded
from src.contexts.projects.core.failure_events import SourceNotAdded
from src.contexts.sources.infra.pdf_extractor import PdfExtractor
from src.contexts.sources.infra.text_extractor import TextExtractor

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def add_source(
    command: AddSourceCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[Source, str]:
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
        Success with Source entity, or Failure with error message
    """
    # Step 1: Validate
    if state.project is None:
        return Failure("No project is currently open")

    source_path = Path(command.source_path)

    # Step 2: Build domain state and derive event
    domain_state = DomainProjectState(
        path_exists=lambda p: p.exists(),
        parent_writable=lambda _p: True,
        existing_sources=tuple(state.sources),
    )

    result = derive_add_source(
        source_path=source_path,
        origin=command.origin,
        memo=command.memo,
        owner=None,
        state=domain_state,
    )

    if isinstance(result, SourceNotAdded):
        return Failure(result.reason)

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

    # Step 4: Persist and update state
    if sources_ctx and sources_ctx.source_repo:
        sources_ctx.source_repo.save(source)

    state.add_source(source)

    # Step 5: Publish event
    event_bus.publish(event)

    return Success(source)
