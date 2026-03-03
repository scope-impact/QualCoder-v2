"""
Exchange ViewModel

Manages UI state for import/export operations.
Calls command handlers directly (no intermediate service layer).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.exchange.presentation")


class ExchangeViewModel:
    """ViewModel for import/export operations."""

    def __init__(
        self,
        code_repo,
        category_repo,
        segment_repo,
        source_repo,
        case_repo,
        event_bus: EventBus,
    ):
        self._code_repo = code_repo
        self._category_repo = category_repo
        self._segment_repo = segment_repo
        self._source_repo = source_repo
        self._case_repo = case_repo
        self._event_bus = event_bus
        self._last_error: str | None = None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    # === Export Operations ===

    def export_codebook(self, output_path: str, include_memos: bool = True) -> bool:
        from src.contexts.exchange.core.commandHandlers.export_codebook import export_codebook
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        result = export_codebook(
            command=ExportCodebookCommand(output_path=output_path, include_memos=include_memos),
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def export_coded_html(self, output_path: str, source_id: str | None = None) -> bool:
        from src.contexts.exchange.core.commandHandlers.export_coded_html import export_coded_html
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand

        result = export_coded_html(
            command=ExportCodedHTMLCommand(output_path=output_path, source_id=source_id),
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def export_refi_qda(self, output_path: str, project_name: str = "QualCoder Project") -> bool:
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import export_refi_qda
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand

        result = export_refi_qda(
            command=ExportRefiQdaCommand(output_path=output_path, project_name=project_name),
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    # === Import Operations ===

    def import_code_list(self, source_path: str) -> bool:
        from src.contexts.exchange.core.commandHandlers.import_code_list import import_code_list
        from src.contexts.exchange.core.commands import ImportCodeListCommand

        result = import_code_list(
            command=ImportCodeListCommand(source_path=source_path),
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def import_survey_csv(self, source_path: str, name_column: str | None = None) -> bool:
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import import_survey_csv
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand

        result = import_survey_csv(
            command=ImportSurveyCSVCommand(source_path=source_path, name_column=name_column),
            case_repo=self._case_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def import_refi_qda(self, source_path: str) -> bool:
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import import_refi_qda
        from src.contexts.exchange.core.commands import ImportRefiQdaCommand

        result = import_refi_qda(
            command=ImportRefiQdaCommand(source_path=source_path),
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def import_rqda(self, source_path: str) -> bool:
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand

        result = import_rqda(
            command=ImportRqdaCommand(source_path=source_path),
            source_repo=self._source_repo,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )
        return self._handle_result(result)

    def _handle_result(self, result: OperationResult) -> bool:
        if result.is_success:
            self._last_error = None
            return True
        self._last_error = result.error
        return False
