"""
Export REFI-QDA Use Case.

Exports the full project as a REFI-QDA 1.0 .qdpx archive.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.exchange.core.commands import ExportRefiQdaCommand
from src.contexts.exchange.core.events import RefiQdaExported
from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CategoryRepository,
        CodeRepository,
        SegmentRepository,
    )
    from src.contexts.sources.core.commandHandlers._state import SourceRepository
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.exchange.core")


def export_refi_qda(
    command: ExportRefiQdaCommand,
    source_repo: SourceRepository,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Export full project as REFI-QDA .qdpx.

    1. Load all data
    2. Write QDPX archive
    3. Publish event
    """
    logger.debug("export_refi_qda: path=%s", command.output_path)

    codes = code_repo.get_all()
    categories = category_repo.get_all()
    sources = source_repo.get_all()

    # Collect all segments across all sources
    all_segments = []
    for source in sources:
        all_segments.extend(segment_repo.get_by_source(source.id))

    try:
        write_refi_qda(
            codes=codes,
            categories=categories,
            sources=sources,
            segments=all_segments,
            output_path=command.output_path,
            project_name=command.project_name,
        )
    except OSError as e:
        logger.error("export_refi_qda I/O error: %s", e)
        return OperationResult.fail(
            error=f"Failed to write QDPX: {e}",
            error_code="REFI_QDA_NOT_EXPORTED/IO_ERROR",
        )

    event = RefiQdaExported.create(
        output_path=command.output_path,
        code_count=len(codes),
        source_count=len(sources),
        segment_count=len(all_segments),
    )
    event_bus.publish(event)

    logger.info(
        "REFI-QDA exported: %d codes, %d sources, %d segments to %s",
        len(codes), len(sources), len(all_segments), command.output_path,
    )

    return OperationResult.ok(data=event)
