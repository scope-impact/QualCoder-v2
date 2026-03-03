"""
Import REFI-QDA Use Case.

Imports codes, sources, and codings from a REFI-QDA .qdpx archive
by delegating to existing command handlers.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.coding.core.commands import CreateCodeCommand
from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.entities import Code, TextPosition, TextSegment
from src.contexts.exchange.core.commands import ImportRefiQdaCommand
from src.contexts.exchange.core.events import RefiQdaImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CategoryRepository,
        CodeRepository,
        SegmentRepository,
    )
    from src.contexts.sources.core.commandHandlers._state import SourceRepository
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.exchange.core")


def import_refi_qda(
    command: ImportRefiQdaCommand,
    source_repo: SourceRepository,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Import a REFI-QDA project from a .qdpx archive.

    1. Parse the archive
    2. Create codes (via create_code handler)
    3. Create sources
    4. Create segments (codings)
    5. Publish event
    """
    logger.debug("import_refi_qda: path=%s", command.source_path)

    source_path = Path(command.source_path)
    try:
        parsed = read_refi_qda(source_path)
    except FileNotFoundError:
        failure = ImportFailed.file_not_found(command.source_path, format_label="REFI_QDA")
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)
    except Exception as e:
        logger.error("Failed to parse QDPX: %s", e)
        return OperationResult.fail(
            error=f"Failed to parse QDPX file: {e}",
            error_code="REFI_QDA_NOT_IMPORTED/PARSE_ERROR",
        )

    # 1. Create categories
    from src.contexts.coding.core.entities import Category
    from src.shared.common.types import CategoryId

    guid_to_category_id: dict[str, str] = {}
    for parsed_cat in parsed.categories:
        cat_id = CategoryId.new()
        cat = Category(id=cat_id, name=parsed_cat.name, memo=parsed_cat.memo)
        category_repo.save(cat)
        guid_to_category_id[parsed_cat.guid] = cat_id.value

    # 2. Create codes
    guid_to_code_id: dict[str, CodeId] = {}
    codes_created = 0

    for parsed_code in parsed.codes:
        category_id = None
        if parsed_code.category_guid and parsed_code.category_guid in guid_to_category_id:
            category_id = guid_to_category_id[parsed_code.category_guid]

        result = create_code(
            command=CreateCodeCommand(
                name=parsed_code.name,
                color=parsed_code.color,
                memo=parsed_code.memo,
                category_id=category_id,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        if result.is_success:
            code: Code = result.data
            guid_to_code_id[parsed_code.guid] = code.id
            codes_created += 1

    # 3. Create sources
    guid_to_source_id: dict[str, SourceId] = {}
    guid_to_fulltext: dict[str, str] = {}
    sources_created = 0

    for parsed_source in parsed.sources:
        source_id = SourceId.new()
        source = Source(
            id=source_id,
            name=parsed_source.name,
            fulltext=parsed_source.fulltext,
            source_type=SourceType.TEXT,
        )
        source_repo.save(source)
        guid_to_source_id[parsed_source.guid] = source_id
        guid_to_fulltext[parsed_source.guid] = parsed_source.fulltext
        sources_created += 1

    # 4. Create segments (codings)
    segments_created = 0
    for coding in parsed.codings:
        code_id = guid_to_code_id.get(coding.code_guid)
        source_id = guid_to_source_id.get(coding.source_guid)
        if not code_id or not source_id:
            continue

        fulltext = guid_to_fulltext.get(coding.source_guid, "")
        selected_text = fulltext[coding.start:coding.end] if fulltext else ""

        segment = TextSegment(
            id=SegmentId.new(),
            source_id=source_id,
            code_id=code_id,
            position=TextPosition(start=coding.start, end=coding.end),
            selected_text=selected_text,
        )
        segment_repo.save(segment)
        segments_created += 1

    # 5. Publish event
    event = RefiQdaImported.create(
        source_path=command.source_path,
        codes_created=codes_created,
        sources_created=sources_created,
        segments_created=segments_created,
    )
    event_bus.publish(event)

    logger.info(
        "REFI-QDA imported: %d codes, %d sources, %d segments from %s",
        codes_created, sources_created, segments_created, command.source_path,
    )

    return OperationResult.ok(data=event)
