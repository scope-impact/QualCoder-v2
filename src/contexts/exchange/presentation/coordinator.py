"""
Exchange Coordinator.

Wraps functional command handlers to provide a stateful interface.
Holds references to repositories and event bus so callers don't need to.

Used by both ExchangeViewModel (UI) and ExchangeTools (MCP).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.exchange.core.commands import (
    ExportCodebookCommand,
    ExportCodedHTMLCommand,
    ExportRefiQdaCommand,
    ImportCodeListCommand,
    ImportRefiQdaCommand,
    ImportRqdaCommand,
    ImportSurveyCSVCommand,
)
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


class ExchangeCoordinator:
    """Coordinator for exchange operations.

    Provides a stateful interface over functional command handlers.
    Each method dispatches to the correct handler with the correct repos.

    Unlike CodingCoordinator, exchange handlers have heterogeneous
    signatures (different repos per handler), so there is no generic
    ``_dispatch``.
    """

    def __init__(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        case_repo,
        event_bus: EventBus,
    ) -> None:
        self._code_repo = code_repo
        self._category_repo = category_repo
        self._segment_repo = segment_repo
        self._source_repo = source_repo
        self._case_repo = case_repo
        self._event_bus = event_bus

    # =========================================================================
    # Export Commands
    # =========================================================================

    def export_codebook(self, command: ExportCodebookCommand) -> OperationResult:
        """Export the codebook as a document."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )

        return export_codebook(
            command=command,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            event_bus=self._event_bus,
        )

    def export_coded_html(self, command: ExportCodedHTMLCommand) -> OperationResult:
        """Export coded text as HTML."""
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )

        return export_coded_html(
            command=command,
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

    def export_refi_qda(self, command: ExportRefiQdaCommand) -> OperationResult:
        """Export project in REFI-QDA format (.qdpx)."""
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )

        return export_refi_qda(
            command=command,
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

    # =========================================================================
    # Import Commands
    # =========================================================================

    def import_code_list(self, command: ImportCodeListCommand) -> OperationResult:
        """Import codes from a plain-text code list."""
        from src.contexts.exchange.core.commandHandlers.import_code_list import (
            import_code_list,
        )

        return import_code_list(
            command=command,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

    def import_survey_csv(self, command: ImportSurveyCSVCommand) -> OperationResult:
        """Import survey data from a CSV file."""
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )

        return import_survey_csv(
            command=command,
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )

    def import_refi_qda(self, command: ImportRefiQdaCommand) -> OperationResult:
        """Import a REFI-QDA project (.qdpx)."""
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import (
            import_refi_qda,
        )

        return import_refi_qda(
            command=command,
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

    def import_rqda(self, command: ImportRqdaCommand) -> OperationResult:
        """Import an RQDA project (.rqda SQLite database)."""
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda

        return import_rqda(
            command=command,
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
