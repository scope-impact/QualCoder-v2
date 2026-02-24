"""
Coding Queries.

Pure query functions for reading coding data.
"""

from __future__ import annotations

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
)
from src.contexts.coding.core.entities import Category, Code, TextSegment
from src.shared.common.types import CodeId, SourceId


def get_all_codes(code_repo: CodeRepository) -> list[Code]:
    """Get all codes in the project."""
    return code_repo.get_all()


def get_code(code_repo: CodeRepository, code_id: int) -> Code | None:
    """Get a specific code by ID."""
    return code_repo.get_by_id(CodeId(value=code_id))


def get_segments_for_source(
    segment_repo: SegmentRepository, source_id: int
) -> list[TextSegment]:
    """Get all segments for a source."""
    return segment_repo.get_by_source(SourceId(value=source_id))


def get_segments_for_code(
    segment_repo: SegmentRepository, code_id: int
) -> list[TextSegment]:
    """Get all segments with a specific code."""
    return segment_repo.get_by_code(CodeId(value=code_id))


def get_all_categories(category_repo: CategoryRepository) -> list[Category]:
    """Get all categories."""
    return category_repo.get_all()
