"""
Coding Bounded Context.

Groups repositories and services for qualitative coding.
Owns: cod_category, cod_code, cod_segment tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.coding.infra.repositories import (
        SQLiteCategoryRepository,
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )


@dataclass
class CodingContext:
    """
    Coding bounded context - manages codes, categories, and segments.

    Provides access to:
    - CodeRepository: CRUD for codes
    - CategoryRepository: CRUD for code categories
    - SegmentRepository: CRUD for coded text segments

    Publishes events:
    - CodeCreated, CodeRenamed, CodeDeleted
    - CategoryCreated, CategoryRenamed, CategoryDeleted
    - SegmentCreated, SegmentDeleted

    Subscribes to events:
    - SourceRenamed: Updates denormalized source_name in cod_segment
    - SourceDeleted: Deletes related segments
    """

    code_repo: SQLiteCodeRepository
    category_repo: SQLiteCategoryRepository
    segment_repo: SQLiteSegmentRepository

    @classmethod
    def create(cls, connection: Connection) -> CodingContext:
        """
        Create a CodingContext with all repositories.

        Args:
            connection: SQLAlchemy connection to the project database

        Returns:
            Configured CodingContext
        """
        from src.contexts.coding.infra.repositories import (
            SQLiteCategoryRepository,
            SQLiteCodeRepository,
            SQLiteSegmentRepository,
        )

        return cls(
            code_repo=SQLiteCodeRepository(connection),
            category_repo=SQLiteCategoryRepository(connection),
            segment_repo=SQLiteSegmentRepository(connection),
        )
