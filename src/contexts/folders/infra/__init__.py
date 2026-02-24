"""
Folders Context: Infrastructure Layer

Repositories and database schemas for folder persistence.
"""

from src.contexts.folders.infra.folder_repository import SQLiteFolderRepository

__all__ = ["SQLiteFolderRepository"]
