"""
Coding Queries.

Pure query functions for reading coding data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.entities import Category, Code, TextSegment
from src.contexts.shared.core.types import CodeId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext


def get_all_codes(coding_ctx: CodingContext) -> list[Code]:
    """Get all codes in the project."""
    return coding_ctx.code_repo.get_all()


def get_code(coding_ctx: CodingContext, code_id: int) -> Code | None:
    """Get a specific code by ID."""
    return coding_ctx.code_repo.get_by_id(CodeId(value=code_id))


def get_segments_for_source(
    coding_ctx: CodingContext, source_id: int
) -> list[TextSegment]:
    """Get all segments for a source."""
    return coding_ctx.segment_repo.get_by_source(SourceId(value=source_id))


def get_segments_for_code(coding_ctx: CodingContext, code_id: int) -> list[TextSegment]:
    """Get all segments with a specific code."""
    return coding_ctx.segment_repo.get_by_code(CodeId(value=code_id))


def get_all_categories(coding_ctx: CodingContext) -> list[Category]:
    """Get all categories."""
    return coding_ctx.category_repo.get_all()
