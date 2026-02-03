"""
Bounded Context Classes for QualCoder.

These classes bundle repositories for each bounded context.
They are created when a project is opened and cleared when it closes.
Supports both SQLite and Convex backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.shared.infra.repositories import BackendType

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
    from src.contexts.projects.infra.settings_repository import (
        SQLiteProjectSettingsRepository,
    )
    from src.shared.infra.convex import ConvexClientWrapper
    from src.shared.infra.repositories import (
        CaseRepositoryProtocol,
        CategoryRepositoryProtocol,
        CodeRepositoryProtocol,
        FolderRepositoryProtocol,
        SegmentRepositoryProtocol,
        SourceRepositoryProtocol,
    )


@dataclass
class SourcesContext:
    """
    Sources bounded context - manages source files and folders.

    Provides access to:
    - SourceRepository: CRUD for source files
    - FolderRepository: CRUD for folder hierarchy
    """

    source_repo: SourceRepositoryProtocol
    folder_repo: FolderRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
    ) -> SourcesContext:
        """Create a SourcesContext with all repositories."""
        if backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            from src.contexts.sources.infra.convex_repositories import (
                ConvexFolderRepository,
                ConvexSourceRepository,
            )

            return cls(
                source_repo=ConvexSourceRepository(convex_client),
                folder_repo=ConvexFolderRepository(convex_client),
            )
        else:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
            from src.contexts.sources.infra.folder_repository import (
                SQLiteFolderRepository,
            )
            from src.contexts.sources.infra.source_repository import (
                SQLiteSourceRepository,
            )

            return cls(
                source_repo=SQLiteSourceRepository(connection),
                folder_repo=SQLiteFolderRepository(connection),
            )


@dataclass
class CasesContext:
    """
    Cases bounded context - manages research cases and attributes.

    Provides access to:
    - CaseRepository: CRUD for cases and their attributes
    """

    case_repo: CaseRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
    ) -> CasesContext:
        """Create a CasesContext with all repositories."""
        if backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            from src.contexts.cases.infra.convex_repository import ConvexCaseRepository

            return cls(case_repo=ConvexCaseRepository(convex_client))
        else:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
            from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

            return cls(case_repo=SQLiteCaseRepository(connection))


@dataclass
class CodingContext:
    """
    Coding bounded context - manages codes, categories, and segments.

    Provides access to:
    - CodeRepository: CRUD for codes
    - CategoryRepository: CRUD for code categories
    - SegmentRepository: CRUD for coded text segments
    """

    code_repo: CodeRepositoryProtocol
    category_repo: CategoryRepositoryProtocol
    segment_repo: SegmentRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
    ) -> CodingContext:
        """Create a CodingContext with all repositories."""
        if backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            from src.contexts.coding.infra.convex_repositories import (
                ConvexCategoryRepository,
                ConvexCodeRepository,
                ConvexSegmentRepository,
            )

            return cls(
                code_repo=ConvexCodeRepository(convex_client),
                category_repo=ConvexCategoryRepository(convex_client),
                segment_repo=ConvexSegmentRepository(convex_client),
            )
        else:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
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


@dataclass
class ProjectsContext:
    """
    Projects bounded context - manages project metadata and settings.

    Provides access to:
    - ProjectRepository: Project creation, validation, loading
    - SettingsRepository: Project-level settings

    Note: ProjectsContext currently only supports SQLite backend as
    project metadata is stored locally. For Convex backend, project
    settings are stored in Convex via the prj_settings table.
    """

    project_repo: SQLiteProjectRepository | Any  # SQLite or Convex
    settings_repo: SQLiteProjectSettingsRepository | Any  # SQLite or Convex

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
    ) -> ProjectsContext:
        """Create a ProjectsContext with all repositories."""
        # ProjectsContext always uses SQLite for local project file management
        # but can use Convex for cloud project settings
        if connection is None:
            raise ValueError("SQLAlchemy connection required for project management")

        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )
        from src.contexts.projects.infra.settings_repository import (
            SQLiteProjectSettingsRepository,
        )

        return cls(
            project_repo=SQLiteProjectRepository(connection),
            settings_repo=SQLiteProjectSettingsRepository(connection),
        )
