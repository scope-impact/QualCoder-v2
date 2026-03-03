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
