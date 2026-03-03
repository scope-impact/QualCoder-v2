"""
Exchange Context: Commands

Input DTOs for import/export operations.
Frozen dataclasses with primitive types only.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportCodebookCommand:
    """Command to export the codebook as a document."""

    output_path: str
    include_memos: bool = True


@dataclass(frozen=True)
class ImportCodeListCommand:
    """Command to import codes from a plain-text code list."""

    source_path: str


@dataclass(frozen=True)
class ImportSurveyCSVCommand:
    """Command to import survey data from a CSV file."""

    source_path: str
    name_column: str | None = None  # Defaults to first column


@dataclass(frozen=True)
class ExportCodedHTMLCommand:
    """Command to export coded text as HTML."""

    output_path: str
    source_id: str | None = None  # None = all sources
