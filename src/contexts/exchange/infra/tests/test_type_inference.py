"""
Exchange Infra: Type Inference Tests

TDD tests for inferring AttributeType from CSV column values.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.unit]


@allure.epic("QualCoder v2")
@allure.feature("QC-051 Firebase Analytics Import")
@allure.story("QC-051.01 CSV Type Inference")
class TestInferAttributeType:
    """Tests for inferring attribute type from a list of string values."""

    @allure.title("Integer values infer as NUMBER")
    def test_integers_infer_as_number(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["1", "2", "3", "100"]) == AttributeType.NUMBER

    @allure.title("Float values infer as NUMBER")
    def test_floats_infer_as_number(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["1.5", "2.7", "3.14"]) == AttributeType.NUMBER

    @allure.title("Mixed int and float infer as NUMBER")
    def test_mixed_numeric_infer_as_number(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["1", "2.5", "300"]) == AttributeType.NUMBER

    @allure.title("Negative numbers infer as NUMBER")
    def test_negative_numbers_infer_as_number(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["-1", "-2.5", "3"]) == AttributeType.NUMBER

    @allure.title("ISO date strings infer as DATE")
    def test_iso_dates_infer_as_date(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["2026-01-15", "2026-03-01"]) == AttributeType.DATE

    @allure.title("Boolean strings infer as BOOLEAN")
    def test_booleans_infer_as_boolean(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["true", "false", "True", "FALSE"]) == AttributeType.BOOLEAN

    @allure.title("Mixed text values infer as TEXT")
    def test_mixed_text_infer_as_text(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["hello", "world", "123abc"]) == AttributeType.TEXT

    @allure.title("Empty values are skipped during inference")
    def test_empty_values_skipped(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["1", "", "3", ""]) == AttributeType.NUMBER

    @allure.title("All empty values infer as TEXT")
    def test_all_empty_infer_as_text(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["", "", ""]) == AttributeType.TEXT

    @allure.title("Empty list infers as TEXT")
    def test_empty_list_infer_as_text(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type([]) == AttributeType.TEXT

    @allure.title("Mixed numeric and text infer as TEXT")
    def test_mixed_numeric_text_infer_as_text(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import infer_attribute_type

        assert infer_attribute_type(["1", "hello", "3"]) == AttributeType.TEXT


@allure.epic("QualCoder v2")
@allure.feature("QC-051 Firebase Analytics Import")
@allure.story("QC-051.01 CSV Column Type Inference")
class TestInferColumnTypes:
    """Tests for inferring types across all columns of a CSVParseResult."""

    @allure.title("Infers types for each column in a CSV")
    def test_infer_column_types(self):
        from src.contexts.cases.core.entities import AttributeType
        from src.contexts.exchange.infra.csv_parser import (
            CSVParseResult,
            infer_column_types,
        )

        result = CSVParseResult(
            headers=["name", "age", "active", "joined"],
            rows=[
                {"name": "Alice", "age": "30", "active": "true", "joined": "2026-01-01"},
                {"name": "Bob", "age": "25", "active": "false", "joined": "2026-02-15"},
            ],
            name_column="name",
        )

        types = infer_column_types(result)
        assert "name" not in types  # name_column is skipped
        assert types["age"] == AttributeType.NUMBER
        assert types["active"] == AttributeType.BOOLEAN
        assert types["joined"] == AttributeType.DATE

    @allure.title("Skips name column in type inference")
    def test_skips_name_column(self):
        from src.contexts.exchange.infra.csv_parser import (
            CSVParseResult,
            infer_column_types,
        )

        result = CSVParseResult(
            headers=["name", "score"],
            rows=[{"name": "Alice", "score": "85"}],
            name_column="name",
        )

        types = infer_column_types(result)
        assert "name" not in types
        assert "score" in types
