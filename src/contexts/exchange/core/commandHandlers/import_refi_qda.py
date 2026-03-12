"""
Import REFI-QDA Use Case.

Imports codes, sources, and codings from a REFI-QDA .qdpx archive
by delegating to existing command handlers.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers.create_category import create_category
from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commands import (
    CreateCategoryCommand,
    CreateCodeCommand,
)
from src.contexts.coding.core.entities import Code, TextPosition, TextSegment
from src.contexts.coding.core.events import SegmentCoded
from src.contexts.exchange.core.commands import ImportRefiQdaCommand
from src.contexts.exchange.core.events import RefiQdaImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda
from src.contexts.projects.core.events import SourceAdded
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId, SegmentId, SourceId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CategoryRepository,
        CodeRepository,
        SegmentRepository,
    )
    from src.contexts.sources.core.commandHandlers._state import SourceRepository
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.exchange.core")


@metered_command("import_refi_qda")
def import_refi_qda(
    command: ImportRefiQdaCommand,
    source_repo: SourceRepository,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
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
        failure = ImportFailed.file_not_found(
            command.source_path, format_label="REFI_QDA"
        )
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)
    except (zipfile.BadZipFile, ET.ParseError) as e:
        logger.error("Failed to parse QDPX: %s", e)
        return OperationResult.fail(
            error=f"Failed to parse QDPX file: {e}",
            error_code="REFI_QDA_NOT_IMPORTED/PARSE_ERROR",
        )

    # 1. Create categories (via create_category handler)
    guid_to_category_id: dict[str, str] = {}
    for parsed_cat in parsed.categories:
        cat_result = create_category(
            command=CreateCategoryCommand(
                name=parsed_cat.name,
                memo=parsed_cat.memo,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            session=session,
        )
        if cat_result.is_success:
            guid_to_category_id[parsed_cat.guid] = cat_result.data.id.value

    # 2. Create codes (via create_code handler)
    guid_to_code_id: dict[str, CodeId] = {}
    guid_to_code_name: dict[str, str] = {}
    codes_created = 0

    for parsed_code in parsed.codes:
        category_id = None
        if (
            parsed_code.category_guid
            and parsed_code.category_guid in guid_to_category_id
        ):
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
            session=session,
        )

        if result.is_success:
            code: Code = result.data
            guid_to_code_id[parsed_code.guid] = code.id
            guid_to_code_name[parsed_code.guid] = parsed_code.name
            codes_created += 1

    # 3. Create sources
    # Note: We persist directly rather than delegating to add_text_source because
    # that handler requires ProjectState and does uniqueness checks that are
    # incompatible with bulk import. We publish SourceAdded events to keep the
    # event log complete and trigger reactive UI updates.
    guid_to_source_id: dict[str, SourceId] = {}
    guid_to_source_name: dict[str, str] = {}
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
        event_bus.publish(
            SourceAdded.create(
                source_id=source_id,
                name=parsed_source.name,
                source_type=SourceType.TEXT,
                file_path=Path(f"import://{parsed_source.name}"),
                file_size=len(parsed_source.fulltext) if parsed_source.fulltext else 0,
                origin="refi-qda-import",
            )
        )
        guid_to_source_id[parsed_source.guid] = source_id
        guid_to_source_name[parsed_source.guid] = parsed_source.name
        guid_to_fulltext[parsed_source.guid] = parsed_source.fulltext
        sources_created += 1

    # 4. Create segments (codings)
    # Note: We persist directly rather than delegating to apply_code because
    # that handler runs overlap detection that would reject legitimate imported
    # codings. We publish SegmentCoded events for event log completeness.
    segments_created = 0
    for coding in parsed.codings:
        code_id = guid_to_code_id.get(coding.code_guid)
        source_id = guid_to_source_id.get(coding.source_guid)
        if not code_id or not source_id:
            continue

        fulltext = guid_to_fulltext.get(coding.source_guid, "")
        selected_text = fulltext[coding.start : coding.end] if fulltext else ""
        position = TextPosition(start=coding.start, end=coding.end)

        segment = TextSegment(
            id=SegmentId.new(),
            source_id=source_id,
            code_id=code_id,
            position=position,
            selected_text=selected_text,
        )
        segment_repo.save(segment)
        event_bus.publish(
            SegmentCoded.create(
                segment_id=segment.id,
                code_id=code_id,
                code_name=guid_to_code_name.get(coding.code_guid, ""),
                source_id=source_id,
                source_name=guid_to_source_name.get(coding.source_guid, ""),
                position=position,
                selected_text=selected_text,
            )
        )
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
        codes_created,
        sources_created,
        segments_created,
        command.source_path,
    )

    return OperationResult.ok(data=event)
