"""
Exchange Infra: CSV Parser

Parses survey CSV files into structured row data.
Uses stdlib csv module for robust parsing.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

from src.contexts.cases.core.entities import AttributeType


@dataclass(frozen=True)
class CSVParseResult:
    """Result of parsing a CSV file."""

    headers: list[str]
    rows: list[dict[str, str]]
    name_column: str | None = None


def parse_survey_csv(
    text: str,
    name_column: str | None = None,
) -> CSVParseResult:
    """
    Parse a survey CSV into headers and row dicts.

    Args:
        text: Raw CSV text
        name_column: Column to use as case name. Defaults to first column.

    Returns:
        CSVParseResult with headers, rows, and resolved name_column
    """
    if not text.strip():
        return CSVParseResult(headers=[], rows=[], name_column=None)

    reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)

    if reader.fieldnames is None:
        return CSVParseResult(headers=[], rows=[], name_column=None)

    headers = [h.strip() for h in reader.fieldnames]

    resolved_name_column = (
        name_column if name_column else (headers[0] if headers else None)
    )

    rows = []
    for row in reader:
        cleaned = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        rows.append(cleaned)

    return CSVParseResult(
        headers=headers,
        rows=rows,
        name_column=resolved_name_column,
    )


# ============================================================
# Type Inference
# ============================================================

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def infer_attribute_type(values: list[str]) -> AttributeType:
    """Infer the best-fit AttributeType from a list of string values.

    Empty strings are skipped. If all non-empty values match a type,
    that type is returned. Otherwise defaults to TEXT.
    """
    non_empty = [v for v in values if v]
    if not non_empty:
        return AttributeType.TEXT

    if all(_is_numeric(v) for v in non_empty):
        return AttributeType.NUMBER

    if all(_DATE_RE.match(v) for v in non_empty):
        return AttributeType.DATE

    if all(v.lower() in ("true", "false") for v in non_empty):
        return AttributeType.BOOLEAN

    return AttributeType.TEXT


def infer_column_types(
    parse_result: CSVParseResult,
) -> dict[str, AttributeType]:
    """Infer AttributeType for each column in a CSVParseResult.

    Skips the name_column (case name, not an attribute).
    """
    types: dict[str, AttributeType] = {}
    for header in parse_result.headers:
        if header == parse_result.name_column:
            continue
        column_values = [row.get(header, "") for row in parse_result.rows]
        types[header] = infer_attribute_type(column_values)
    return types
