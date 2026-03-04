"""
Exchange Infra: CSV Parser

Parses survey CSV files into structured row data.
Uses stdlib csv module for robust parsing.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass


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
