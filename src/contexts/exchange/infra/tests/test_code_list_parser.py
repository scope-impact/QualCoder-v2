"""
Exchange Infra: Code List Parser Tests

Tests for parsing plain-text code lists into code/category structures.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.unit]


@allure.epic("QC-036 Exchange")
@allure.feature("QC-036 Exchange")
@allure.story("QC-036.04 Import Code List")
class TestCodeListParser:
    """Tests for plain-text code list parser."""

    @allure.title("Parses flat list and skips empty/comment lines")
    def test_parse_flat_list_skips_blanks_and_comments(self):
        """Flat codes parsed correctly; empty lines and #-comments are ignored."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "# header comment\nJoy\n\n\nAnger\n# inline comment\nSadness\n\n"
        result = parse_code_list(text)

        assert len(result.codes) == 3
        assert [c.name for c in result.codes] == ["Joy", "Anger", "Sadness"]
        assert len(result.categories) == 0

    @allure.title("Parses indented list creating categories (spaces and tabs)")
    @pytest.mark.parametrize(
        "text",
        [
            "Emotions\n  Joy\n  Anger\nActions\n  Helping\n",
            "Emotions\n\tJoy\n\tAnger\nActions\n\tHelping\n",
        ],
        ids=["space-indent", "tab-indent"],
    )
    def test_parse_indented_list_creates_categories(self, text):
        """Indented items become codes under the parent category for both spaces and tabs."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        result = parse_code_list(text)

        assert len(result.categories) == 2
        cat_names = [c.name for c in result.categories]
        assert "Emotions" in cat_names
        assert "Actions" in cat_names
        assert len(result.codes) == 3

    @allure.title("Parsed codes reference their parent category")
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

    @allure.title("Handles mixed categorized/uncategorized and strips whitespace")
    def test_mixed_categorized_uncategorized_strips_whitespace(self):
        """Standalone codes, categorized codes, and whitespace stripping."""
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        text = "Misc\nEmotions\n  Joy\n  Anger\nOther\n"
        result = parse_code_list(text)

        assert len(result.categories) == 1
        assert result.categories[0].name == "Emotions"

        code_names = [c.name for c in result.codes]
        assert "Misc" in code_names
        assert "Joy" in code_names
        assert "Other" in code_names
        assert all(c.name == c.name.strip() for c in result.codes)

    @allure.title("Empty text returns empty result")
    def test_parse_empty_text_returns_empty(self):
        from src.contexts.exchange.infra.code_list_parser import parse_code_list

        result = parse_code_list("")
        assert len(result.codes) == 0
        assert len(result.categories) == 0
