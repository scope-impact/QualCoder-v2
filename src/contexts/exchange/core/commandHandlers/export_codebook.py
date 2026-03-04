"""
Export Codebook Use Case.

Exports all codes and categories as a plain-text codebook document.
Returns OperationResult with ExportManifest on success.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.exchange.core.commands import ExportCodebookCommand
from src.contexts.exchange.core.derivers import derive_export_codebook
from src.contexts.exchange.core.events import CodebookExported
from src.contexts.exchange.core.failure_events import ExportFailed
from src.contexts.exchange.infra.codebook_writer import write_codebook
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CategoryRepository,
        CodeRepository,
    )
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.exchange.core")


def export_codebook(
    command: ExportCodebookCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Export the codebook as a plain-text document.

    1. Load state (codes, categories)
    2. Derive event (validate)
    3. Write file (I/O)
    4. Publish event
    """
    logger.debug("export_codebook: path=%s", command.output_path)

    # 1. Load state
    codes = code_repo.get_all()
    categories = category_repo.get_all()

    # 2. Derive (domain decides)
    result = derive_export_codebook(
        output_path=command.output_path,
        codes=tuple(codes),
        categories=tuple(categories),
    )

    # 3. Handle failure
    if isinstance(result, ExportFailed):
        logger.error("export_codebook failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    # 4. Write file
    try:
        write_codebook(
            codes=codes,
            categories=categories,
            output_path=command.output_path,
            include_memos=command.include_memos,
        )
    except OSError as e:
        logger.error("export_codebook I/O error: %s", e)
        return OperationResult.fail(
            error=f"Failed to write codebook: {e}",
            error_code="CODEBOOK_NOT_EXPORTED/IO_ERROR",
            suggestions=("Check file permissions", "Try a different path"),
        )

    # 5. Publish success event
    event = CodebookExported.create(
        output_path=command.output_path,
        code_count=len(codes),
        category_count=len(categories),
        include_memos=command.include_memos,
    )
    event_bus.publish(event)

    logger.info(
        "Codebook exported: %d codes, %d categories to %s",
        len(codes),
        len(categories),
        command.output_path,
    )

    return OperationResult.ok(data=event)
