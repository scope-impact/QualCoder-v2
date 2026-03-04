"""
Exchange Infra: CSV Parser Tests (TDD - RED phase)

Tests for parsing survey CSV files into case data.
"""

from __future__ import annotations


class TestCsvParser:
    """Tests for survey CSV parser."""

    def test_parse_basic_csv(self):
        """Parse CSV with header row and data rows."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = "Name,Age,Gender\nAlice,30,F\nBob,25,M\n"
        result = parse_survey_csv(csv_text)

        assert len(result.rows) == 2
        assert result.headers == ["Name", "Age", "Gender"]
        assert result.rows[0]["Name"] == "Alice"
        assert result.rows[0]["Age"] == "30"
        assert result.rows[1]["Name"] == "Bob"

    def test_parse_csv_with_name_column(self):
        """The first column is used as case name by default."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = "CaseName,Score\nP001,85\nP002,92\n"
        result = parse_survey_csv(csv_text)

        assert result.name_column == "CaseName"
        assert result.rows[0]["CaseName"] == "P001"

    def test_parse_empty_csv(self):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        result = parse_survey_csv("")
        assert len(result.rows) == 0
        assert len(result.headers) == 0

    def test_parse_header_only(self):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        result = parse_survey_csv("Name,Age\n")
        assert len(result.rows) == 0
        assert result.headers == ["Name", "Age"]

    def test_parse_csv_strips_whitespace(self):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = " Name , Age \n Alice , 30 \n"
        result = parse_survey_csv(csv_text)

        assert result.headers == ["Name", "Age"]
        assert result.rows[0]["Name"] == "Alice"
        assert result.rows[0]["Age"] == "30"

    def test_parse_csv_with_quoted_fields(self):
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = 'Name,Comment\nAlice,"Has a, comma"\n'
        result = parse_survey_csv(csv_text)

        assert result.rows[0]["Comment"] == "Has a, comma"

    def test_parse_csv_custom_name_column(self):
        """Can specify which column to use as case name."""
        from src.contexts.exchange.infra.csv_parser import parse_survey_csv

        csv_text = "ID,Participant,Score\n1,Alice,85\n"
        result = parse_survey_csv(csv_text, name_column="Participant")

        assert result.name_column == "Participant"
