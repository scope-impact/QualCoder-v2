"""
Projects Bounded Context.

Groups repositories and services for project management.
Owns: prj_settings table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
    from src.contexts.projects.infra.settings_repository import (
        SQLiteProjectSettingsRepository,
    )


@dataclass
class ProjectsContext:
    """
    Projects bounded context - manages project metadata and settings.

    Provides access to:
    - ProjectRepository: Project creation, validation, loading
    - SettingsRepository: Project-level settings

    Publishes events:
    - ProjectOpened
    - ProjectClosed
    - ProjectCreated
    - SettingChanged
    """

    project_repo: SQLiteProjectRepository
    settings_repo: SQLiteProjectSettingsRepository

    @classmethod
    def create(cls, connection: Connection) -> ProjectsContext:
        """
        Create a ProjectsContext with all repositories.

        Args:
            connection: SQLAlchemy connection to the project database

        Returns:
            Configured ProjectsContext
        """
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
