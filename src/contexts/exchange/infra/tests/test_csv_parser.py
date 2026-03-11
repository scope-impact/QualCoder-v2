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

    @allure.title("Parses CSV with headers, data, quoted fields, whitespace stripping, and name_column")
    def test_parse_csv_formats_and_name_column(self):
        """Parse CSV with various formats and name_column configuration."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = 'Name,Age,Comment\nAlice,30,"Has a, comma"\nBob,25,Simple\n'
        result = parse_survey_csv(csv_text)

        assert len(result.rows) == 2
        assert result.headers == ["Name", "Age", "Comment"]
        assert result.rows[0]["Name"] == "Alice"
        assert result.rows[0]["Age"] == "30"
        assert result.rows[0]["Comment"] == "Has a, comma"
        assert result.rows[1]["Name"] == "Bob"

        # Default name_column is first column
        assert result.name_column == "Name"

        # Custom name_column
        csv_text2 = "ID,Participant,Score\n1,Alice,85\n"
        result_custom = parse_survey_csv(csv_text2, name_column="Participant")
        assert result_custom.name_column == "Participant"

        # Whitespace stripping
        csv_text3 = " Name , Age \n Alice , 30 \n"
        result_ws = parse_survey_csv(csv_text3)
        assert result_ws.headers == ["Name", "Age"]
        assert result_ws.rows[0]["Name"] == "Alice"
        assert result_ws.rows[0]["Age"] == "30"

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
