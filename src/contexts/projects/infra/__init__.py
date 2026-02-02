"""
Projects Infrastructure Layer.

SQLAlchemy Core implementations for project data persistence.
"""

from src.contexts.projects.infra.project_repository import SQLiteProjectRepository
from src.contexts.projects.infra.schema import (
    create_all,
    create_all_contexts,
    drop_all,
    drop_all_contexts,
    metadata,
    prj_settings,
    project_settings,
)
from src.contexts.projects.infra.settings_repository import (
    SQLiteProjectSettingsRepository,
)

__all__ = [
    # Repositories
    "SQLiteProjectRepository",
    "SQLiteProjectSettingsRepository",
    # Schema - V2 prefixed
    "prj_settings",
    # Schema - Compatibility alias
    "project_settings",
    # Schema utilities
    "create_all",
    "create_all_contexts",
    "drop_all",
    "drop_all_contexts",
    "metadata",
]
