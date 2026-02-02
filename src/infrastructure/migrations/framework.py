"""
Migration Framework - Core infrastructure for database schema migrations.

Provides version tracking, migration execution, and rollback support.
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SchemaVersion(Enum):
    """
    Schema versions for QualCoder database.

    Version history:
    - V1: Original QualCoder schema (mixed contexts)
    - V2: Schema isolation by bounded context
    """

    V1 = 1
    V2 = 2


SCHEMA_VERSION_KEY = "schema_version"


class MigrationError(Exception):
    """Raised when a migration fails."""

    pass


@dataclass(frozen=True)
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    from_version: SchemaVersion
    to_version: SchemaVersion
    message: str


class Migration(ABC):
    """
    Abstract base class for database migrations.

    Each migration handles upgrading from one schema version to the next,
    and provides rollback capability for safe recovery.
    """

    @property
    @abstractmethod
    def from_version(self) -> SchemaVersion:
        """The version this migration upgrades from."""
        ...

    @property
    @abstractmethod
    def to_version(self) -> SchemaVersion:
        """The version this migration upgrades to."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this migration does."""
        ...

    @abstractmethod
    def upgrade(self, conn: Connection) -> None:
        """
        Apply the migration.

        Args:
            conn: SQLAlchemy connection (transaction managed externally)

        Raises:
            MigrationError: If migration fails
        """
        ...

    @abstractmethod
    def downgrade(self, conn: Connection) -> None:
        """
        Roll back the migration.

        Args:
            conn: SQLAlchemy connection (transaction managed externally)

        Raises:
            MigrationError: If rollback fails
        """
        ...

    def pre_check(self, _conn: Connection) -> bool:
        """
        Optional pre-migration validation.

        Override to add custom checks before migration runs.

        Args:
            _conn: SQLAlchemy connection (unused in base implementation)

        Returns:
            True if migration can proceed, False otherwise
        """
        return True


