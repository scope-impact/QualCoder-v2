"""
Exchange Infra: CSV Parser Tests

Tests for parsing survey CSV files into case data.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.unit]


@allure.epic("QC-036 Exchange")
@allure.feature("QC-036 Exchange")
@allure.story("QC-036.05 Import Survey CSV")
class TestCsvParser:
    """Tests for survey CSV parser."""

    @allure.title("Parses basic CSV with headers, data, whitespace stripping, and quoted fields")
    def test_parse_csv_with_various_formats(self):
        """Parse CSV with header row, data rows, stripped whitespace, and quoted commas."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = 'Name,Age,Comment\nAlice,30,"Has a, comma"\nBob,25,Simple\n'
        result = parse_survey_csv(csv_text)

        assert len(result.rows) == 2
        assert result.headers == ["Name", "Age", "Comment"]
        assert result.rows[0]["Name"] == "Alice"
        assert result.rows[0]["Age"] == "30"
        assert result.rows[0]["Comment"] == "Has a, comma"
        assert result.rows[1]["Name"] == "Bob"

    @allure.title("First column used as default case name; custom name_column supported")
    def test_parse_csv_name_column(self):
        """Default name_column is first column; can override with name_column param."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = "ID,Participant,Score\n1,Alice,85\n"
        result_default = parse_survey_csv(csv_text)
        assert result_default.name_column == "ID"

        result_custom = parse_survey_csv(csv_text, name_column="Participant")
        assert result_custom.name_column == "Participant"

    @allure.title("Empty and header-only CSV return empty rows")
    @pytest.mark.parametrize(
        "csv_text,expected_headers",
        [
            ("", []),
            ("Name,Age\n", ["Name", "Age"]),
        ],
        ids=["empty", "header-only"],
    )
    def test_parse_empty_and_header_only(self, csv_text, expected_headers):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        result = parse_survey_csv(csv_text)
        assert len(result.rows) == 0
        assert result.headers == expected_headers

    @allure.title("Strips whitespace from headers and values")
    def test_parse_csv_strips_whitespace(self):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = " Name , Age \n Alice , 30 \n"
        result = parse_survey_csv(csv_text)

        assert result.headers == ["Name", "Age"]
        assert result.rows[0]["Name"] == "Alice"
        assert result.rows[0]["Age"] == "30"
