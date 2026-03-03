"""
Exchange Infra: Code List Parser Tests (TDD - RED phase)

Tests for parsing plain-text code lists into code/category structures.
"""
from __future__ import annotations

import pytest


class TestCodeListParser:
    """Tests for plain-text code list parser."""

    def test_parse_flat_list(self):
        """Simple list of code names, one per line."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Joy\nAnger\nSadness\n"
        result = parse_code_list(text)

        assert len(result.codes) == 3
        assert result.codes[0].name == "Joy"
        assert result.codes[1].name == "Anger"
        assert result.codes[2].name == "Sadness"
        assert len(result.categories) == 0

    def test_parse_indented_list_creates_categories(self):
        """Indented items become codes under the parent category."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Emotions\n  Joy\n  Anger\nActions\n  Helping\n"
        result = parse_code_list(text)

        assert len(result.categories) == 2
        cat_names = [c.name for c in result.categories]
        assert "Emotions" in cat_names
        assert "Actions" in cat_names

        assert len(result.codes) == 3
        code_names = [c.name for c in result.codes]
        assert "Joy" in code_names
        assert "Anger" in code_names
        assert "Helping" in code_names

    def test_parse_skips_empty_lines(self):
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Joy\n\n\nAnger\n\n"
        result = parse_code_list(text)

        assert len(result.codes) == 2

    def test_parse_skips_comment_lines(self):
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "# This is a comment\nJoy\n# Another comment\nAnger\n"
        result = parse_code_list(text)

        assert len(result.codes) == 2
        assert result.codes[0].name == "Joy"

    def test_parse_strips_whitespace(self):
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "  Joy  \n  Anger  \n"
        result = parse_code_list(text)

        # Top-level items with leading spaces but no parent are flat codes
        assert all(c.name == c.name.strip() for c in result.codes)

    def test_parse_empty_text_returns_empty(self):
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        result = parse_code_list("")
        assert len(result.codes) == 0
        assert len(result.categories) == 0

    def test_parsed_codes_have_category_references(self):
        """Indented codes should reference their parent category."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Emotions\n  Joy\n  Anger\n"
        result = parse_code_list(text)

        emotions_cat = next(c for c in result.categories if c.name == "Emotions")
        joy = next(c for c in result.codes if c.name == "Joy")
        anger = next(c for c in result.codes if c.name == "Anger")

        assert joy.category_name == emotions_cat.name
        assert anger.category_name == emotions_cat.name

    def test_parse_tab_indentation(self):
        """Tabs should work as indentation too."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Emotions\n\tJoy\n\tAnger\n"
        result = parse_code_list(text)

        assert len(result.categories) == 1
        assert len(result.codes) == 2

    def test_mixed_categorized_and_uncategorized(self):
        """Some codes in categories, some standalone."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Misc\nEmotions\n  Joy\n  Anger\nOther\n"
        result = parse_code_list(text)

        # Misc and Other are standalone codes (no indented children)
        # Emotions is a category (has indented children)
        assert len(result.categories) == 1
        cat_names = [c.name for c in result.categories]
        assert "Emotions" in cat_names

        code_names = [c.name for c in result.codes]
        assert "Misc" in code_names
        assert "Joy" in code_names
        assert "Other" in code_names
