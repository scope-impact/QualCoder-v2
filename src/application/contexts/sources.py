"""
Sources Bounded Context.

Groups repositories and services for source file management.
Owns: src_source, src_folder tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
    from src.contexts.sources.infra.source_repository import SQLiteSourceRepository


@dataclass
class SourcesContext:
    """
    Sources bounded context - manages source files and folders.

    Provides access to:
    - SourceRepository: CRUD for source files
    - FolderRepository: CRUD for folder hierarchy

    Publishes events:
    - SourceImported
    - SourceRenamed
    - SourceDeleted
    - FolderCreated
    - FolderRenamed
    - FolderDeleted
    """

    source_repo: SQLiteSourceRepository
    folder_repo: SQLiteFolderRepository

    @classmethod
    def create(cls, connection: Connection) -> SourcesContext:
        """
        Create a SourcesContext with all repositories.

        Args:
            connection: SQLAlchemy connection to the project database

        Returns:
            Configured SourcesContext
        """
        from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
        from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

        return cls(
            source_repo=SQLiteSourceRepository(connection),
            folder_repo=SQLiteFolderRepository(connection),
        )
