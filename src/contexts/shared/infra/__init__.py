"""Shared infrastructure - protocols and cross-cutting infrastructure."""

from src.contexts.shared.infra.protocols import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
    SourceRepository,
)

__all__ = [
    "CategoryRepository",
    "CodeRepository",
    "SegmentRepository",
    "SourceRepository",
]
