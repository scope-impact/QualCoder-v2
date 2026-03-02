"""
Bounded Context Classes for QualCoder.

These classes bundle repositories for each bounded context.
They are created when a project is opened and cleared when it closes.
Supports SQLite (primary) with optional Convex sync.
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
    from src.shared.infra.sync import SyncEngine
    from src.shared.infra.sync.outbox import OutboxWriter


def _create_outbox(
    connection: Connection, sync_engine: SyncEngine | None
) -> OutboxWriter | None:
    """Create an OutboxWriter when cloud sync is enabled, otherwise None."""
    if sync_engine is None:
        return None
    from src.shared.infra.sync.outbox import OutboxWriter

    return OutboxWriter(connection)


@dataclass
class SourcesContext:
    """
    Sources bounded context - manages source files.

    Provides access to:
    - SourceRepository: CRUD for source files
    """

    source_repo: SourceRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
        sync_engine: SyncEngine | None = None,
        event_bus: Any = None,  # noqa: ARG003
    ) -> SourcesContext:
        """Create a SourcesContext with all repositories."""
        if backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            from src.contexts.sources.infra.convex_repositories import (
                ConvexSourceRepository,
            )

            return cls(
                source_repo=ConvexSourceRepository(convex_client),
            )
        else:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
            from src.contexts.sources.infra.source_repository import (
                SQLiteSourceRepository,
            )

            return cls(
                source_repo=SQLiteSourceRepository(
                    connection, outbox=_create_outbox(connection, sync_engine)
                ),
            )


@dataclass
class FoldersContext:
    """
    Folders bounded context - manages folder hierarchy for organizing sources.

    Provides access to:
    - FolderRepository: CRUD for folder hierarchy
    """

    folder_repo: FolderRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        convex_client: ConvexClientWrapper | None = None,
        backend_type: BackendType = BackendType.SQLITE,
        sync_engine: SyncEngine | None = None,
        event_bus: Any = None,  # noqa: ARG003
    ) -> FoldersContext:
        """Create a FoldersContext with all repositories."""
        if backend_type == BackendType.CONVEX:
            if convex_client is None:
                raise ValueError("ConvexClientWrapper required for Convex backend")
            from src.contexts.sources.infra.convex_repositories import (
                ConvexFolderRepository,
            )

            return cls(
                folder_repo=ConvexFolderRepository(convex_client),
            )
        else:
            if connection is None:
                raise ValueError("SQLAlchemy connection required for SQLite backend")
            from src.contexts.folders.infra.folder_repository import (
                SQLiteFolderRepository,
            )

            return cls(
                folder_repo=SQLiteFolderRepository(
                    connection, outbox=_create_outbox(connection, sync_engine)
                ),
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
        sync_engine: SyncEngine | None = None,
        event_bus: Any = None,  # noqa: ARG003
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

            return cls(
                case_repo=SQLiteCaseRepository(
                    connection, outbox=_create_outbox(connection, sync_engine)
                )
            )


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
        sync_engine: SyncEngine | None = None,
        event_bus: Any = None,  # noqa: ARG003
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

            outbox = _create_outbox(connection, sync_engine)
            return cls(
                code_repo=SQLiteCodeRepository(connection, outbox=outbox),
                category_repo=SQLiteCategoryRepository(connection, outbox=outbox),
                segment_repo=SQLiteSegmentRepository(connection, outbox=outbox),
            )


@dataclass
class ProjectsContext:
    """
    Projects bounded context - manages project metadata and settings.

    Provides access to:
    - ProjectRepository: Project creation, validation, loading
    - SettingsRepository: Project-level settings
    - GitAdapter: Git repository operations (for VCS)
    - DiffableAdapter: SQLite to JSON conversion (for VCS)

    Note: ProjectsContext currently only supports SQLite backend as
    project metadata is stored locally. For Convex backend, project
    settings are stored in Convex via the prj_settings table.
    """

    project_repo: SQLiteProjectRepository | Any  # SQLite or Convex
    settings_repo: SQLiteProjectSettingsRepository | Any  # SQLite or Convex
    git_adapter: Any | None = None  # GitRepositoryAdapter
    diffable_adapter: Any | None = None  # SqliteDiffableAdapter

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        _convex_client: ConvexClientWrapper | None = None,  # Reserved for future use
        _backend_type: BackendType = BackendType.SQLITE,  # Reserved for future use
        project_path: str | None = None,
    ) -> ProjectsContext:
        """Create a ProjectsContext with all repositories."""
        # ProjectsContext always uses SQLite for local project file management
        # but can use Convex for cloud project settings
        if connection is None:
            raise ValueError("SQLAlchemy connection required for project management")

        from pathlib import Path

        from src.contexts.projects.infra.git_repository_adapter import (
            GitRepositoryAdapter,
        )
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )
        from src.contexts.projects.infra.settings_repository import (
            SQLiteProjectSettingsRepository,
        )
        from src.contexts.projects.infra.sqlite_diffable_adapter import (
            SqliteDiffableAdapter,
        )

        # Create VCS adapters if project path is provided
        git_adapter = None
        diffable_adapter = None
        if project_path:
            project_dir = Path(project_path).parent
            git_adapter = GitRepositoryAdapter(project_dir)
            diffable_adapter = SqliteDiffableAdapter()

        return cls(
            project_repo=SQLiteProjectRepository(connection),
            settings_repo=SQLiteProjectSettingsRepository(connection),
            git_adapter=git_adapter,
            diffable_adapter=diffable_adapter,
        )
