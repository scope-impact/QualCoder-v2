"""
Exchange Context: Derivers (Pure Event Derivation)

Compose invariants to derive success or failure events.
Pure functions: no I/O, no side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.exchange.core.events import CodebookExported
from src.contexts.exchange.core.failure_events import ExportFailed
from src.contexts.exchange.core.invariants import (
    can_export_codebook,
    is_valid_output_path,
)

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code


def derive_export_codebook(
    output_path: str,
    codes: tuple[Code, ...],
    categories: tuple[Category, ...],
) -> CodebookExported | ExportFailed:
    """Derive export event from state. PURE - no I/O."""
    if not can_export_codebook(code_count=len(codes)):
        return ExportFailed.no_codes()

    if not is_valid_output_path(output_path):
        return ExportFailed.invalid_path(output_path)

    return CodebookExported.create(
        output_path=output_path,
        code_count=len(codes),
        category_count=len(categories),
        include_memos=False,  # Deriver doesn't decide this; command handler sets it
    )
