"""
Project Infrastructure Layer.

SQLAlchemy Core implementations for project data persistence.
"""

from src.infrastructure.projects.schema import (
    case_source,
    create_all,
    drop_all,
    metadata,
    project_settings,
    source,
)
from src.infrastructure.projects.settings_repository import (
    SQLiteProjectSettingsRepository,
)
from src.infrastructure.projects.source_repository import SQLiteSourceRepository

__all__ = [
    # Repositories
    "SQLiteProjectSettingsRepository",
    "SQLiteSourceRepository",
    # Schema
    "case_source",
    "create_all",
    "drop_all",
    "metadata",
    "project_settings",
    "source",
]
