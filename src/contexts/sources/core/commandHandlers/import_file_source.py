"""
Import File Source Use Case

Functional use case for importing a file-based source by file path.
Used by AI agents to programmatically add documents, PDFs, images,
audio, and video to the project without inline content.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

import logging
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
from src.shared.infra.metrics import metered_command
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.sources.core")

ALL_SUPPORTED_EXTENSIONS = sorted(
    TEXT_EXTENSIONS
    | PDF_EXTENSIONS
    | IMAGE_EXTENSIONS
    | AUDIO_EXTENSIONS
    | VIDEO_EXTENSIONS
)

_TEXT_EXTRACTORS = {
    SourceType.TEXT: TextExtractor,
    SourceType.PDF: PdfExtractor,
}


def _extract_text(source_type: SourceType, file_path: Path) -> str | None:
    """Extract text content from a file if the source type supports it."""
    extractor_cls = _TEXT_EXTRACTORS.get(source_type)
    if extractor_cls is None:
        return None
    extractor = extractor_cls()
    if not extractor.supports(file_path):
        return None
    result = extractor.extract(file_path)
    if isinstance(result, Success):
        return result.unwrap().content
    return None


@metered_command("import_file_source")
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
    logger.debug("import_file_source: file_path=%s, name=%s", command.file_path, command.name)
    # Step 1: Validate project is open
    if state.project is None:
        logger.error("import_file_source: no project is currently open")
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_IMPORTED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Validate file path is absolute
    file_path = Path(command.file_path)
    if not file_path.is_absolute():
        logger.error("import_file_source: relative path provided, file_path=%s", command.file_path)
        return OperationResult.fail(
            error=f"File path must be absolute: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/RELATIVE_PATH",
            suggestions=("Provide an absolute file path",),
        )

    # Validate file exists and is accessible
    if not file_path.exists():
        logger.error("import_file_source: file not found, file_path=%s", command.file_path)
        return OperationResult.fail(
            error=f"File not found: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/FILE_NOT_FOUND",
            suggestions=("Check that the file path is correct and the file exists",),
        )

    if not file_path.is_file():
        logger.error("import_file_source: path is not a file, file_path=%s", command.file_path)
        return OperationResult.fail(
            error=f"Path is not a file: {command.file_path}",
            error_code="SOURCE_NOT_IMPORTED/NOT_A_FILE",
            suggestions=("Provide a path to a file, not a directory",),
        )

    # Step 2: Detect source type
    source_type = detect_source_type(file_path)
    if source_type == SourceType.UNKNOWN:
        supported = ", ".join(ALL_SUPPORTED_EXTENSIONS)
        logger.error("import_file_source: unsupported file type=%s", file_path.suffix)
        return OperationResult.fail(
            error=f"Unsupported file type: {file_path.suffix}. Supported extensions: {supported}",
            error_code="SOURCE_NOT_IMPORTED/UNSUPPORTED_TYPE",
        )

    # Step 3: Resolve name and check uniqueness
    name = command.name.strip() if command.name else file_path.name
    if not name:
        logger.error("import_file_source: source name is empty")
        return OperationResult.fail(
            error="Source name cannot be empty",
            error_code="SOURCE_NOT_IMPORTED/EMPTY_NAME",
            suggestions=("Provide a non-empty name or omit to use filename",),
        )

    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    if not is_source_name_unique(name, existing_sources):
        logger.error("import_file_source: duplicate source name=%s", name)
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
    fulltext = _extract_text(source_type, file_path)

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

    logger.info("import_file_source: imported source name=%s, id=%s, type=%s", source.name, source.id, source_type)
    return OperationResult.ok(
        data=source,
        rollback=RemoveSourceCommand(source_id=source.id.value),
    )
