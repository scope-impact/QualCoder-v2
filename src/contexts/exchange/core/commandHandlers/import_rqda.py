"""
Import RQDA Use Case.

Imports codes, sources, and codings from an RQDA SQLite database.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commands import CreateCodeCommand
from src.contexts.coding.core.entities import Code, TextPosition, TextSegment
from src.contexts.coding.core.events import SegmentCoded
from src.contexts.exchange.core.commands import ImportRqdaCommand
from src.contexts.exchange.core.events import RqdaImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.rqda_reader import read_rqda
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


@metered_command("import_rqda")
def import_rqda(
    command: ImportRqdaCommand,
    source_repo: SourceRepository,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Import an RQDA project from a SQLite database.

    1. Read RQDA database
    2. Create codes (via create_code handler)
    3. Create sources
    4. Create segments
    5. Publish event
    """
    logger.debug("import_rqda: path=%s", command.source_path)

    source_path = Path(command.source_path)
    if not source_path.exists():
        failure = ImportFailed.file_not_found(command.source_path, format_label="RQDA")
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    try:
        parsed = read_rqda(source_path)
    except sqlite3.Error as e:
        logger.error("Failed to read RQDA: %s", e)
        return OperationResult.fail(
            error=f"Failed to read RQDA database: {e}",
            error_code="RQDA_NOT_IMPORTED/PARSE_ERROR",
        )

    # 1. Create codes (via create_code handler)
    rqda_id_to_code_id: dict[int, CodeId] = {}
    rqda_id_to_code_name: dict[int, str] = {}
    codes_created = 0

    for rqda_code in parsed.codes:
        result = create_code(
            command=CreateCodeCommand(
                name=rqda_code.name,
                color=rqda_code.color,
                memo=rqda_code.memo,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            session=session,
        )

        if result.is_success:
            code: Code = result.data
            rqda_id_to_code_id[rqda_code.id] = code.id
            rqda_id_to_code_name[rqda_code.id] = rqda_code.name
            codes_created += 1

    # 2. Create sources
    # Note: Direct persistence + event publishing (see import_refi_qda.py for rationale)
    rqda_id_to_source_id: dict[int, SourceId] = {}
    rqda_id_to_source_name: dict[int, str] = {}
    sources_created = 0

    for rqda_source in parsed.sources:
        source_id = SourceId.new()
        source = Source(
            id=source_id,
            name=rqda_source.name,
            fulltext=rqda_source.fulltext,
            source_type=SourceType.TEXT,
        )
        source_repo.save(source)
        event_bus.publish(
            SourceAdded.create(
                source_id=source_id,
                name=rqda_source.name,
                source_type=SourceType.TEXT,
                file_path=Path(f"import://{rqda_source.name}"),
                file_size=len(rqda_source.fulltext) if rqda_source.fulltext else 0,
                origin="rqda-import",
            )
        )
        rqda_id_to_source_id[rqda_source.id] = source_id
        rqda_id_to_source_name[rqda_source.id] = rqda_source.name
        sources_created += 1

    # 3. Create segments
    # Note: Direct persistence + event publishing (see import_refi_qda.py for rationale)
    segments_created = 0
    for coding in parsed.codings:
        code_id = rqda_id_to_code_id.get(coding.code_id)
        source_id = rqda_id_to_source_id.get(coding.source_id)
        if not code_id or not source_id:
            continue

        position = TextPosition(start=coding.start, end=coding.end)
        segment = TextSegment(
            id=SegmentId.new(),
            source_id=source_id,
            code_id=code_id,
            position=position,
            selected_text=coding.selected_text,
        )
        segment_repo.save(segment)
        event_bus.publish(
            SegmentCoded.create(
                segment_id=segment.id,
                code_id=code_id,
                code_name=rqda_id_to_code_name.get(coding.code_id, ""),
                source_id=source_id,
                source_name=rqda_id_to_source_name.get(coding.source_id, ""),
                position=position,
                selected_text=coding.selected_text,
            )
        )
        segments_created += 1

    # 4. Publish event
    event = RqdaImported.create(
        source_path=command.source_path,
        codes_created=codes_created,
        sources_created=sources_created,
        segments_created=segments_created,
    )
    event_bus.publish(event)

    logger.info(
        "RQDA imported: %d codes, %d sources, %d segments from %s",
        codes_created,
        sources_created,
        segments_created,
        command.source_path,
    )

    return OperationResult.ok(data=event)
