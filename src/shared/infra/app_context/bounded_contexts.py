"""
Bounded Context Classes for QualCoder.

These classes bundle repositories for each bounded context.
They are created when a project is opened and cleared when it closes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
    from src.contexts.coding.infra.repositories import (
        SQLiteCategoryRepository,
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )
    from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
    from src.contexts.projects.infra.settings_repository import (
        SQLiteProjectSettingsRepository,
    )
    from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
    from src.contexts.sources.infra.source_repository import SQLiteSourceRepository


@dataclass
class SourcesContext:
    """
    Sources bounded context - manages source files and folders.

    Provides access to:
    - SourceRepository: CRUD for source files
    - FolderRepository: CRUD for folder hierarchy
    """

    source_repo: SQLiteSourceRepository
    folder_repo: SQLiteFolderRepository

    @classmethod
    def create(cls, connection: Connection) -> SourcesContext:
        """Create a SourcesContext with all repositories."""
        from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
        from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

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

    case_repo: SQLiteCaseRepository

    @classmethod
    def create(cls, connection: Connection) -> CasesContext:
        """Create a CasesContext with all repositories."""
        from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

        return cls(
            case_repo=SQLiteCaseRepository(connection),
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

    code_repo: SQLiteCodeRepository
    category_repo: SQLiteCategoryRepository
    segment_repo: SQLiteSegmentRepository

    @classmethod
    def create(cls, connection: Connection) -> CodingContext:
        """Create a CodingContext with all repositories."""
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
    """

    project_repo: SQLiteProjectRepository
    settings_repo: SQLiteProjectSettingsRepository

    @classmethod
    def create(cls, connection: Connection) -> ProjectsContext:
        """Create a ProjectsContext with all repositories."""
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
