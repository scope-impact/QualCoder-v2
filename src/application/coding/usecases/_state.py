"""
Shared state building for coding use cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.derivers import CodingState
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext


def build_coding_state(
    coding_ctx: CodingContext,
    source_id: SourceId | None = None,
    source_exists: bool = True,
    source_content_provider=None,
) -> CodingState:
    """
    Build the current state for derivers.

    Args:
        coding_ctx: Coding context with repositories
        source_id: Optional source ID for source-specific operations
        source_exists: Whether the source exists
        source_content_provider: Optional provider for source content/length

    Returns:
        CodingState for use with derivers
    """
    codes = tuple(coding_ctx.code_repo.get_all())
    categories = tuple(coding_ctx.category_repo.get_all())
    segments = tuple(coding_ctx.segment_repo.get_all())

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
