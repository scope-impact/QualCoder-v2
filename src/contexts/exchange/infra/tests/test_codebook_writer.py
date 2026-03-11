"""
Exchange Infra: Codebook Writer Tests

Tests for the plain-text codebook writer.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Category, Code, Color
from src.shared.common.types import CategoryId, CodeId

pytestmark = [pytest.mark.unit]


@allure.epic("QC-036 Exchange")
@allure.feature("QC-036 Exchange")
@allure.story("QC-036.06 Export Codebook")
class TestCodebookWriter:
    """Tests for the codebook text file writer."""

    def _make_code(
        self,
        name: str,
        color: str = "#FF0000",
        memo: str | None = None,
        category_id: CategoryId | None = None,
    ):
        return Code(
            id=CodeId.new(),
            name=name,
            color=Color.from_hex(color),
            memo=memo,
            category_id=category_id,
        )

    def _make_category(
        self, name: str, memo: str | None = None, parent_id: CategoryId | None = None
    ):
        return Category(id=CategoryId.new(), name=name, memo=memo, parent_id=parent_id)

    @allure.title("Writes basic codebook with codes, categories, and uncategorized section")
    def test_write_codebook_with_categories_and_uncategorized(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        cat = self._make_category("Emotions", memo="Emotion codes")
        codes = [
            self._make_code("Joy", "#00FF00", category_id=cat.id),
            self._make_code("Anger", "#FF0000", category_id=cat.id),
            self._make_code("Misc", "#999999"),  # uncategorized
        ]
        output_path = tmp_path / "codebook.txt"

        write_codebook(
            codes=codes,
            categories=[cat],
            output_path=output_path,
            include_memos=False,
        )

        content = output_path.read_text()
        assert "Joy" in content
        assert "Anger" in content
        assert "#00ff00" in content.lower() or "#00FF00" in content
        # Category appears before its codes
        assert content.index("Emotions") < content.index("Joy")
        assert content.index("Emotions") < content.index("Anger")
        # Uncategorized section
        assert "Uncategorized" in content
        assert "Misc" in content

    @allure.title("Writes codebook with memos when included; excludes when not")
    def test_write_codebook_memo_inclusion(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        cat = self._make_category("Emotions", memo="Emotion codes")
        codes = [
            self._make_code("Joy", "#00FF00", memo="Happy feeling", category_id=cat.id),
        ]

        # With memos
        with_memos_path = tmp_path / "with_memos.txt"
        write_codebook(
            codes=codes, categories=[cat],
            output_path=with_memos_path, include_memos=True,
        )
        content_with = with_memos_path.read_text()
        assert "Happy feeling" in content_with
        assert "Emotion codes" in content_with

        # Without memos
        without_memos_path = tmp_path / "without_memos.txt"
        write_codebook(
            codes=codes, categories=[],
            output_path=without_memos_path, include_memos=False,
        )
        content_without = without_memos_path.read_text()
        assert "Joy" in content_without
        assert "Happy feeling" not in content_without
