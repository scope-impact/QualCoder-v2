"""
Import File Source Use Case

Functional use case for importing a file-based source by file path.
Used by AI agents to programmatically add documents, PDFs, images,
audio, and video to the project without inline content.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Success

from src.contexts.projects.core.commands import (
    ImportFileSourceCommand,
    RemoveSourceCommand,
)
from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.projects.core.events import SourceAdded
from src.contexts.projects.core.invariants import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
    detect_source_type,
    is_source_name_unique,
)
from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.contexts.sources.infra.pdf_extractor import PdfExtractor
from src.contexts.sources.infra.text_extractor import TextExtractor
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

ALL_SUPPORTED_EXTENSIONS = sorted(
    TEXT_EXTENSIONS
    | PDF_EXTENSIONS
    | IMAGE_EXTENSIONS
    | AUDIO_EXTENSIONS
    | VIDEO_EXTENSIONS
)


def import_file_source(
    command: ImportFileSourceCommand,
    state: ProjectState,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Import a file-based source into the current project.

    Functional use case following 5-step pattern:
    1. Validate project is open and file path is valid
    2. Detect source type and validate it's supported
    3. Resolve name, check uniqueness; if dry_run return preview
    4. Extract text content where applicable, persist source
    5. Publish SourceAdded event

    Args:
        command: Command with file path and optional metadata
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
            error_code="SOURCE_NOT_IMPORTED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Validate file path is absolute
    file_path = Path(command.file_path)
    if not file_path.is_absolute():
        return OperationResult.fail(
            error=f"File path must be absolute: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/RELATIVE_PATH",
            suggestions=("Provide an absolute file path",),
        )

    # Validate file exists and is accessible
    if not file_path.exists():
        return OperationResult.fail(
            error=f"File not found: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/FILE_NOT_FOUND",
            suggestions=("Check that the file path is correct and the file exists",),
        )

    if not file_path.is_file():
        return OperationResult.fail(
            error=f"Path is not a file: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/NOT_A_FILE",
            suggestions=("Provide a path to a file, not a directory",),
        )

    # Step 2: Detect source type
    source_type = detect_source_type(file_path)
    if source_type == SourceType.UNKNOWN:
        supported = ", ".join(ALL_SUPPORTED_EXTENSIONS)
        return OperationResult.fail(
            error=f"Unsupported file type: {file_path.suffix}. Supported extensions: {supported}",
            error_code="SOURCE_NOT_IMPORTED/UNSUPPORTED_TYPE",
        )

    # Step 3: Resolve name and check uniqueness
    name = command.name.strip() if command.name else file_path.name
    if not name:
        return OperationResult.fail(
            error="Source name cannot be empty",
            error_code="SOURCE_NOT_IMPORTED/EMPTY_NAME",
            suggestions=("Provide a non-empty name or omit to use filename",),
        )

    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    if not is_source_name_unique(name, existing_sources):
        return OperationResult.fail(
            error=f"Source with name '{name}' already exists",
            error_code="SOURCE_NOT_IMPORTED/DUPLICATE_NAME",
            suggestions=(
                "Use a different name via the 'name' parameter",
                "Check existing sources with list_sources",
            ),
        )

    # Get file size
    file_size = file_path.stat().st_size

    # Dry run: return preview without persisting
    if command.dry_run:
        return OperationResult.ok(
            data={
                "dry_run": True,
                "file_path": str(file_path),
                "name": name,
                "source_type": source_type.value,
                "file_size": file_size,
                "message": f"File '{name}' ({source_type.value}, {file_size} bytes) is valid and ready to import",
            }
        )

    # Step 4: Extract text content for text/PDF sources
    fulltext: str | None = None
    extractors = {SourceType.TEXT: TextExtractor, SourceType.PDF: PdfExtractor}
    extractor_cls = extractors.get(source_type)
    if extractor_cls is not None:
        extractor = extractor_cls()
        if extractor.supports(file_path):
            extraction_result = extractor.extract(file_path)
            if isinstance(extraction_result, Success):
                fulltext = extraction_result.unwrap().content

    # Create Source entity
    source_id = SourceId.new()

    source = Source(
        id=source_id,
        name=name,
        source_type=source_type,
        status=SourceStatus.IMPORTED,
        file_path=file_path,
        file_size=file_size,
        origin=command.origin,
        memo=command.memo,
        fulltext=fulltext,
    )

    # Persist to repository
    if source_repo:
        source_repo.save(source)

    # Step 5: Publish SourceAdded event
    event = SourceAdded.create(
        source_id=source_id,
        name=name,
        source_type=source_type,
        file_path=file_path,
        file_size=file_size,
        origin=command.origin,
        memo=command.memo,
        owner=None,
    )
    event_bus.publish(event)

    return OperationResult.ok(
        data=source,
        rollback=RemoveSourceCommand(source_id=source.id.value),
    )
