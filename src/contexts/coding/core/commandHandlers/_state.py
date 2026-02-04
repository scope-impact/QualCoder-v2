"""
Shared state building for coding use cases.

Following DDD workshop pattern: handlers receive specific repositories,
not entire bounded contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.contexts.coding.core.derivers import CodingState
from src.shared.common.types import SourceId

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code, TextSegment


# ============================================================
# Repository Protocols (for DI)
# ============================================================


@runtime_checkable
class CodeRepository(Protocol):
    """Protocol for code repository operations needed by command handlers."""

    def get_all(self) -> list[Code]: ...
    def get_by_id(self, code_id) -> Code | None: ...
    def get_by_category(self, category_id) -> list[Code]: ...
    def save(self, code: Code) -> None: ...
    def delete(self, code_id) -> None: ...


@runtime_checkable
class CategoryRepository(Protocol):
    """Protocol for category repository operations needed by command handlers."""

    def get_all(self) -> list[Category]: ...
    def get_by_id(self, category_id) -> Category | None: ...
    def save(self, category: Category) -> None: ...
    def delete(self, category_id) -> None: ...


@runtime_checkable
class SegmentRepository(Protocol):
    """Protocol for segment repository operations needed by command handlers."""

    def get_all(self) -> list[TextSegment]: ...
    def get_by_id(self, segment_id) -> TextSegment | None: ...
    def get_by_source(self, source_id) -> list[TextSegment]: ...
    def get_by_code(self, code_id) -> list[TextSegment]: ...
    def save(self, segment: TextSegment) -> None: ...
    def delete(self, segment_id) -> None: ...
    def delete_by_code(self, code_id) -> int: ...
    def reassign_code(self, from_code_id, to_code_id) -> int: ...


# ============================================================
# State Building
# ============================================================


def build_coding_state(
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    source_id: SourceId | None = None,
    source_exists: bool = True,
    source_content_provider=None,
) -> CodingState:
    """
    Build the current state for derivers.

    Args:
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        source_id: Optional source ID for source-specific operations
        source_exists: Whether the source exists
        source_content_provider: Optional provider for source content/length

    Returns:
        CodingState for use with derivers
    """
    codes = tuple(code_repo.get_all())
    categories = tuple(category_repo.get_all())
    segments = tuple(segment_repo.get_all())

    source_length = None
    if source_id and source_content_provider:
        source_length = source_content_provider.get_length(source_id)

    return CodingState(
        existing_codes=codes,
        existing_categories=categories,
        existing_segments=segments,
        source_length=source_length,
        source_exists=source_exists,
    )
