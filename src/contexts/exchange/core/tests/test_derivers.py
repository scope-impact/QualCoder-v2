"""
Exchange Context: Deriver Tests (TDD - RED phase)

Tests for pure event derivation in the exchange domain.
"""
from __future__ import annotations

import pytest

from src.contexts.coding.core.entities import Category, Code, Color
from src.shared.common.types import CategoryId, CodeId


class TestDeriveExportCodebook:
    """Tests for the codebook export deriver."""

    def _make_code(self, name: str, color: str = "#FF0000", memo: str | None = None, category_id=None):
        return Code(
            id=CodeId.new(),
            name=name,
            color=Color.from_hex(color),
            memo=memo,
            category_id=category_id,
        )

    def _make_category(self, name: str, memo: str | None = None):
        return Category(id=CategoryId.new(), name=name, memo=memo)

    def test_derive_success_with_codes(self):
        from src.contexts.exchange.core.derivers import derive_export_codebook
        from src.contexts.exchange.core.events import CodebookExported

        codes = (self._make_code("Joy"), self._make_code("Anger"))
        categories = ()

        result = derive_export_codebook(
            output_path="/tmp/codebook.txt",
            codes=codes,
            categories=categories,
        )

        assert isinstance(result, CodebookExported)
        assert result.code_count == 2
        assert result.category_count == 0
        assert result.output_path == "/tmp/codebook.txt"

    def test_derive_failure_with_no_codes(self):
        from src.contexts.exchange.core.derivers import derive_export_codebook
        from src.contexts.exchange.core.failure_events import ExportFailed

        result = derive_export_codebook(
            output_path="/tmp/codebook.txt",
            codes=(),
            categories=(),
        )

        assert isinstance(result, ExportFailed)
        assert "CODEBOOK_NOT_EXPORTED/NO_CODES" in result.event_type

    def test_derive_failure_with_invalid_path(self):
        from src.contexts.exchange.core.derivers import derive_export_codebook
        from src.contexts.exchange.core.failure_events import ExportFailed

        codes = (self._make_code("Joy"),)

        result = derive_export_codebook(
            output_path="",
            codes=codes,
            categories=(),
        )

        assert isinstance(result, ExportFailed)
        assert "INVALID_PATH" in result.event_type
