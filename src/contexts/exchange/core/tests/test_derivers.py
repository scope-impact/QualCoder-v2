"""
Exchange Context: Deriver Tests

Tests for pure event derivation in the exchange domain.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Category, Code, Color
from src.shared.common.types import CategoryId, CodeId

pytestmark = [pytest.mark.unit]


@allure.epic("QualCoder v2")
@allure.feature("QC-039 Import Export Formats")
@allure.story("QC-036.07 Export Derivers")
class TestDeriveExportCodebook:
    """Tests for the codebook export deriver."""

    def _make_code(
        self,
        name: str,
        color: str = "#FF0000",
        memo: str | None = None,
        category_id=None,
    ):
        return Code(
            id=CodeId.new(),
            name=name,
            color=Color.from_hex(color),
            memo=memo,
            category_id=category_id,
        )

    def _make_category(self, name: str, memo: str | None = None):
        return Category(id=CategoryId.new(), name=name, memo=memo)

    @allure.title("Derives success with codes; failure with no codes or invalid path")
    def test_derive_success_and_failure_cases(self):
        from src.contexts.exchange.core.derivers import derive_export_codebook
        from src.contexts.exchange.core.events import CodebookExported
        from src.contexts.exchange.core.failure_events import ExportFailed

        # Success with codes
        codes = (self._make_code("Joy"), self._make_code("Anger"))
        result = derive_export_codebook(
            output_path="/tmp/codebook.txt",
            codes=codes,
            categories=(),
        )
        assert isinstance(result, CodebookExported)
        assert result.code_count == 2
        assert result.category_count == 0
        assert result.output_path == "/tmp/codebook.txt"

        # Failure with no codes
        result = derive_export_codebook(
            output_path="/tmp/codebook.txt",
            codes=(),
            categories=(),
        )
        assert isinstance(result, ExportFailed)
        assert "CODEBOOK_NOT_EXPORTED/NO_CODES" in result.event_type

        # Failure with invalid path
        result = derive_export_codebook(
            output_path="",
            codes=(self._make_code("Joy"),),
            categories=(),
        )
        assert isinstance(result, ExportFailed)
        assert "INVALID_PATH" in result.event_type
