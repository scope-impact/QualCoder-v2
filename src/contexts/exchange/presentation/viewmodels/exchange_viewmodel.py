"""
Exchange ViewModel

Manages UI state for import/export operations.
Delegates to ExchangeCoordinator for command dispatch.
"""
from __future__ import annotations

import logging
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
    from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator

logger = logging.getLogger("qualcoder.exchange.presentation")


class ExchangeViewModel:
    """ViewModel for import/export operations."""

    def __init__(self, coordinator: ExchangeCoordinator) -> None:
        self._coordinator = coordinator
        self._last_error: str | None = None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    # === Export Operations ===

    def export_codebook(self, output_path: str, include_memos: bool = True) -> bool:
        result = self._coordinator.export_codebook(
            ExportCodebookCommand(output_path=output_path, include_memos=include_memos),
        )
        return self._handle_result(result)

    def export_coded_html(self, output_path: str, source_id: str | None = None) -> bool:
        result = self._coordinator.export_coded_html(
            ExportCodedHTMLCommand(output_path=output_path, source_id=source_id),
        )
        return self._handle_result(result)

    def export_refi_qda(self, output_path: str, project_name: str = "QualCoder Project") -> bool:
        result = self._coordinator.export_refi_qda(
            ExportRefiQdaCommand(output_path=output_path, project_name=project_name),
        )
        return self._handle_result(result)

    # === Import Operations ===

    def import_code_list(self, source_path: str) -> bool:
        result = self._coordinator.import_code_list(
            ImportCodeListCommand(source_path=source_path),
        )
        return self._handle_result(result)

    def import_survey_csv(self, source_path: str, name_column: str | None = None) -> bool:
        result = self._coordinator.import_survey_csv(
            ImportSurveyCSVCommand(source_path=source_path, name_column=name_column),
        )
        return self._handle_result(result)

    def import_refi_qda(self, source_path: str) -> bool:
        result = self._coordinator.import_refi_qda(
            ImportRefiQdaCommand(source_path=source_path),
        )
        return self._handle_result(result)

    def import_rqda(self, source_path: str) -> bool:
        result = self._coordinator.import_rqda(
            ImportRqdaCommand(source_path=source_path),
        )
        return self._handle_result(result)

    def _handle_result(self, result: OperationResult) -> bool:
        if result.is_success:
            self._last_error = None
            return True
        self._last_error = result.error
        return False
