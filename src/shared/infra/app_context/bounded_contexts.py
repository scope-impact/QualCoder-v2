"""
Bounded Context Classes for QualCoder.

These classes bundle repositories for each bounded context.
They are created when a project is opened and cleared when it closes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
    from src.contexts.projects.infra.settings_repository import (
        SQLiteProjectSettingsRepository,
    )
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
    Sources bounded context - manages source files.

    Provides access to:
    - SourceRepository: CRUD for source files
    """

    source_repo: SourceRepositoryProtocol

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
    ) -> SourcesContext:
        """Create a SourcesContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.sources.infra.source_repository import (
            SQLiteSourceRepository,
        )

        return cls(
            source_repo=SQLiteSourceRepository(connection),
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
    ) -> FoldersContext:
        """Create a FoldersContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
        from src.contexts.folders.infra.folder_repository import (
            SQLiteFolderRepository,
        )

        return cls(
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
    ) -> CasesContext:
        """Create a CasesContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
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
    ) -> CodingContext:
        """Create a CodingContext with all repositories."""
        if connection is None:
            raise ValueError("Connection required")
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
    - GitAdapter: Git repository operations (for VCS)
    - DiffableAdapter: SQLite to JSON conversion (for VCS)
    """

    project_repo: SQLiteProjectRepository | Any
    settings_repo: SQLiteProjectSettingsRepository | Any
    git_adapter: Any | None = None  # GitRepositoryAdapter
    diffable_adapter: Any | None = None  # SqliteDiffableAdapter

    @classmethod
    def create(
        cls,
        connection: Connection | None = None,
        project_path: str | None = None,
    ) -> ProjectsContext:
        """Create a ProjectsContext with all repositories."""
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
