"""
Repository Factory - Backend-agnostic Repository Creation

Creates the appropriate repository implementations based on the configured backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shared.infra.repositories.protocols import BackendType

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.shared.infra.convex import ConvexClientWrapper
    from src.shared.infra.repositories.protocols import (
        CaseRepositoryProtocol,
        CategoryRepositoryProtocol,
        CodeRepositoryProtocol,
        FolderRepositoryProtocol,
        SegmentRepositoryProtocol,
        SourceRepositoryProtocol,
    )


@dataclass
class RepositorySet:
    """Container for all repository instances."""

    codes: CodeRepositoryProtocol
    categories: CategoryRepositoryProtocol
    segments: SegmentRepositoryProtocol
    sources: SourceRepositoryProtocol
    folders: FolderRepositoryProtocol
    cases: CaseRepositoryProtocol


class RepositoryFactory:
    """
    Factory for creating repository instances based on backend type.

    Supports both SQLite (local) and Convex (cloud) backends.
    """

    @staticmethod
    def create_sqlite_repositories(connection: Connection) -> RepositorySet:
        """
        Create SQLite-backed repository instances.

        Args:
            connection: SQLAlchemy connection to the SQLite database

        Returns:
            RepositorySet with SQLite implementations
        """
        from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
        from src.contexts.coding.infra.repositories import (
            SQLiteCategoryRepository,
            SQLiteCodeRepository,
            SQLiteSegmentRepository,
        )
        from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
        from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

        return RepositorySet(
            codes=SQLiteCodeRepository(connection),
            categories=SQLiteCategoryRepository(connection),
            segments=SQLiteSegmentRepository(connection),
            sources=SQLiteSourceRepository(connection),
            folders=SQLiteFolderRepository(connection),
            cases=SQLiteCaseRepository(connection),
        )

    @staticmethod
    def create_convex_repositories(client: ConvexClientWrapper) -> RepositorySet:
        """
        Create Convex-backed repository instances.

        Args:
            client: ConvexClientWrapper instance connected to the Convex backend

        Returns:
            RepositorySet with Convex implementations
        """
        from src.contexts.cases.infra.convex_repository import ConvexCaseRepository
        from src.contexts.coding.infra.convex_repositories import (
            ConvexCategoryRepository,
            ConvexCodeRepository,
            ConvexSegmentRepository,
        )
        from src.contexts.sources.infra.convex_repositories import (
            ConvexFolderRepository,
            ConvexSourceRepository,
        )

        return RepositorySet(
            codes=ConvexCodeRepository(client),
            categories=ConvexCategoryRepository(client),
            segments=ConvexSegmentRepository(client),
            sources=ConvexSourceRepository(client),
            folders=ConvexFolderRepository(client),
            cases=ConvexCaseRepository(client),
        )

    @classmethod
    def create_repositories(
        cls,
        backend_type: BackendType,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
    ) -> RepositorySet:
        """
        Create repositories based on backend type.

        Args:
            backend_type: The backend type to use
            connection: SQLAlchemy connection (required for SQLite backend)
            convex_client: Convex client (required for Convex backend)

        Returns:
            RepositorySet with appropriate implementations

        Raises:
            ValueError: If required dependencies are not provided
        """
        if backend_type == BackendType.SQLITE:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
            return cls.create_sqlite_repositories(connection)

        elif backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            return cls.create_convex_repositories(convex_client)

        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
