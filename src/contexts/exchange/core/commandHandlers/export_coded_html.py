"""
Export Coded HTML Use Case.

Exports text sources with coded segments highlighted as an HTML document.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.exchange.core.commands import ExportCodedHTMLCommand
from src.contexts.exchange.core.events import CodedHTMLExported
from src.contexts.exchange.core.failure_events import ExportFailed
from src.contexts.exchange.infra.html_writer import write_coded_html
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CodeRepository,
        SegmentRepository,
    )
    from src.contexts.sources.core.commandHandlers._state import SourceRepository
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.exchange.core")


def export_coded_html(
    command: ExportCodedHTMLCommand,
    source_repo: SourceRepository,
    code_repo: CodeRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Export coded text sources as an HTML document.

    1. Load text sources (optionally filtered by source_id)
    2. Load segments and codes for each source
    3. Write HTML
    4. Publish event
    """
    logger.debug("export_coded_html: path=%s", command.output_path)

    # 1. Load sources
    from src.contexts.sources.core.entities import SourceType

    all_sources = source_repo.get_all()
    text_sources = [
        s for s in all_sources if s.source_type == SourceType.TEXT and s.fulltext
    ]

    if command.source_id:
        from src.shared.common.types import SourceId

        target_id = SourceId(value=command.source_id)
        text_sources = [s for s in text_sources if s.id == target_id]

    if not text_sources:
        failure = ExportFailed.no_sources()
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    # 2. Build data for HTML writer
    all_codes = {c.id.value: c for c in code_repo.get_all()}
    total_segments = 0
    sources_data = []

    for source in text_sources:
        segments = segment_repo.get_by_source(source.id)
        total_segments += len(segments)

        # Filter codes to only those used in this source's segments
        source_code_ids = {seg.code_id.value for seg in segments}
        source_codes = {
            cid: all_codes[cid] for cid in source_code_ids if cid in all_codes
        }

        sources_data.append(
            {
                "name": source.name,
                "fulltext": source.fulltext,
                "source_id": source.id,
                "segments": segments,
                "codes": source_codes,
            }
        )

    # 3. Write HTML
    try:
        write_coded_html(sources_data, command.output_path)
    except OSError as e:
        logger.error("export_coded_html I/O error: %s", e)
        return OperationResult.fail(
            error=f"Failed to write HTML: {e}",
            error_code="HTML_NOT_EXPORTED/IO_ERROR",
        )

    # 4. Publish event
    event = CodedHTMLExported.create(
        output_path=command.output_path,
        source_count=len(text_sources),
        segment_count=total_segments,
    )
    event_bus.publish(event)

    logger.info(
        "Coded HTML exported: %d sources, %d segments to %s",
        len(text_sources),
        total_segments,
        command.output_path,
    )

    return OperationResult.ok(data=event)
