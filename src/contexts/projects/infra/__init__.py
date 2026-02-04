"""
Projects Infrastructure Layer.

SQLAlchemy Core implementations for project data persistence.
Adapters for external tools (Git, sqlite-diffable).
"""

from src.contexts.projects.infra.git_repository_adapter import (
    CommitInfo,
    GitRepositoryAdapter,
)
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
from src.contexts.projects.infra.sqlite_diffable_adapter import (
    EXCLUDE_TABLES,
    VCS_DIR_NAME,
    SqliteDiffableAdapter,
)
from src.contexts.projects.infra.version_control_listener import (
    MUTATION_EVENTS,
    VersionControlListener,
)

__all__ = [
    # Repositories
    "SQLiteProjectRepository",
    "SQLiteProjectSettingsRepository",
    # Version Control Adapters
    "GitRepositoryAdapter",
    "SqliteDiffableAdapter",
    # Version Control Types
    "CommitInfo",
    # Version Control Constants
    "EXCLUDE_TABLES",
    "VCS_DIR_NAME",
    "MUTATION_EVENTS",
    # Version Control Listener
    "VersionControlListener",
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
