"""
Exchange Infra: Codebook Writer Tests (TDD - RED phase)

Tests for the plain-text codebook writer.
"""

from __future__ import annotations

from src.contexts.coding.core.entities import Category, Code, Color
from src.shared.common.types import CategoryId, CodeId


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

    def test_write_basic_codebook(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        codes = [
            self._make_code("Joy", "#00FF00"),
            self._make_code("Anger", "#FF0000"),
        ]
        output_path = tmp_path / "codebook.txt"

        write_codebook(
            codes=codes,
            categories=[],
            output_path=output_path,
            include_memos=False,
        )

        content = output_path.read_text()
        assert "Joy" in content
        assert "Anger" in content
        assert "#00ff00" in content.lower() or "#00FF00" in content

    def test_write_codebook_with_categories(self, tmp_path):
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
        # Category should appear as a heading before its codes
        assert content.index("Emotions") < content.index("Joy")
        assert content.index("Emotions") < content.index("Anger")

    def test_write_codebook_with_memos(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        cat = self._make_category("Emotions", memo="Emotion codes")
        codes = [
            self._make_code("Joy", "#00FF00", memo="Happy feeling", category_id=cat.id),
        ]
        output_path = tmp_path / "codebook.txt"

        write_codebook(
            codes=codes,
            categories=[cat],
            output_path=output_path,
            include_memos=True,
        )

        content = output_path.read_text()
        assert "Happy feeling" in content
        assert "Emotion codes" in content

    def test_write_codebook_without_memos_excludes_them(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        codes = [
            self._make_code("Joy", "#00FF00", memo="Happy feeling"),
        ]
        output_path = tmp_path / "codebook.txt"

        write_codebook(
            codes=codes,
            categories=[],
            output_path=output_path,
            include_memos=False,
        )

        content = output_path.read_text()
        assert "Joy" in content
        assert "Happy feeling" not in content

    def test_write_codebook_uncategorized_section(self, tmp_path):
        from src.contexts.exchange.infra.codebook_writer import write_codebook

        cat = self._make_category("Emotions")
        codes = [
            self._make_code("Joy", category_id=cat.id),
            self._make_code("Misc"),  # no category
        ]
        output_path = tmp_path / "codebook.txt"

        write_codebook(
            codes=codes,
            categories=[cat],
            output_path=output_path,
            include_memos=False,
        )

        content = output_path.read_text()
        # Uncategorized codes should appear in their own section
        assert "Uncategorized" in content
        assert "Misc" in content