class MigrationRunner:
    """
    Executes migrations and tracks schema versions.

    The runner manages:
    - Reading/writing schema version from project_settings
    - Executing migrations in order
    - Transaction management and rollback on failure
    """

    def __init__(self, migrations: list[Migration] | None = None) -> None:
        """
        Initialize the migration runner.

        Args:
            migrations: List of available migrations. If None, uses default set.
        """
        self._migrations = migrations or []
        # Sort migrations by from_version for ordered execution
        self._migrations.sort(key=lambda m: m.from_version.value)

    def register(self, migration: Migration) -> None:
        """Register a migration with the runner."""
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.from_version.value)

    def get_current_version(self, conn: Connection) -> SchemaVersion:
        """
        Get the current schema version from the database.

        Args:
            conn: SQLAlchemy connection

        Returns:
            Current SchemaVersion, defaults to V1 if not set
        """
        # Determine which settings table to use
        settings_table = self._get_settings_table_name(conn)

        if settings_table is None:
            # No settings table at all - very old database
            return SchemaVersion.V1

        # Try to read schema_version from settings table
        result = conn.execute(
            text(f"SELECT value FROM {settings_table} WHERE key = :key").bindparams(
                key=SCHEMA_VERSION_KEY
            )
        )
        row = result.fetchone()

        if row is None:
            # No version recorded - assume V1 (original schema)
            return SchemaVersion.V1

        try:
            version_int = int(row[0])
            return SchemaVersion(version_int)
        except (ValueError, TypeError):
            return SchemaVersion.V1

    def _get_settings_table_name(self, conn: Connection) -> str | None:
        """
        Determine the correct settings table name.

        In V2, the actual table is `prj_settings` while `project_settings` is a view.
        We need to use the actual table for writes.

        Returns:
            Table name to use, or None if no settings table exists
        """
        # Check for V2 table first (prj_settings)
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='prj_settings'"
            )
        )
        if result.fetchone():
            return "prj_settings"

        # Check for V1 table (project_settings as actual table, not view)
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='project_settings'"
            )
        )
        if result.fetchone():
            return "project_settings"

        return None

    def set_version(self, conn: Connection, version: SchemaVersion) -> None:
        """
        Set the schema version in the database.

        Args:
            conn: SQLAlchemy connection
            version: Version to set
        """
        # Determine which settings table to use
        settings_table = self._get_settings_table_name(conn)

        if settings_table is None:
            raise MigrationError("No settings table found to store version")

        # Check if key exists
        result = conn.execute(
            text(f"SELECT COUNT(*) FROM {settings_table} WHERE key = :key").bindparams(
                key=SCHEMA_VERSION_KEY
            )
        )
        exists = result.scalar() > 0

        if exists:
            conn.execute(
                text(
                    f"UPDATE {settings_table} SET value = :value WHERE key = :key"
                ).bindparams(key=SCHEMA_VERSION_KEY, value=str(version.value))
            )
        else:
            conn.execute(
                text(
                    f"INSERT INTO {settings_table} (key, value) VALUES (:key, :value)"
                ).bindparams(key=SCHEMA_VERSION_KEY, value=str(version.value))
            )

    def needs_migration(
        self, conn: Connection, target_version: SchemaVersion | None = None
    ) -> bool:
        """
        Check if database needs migration.

        Args:
            conn: SQLAlchemy connection
            target_version: Target version (defaults to latest)

        Returns:
            True if migration is needed
        """
        current = self.get_current_version(conn)
        target = target_version or self._get_latest_version()
        return current.value < target.value

    def migrate(
        self,
        conn: Connection,
        target_version: SchemaVersion | None = None,
    ) -> MigrationResult:
        """
        Run migrations to reach target version.

        Migrations are run in a transaction. If any migration fails,
        the transaction is rolled back and no changes are applied.

        Args:
            conn: SQLAlchemy connection
            target_version: Target version (defaults to latest)

        Returns:
            MigrationResult with success status and details
        """
        current_version = self.get_current_version(conn)
        target = target_version or self._get_latest_version()

        if current_version.value >= target.value:
            return MigrationResult(
                success=True,
                from_version=current_version,
                to_version=current_version,
                message="Already at target version",
            )

        # Find migrations to run
        migrations_to_run = [
            m
            for m in self._migrations
            if m.from_version.value >= current_version.value
            and m.to_version.value <= target.value
        ]

        if not migrations_to_run:
            return MigrationResult(
                success=False,
                from_version=current_version,
                to_version=target,
                message=f"No migration path from {current_version} to {target}",
            )

        # Run pre-checks
        for migration in migrations_to_run:
            if not migration.pre_check(conn):
                return MigrationResult(
                    success=False,
                    from_version=current_version,
                    to_version=target,
                    message=f"Pre-check failed for migration: {migration.description}",
                )

        # Execute migrations
        applied_migrations: list[Migration] = []
        try:
            for migration in migrations_to_run:
                migration.upgrade(conn)
                applied_migrations.append(migration)

            # Update version
            self.set_version(conn, target)
            conn.commit()

            return MigrationResult(
                success=True,
                from_version=current_version,
                to_version=target,
                message=f"Successfully migrated from {current_version} to {target}",
            )

        except Exception as e:
            # Rollback all applied migrations in reverse order
            conn.rollback()
            for migration in reversed(applied_migrations):
                with contextlib.suppress(Exception):
                    migration.downgrade(conn)  # Best effort rollback

            raise MigrationError(
                f"Migration failed: {e}. Rolled back all changes."
            ) from e

    def rollback(
        self,
        conn: Connection,
        target_version: SchemaVersion,
    ) -> MigrationResult:
        """
        Roll back migrations to reach target version.

        Args:
            conn: SQLAlchemy connection
            target_version: Target version to roll back to

        Returns:
            MigrationResult with success status
        """
        current_version = self.get_current_version(conn)

        if current_version.value <= target_version.value:
            return MigrationResult(
                success=True,
                from_version=current_version,
                to_version=current_version,
                message="Already at or below target version",
            )

        # Find migrations to roll back (in reverse order)
        migrations_to_rollback = [
            m
            for m in reversed(self._migrations)
            if m.to_version.value <= current_version.value
            and m.from_version.value >= target_version.value
        ]

        try:
            for migration in migrations_to_rollback:
                migration.downgrade(conn)

            self.set_version(conn, target_version)
            conn.commit()

            return MigrationResult(
                success=True,
                from_version=current_version,
                to_version=target_version,
                message=f"Successfully rolled back from {current_version} to {target_version}",
            )

        except Exception as e:
            conn.rollback()
            raise MigrationError(f"Rollback failed: {e}") from e

    def _get_latest_version(self) -> SchemaVersion:
        """Get the latest schema version from registered migrations."""
        if not self._migrations:
            return SchemaVersion.V1

        return max(m.to_version for m in self._migrations)
