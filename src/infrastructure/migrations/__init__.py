"""
Database Migration Infrastructure.

Provides framework for schema migrations between QualCoder versions.
Supports:
- Version tracking in project_settings
- Forward migrations with rollback support
- Transactional safety
- Compatibility views for renamed tables
"""

from src.infrastructure.migrations.framework import (
    Migration,
    MigrationError,
    MigrationRunner,
    SchemaVersion,
)

__all__ = [
    "Migration",
    "MigrationError",
    "MigrationRunner",
    "SchemaVersion",
]
