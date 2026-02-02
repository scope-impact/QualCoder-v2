"""
Tests for migration framework.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Connection, create_engine, text

from src.infrastructure.migrations.framework import (
    Migration,
    MigrationError,
    MigrationRunner,
    SchemaVersion,
)


class DummyMigration(Migration):
    """Test migration that adds a column."""

    @property
    def from_version(self) -> SchemaVersion:
        return SchemaVersion.V1

    @property
    def to_version(self) -> SchemaVersion:
        return SchemaVersion.V2

    @property
    def description(self) -> str:
        return "Add test_column to project_settings"

    def upgrade(self, conn: Connection) -> None:
        conn.execute(
            text("ALTER TABLE project_settings ADD COLUMN test_column VARCHAR(100)")
        )

    def downgrade(self, conn: Connection) -> None:
        # SQLite doesn't support DROP COLUMN, so recreate table
        conn.execute(
            text("""
                CREATE TABLE project_settings_new (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """)
        )
        conn.execute(
            text("""
                INSERT INTO project_settings_new (key, value, updated_at)
                SELECT key, value, updated_at FROM project_settings
            """)
        )
        conn.execute(text("DROP TABLE project_settings"))
        conn.execute(
            text("ALTER TABLE project_settings_new RENAME TO project_settings")
        )


class FailingMigration(Migration):
    """Migration that always fails for testing rollback."""

    @property
    def from_version(self) -> SchemaVersion:
        return SchemaVersion.V1

    @property
    def to_version(self) -> SchemaVersion:
        return SchemaVersion.V2

    @property
    def description(self) -> str:
        return "Always fails"

    def upgrade(self, conn: Connection) -> None:
        raise MigrationError("Intentional failure")

    def downgrade(self, conn: Connection) -> None:
        pass


@pytest.fixture
def v1_database():
    """Create an in-memory V1 database for testing."""
    engine = create_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        # Create minimal V1 schema
        conn.execute(
            text("""
                CREATE TABLE project_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE source (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_name (
                    cid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_cat (
                    catid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_text (
                    ctid INTEGER PRIMARY KEY,
                    cid INTEGER NOT NULL,
                    fid INTEGER NOT NULL
                )
            """)
        )
        conn.commit()

    yield engine
    engine.dispose()


class TestSchemaVersion:
    """Tests for SchemaVersion enum."""

    def test_version_ordering(self):
        """Versions should be ordered numerically."""
        assert SchemaVersion.V1.value < SchemaVersion.V2.value

    def test_version_values(self):
        """Version values should match expected integers."""
        assert SchemaVersion.V1.value == 1
        assert SchemaVersion.V2.value == 2


class TestMigrationRunner:
    """Tests for MigrationRunner."""

    def test_get_current_version_default(self, v1_database):
        """Should return V1 when no version is recorded."""
        runner = MigrationRunner()

        with v1_database.connect() as conn:
            version = runner.get_current_version(conn)
            assert version == SchemaVersion.V1

    def test_set_and_get_version(self, v1_database):
        """Should correctly store and retrieve version."""
        runner = MigrationRunner()

        with v1_database.connect() as conn:
            runner.set_version(conn, SchemaVersion.V2)
            conn.commit()

            version = runner.get_current_version(conn)
            assert version == SchemaVersion.V2

    def test_needs_migration_true(self, v1_database):
        """Should return True when migration is needed."""
        runner = MigrationRunner([DummyMigration()])

        with v1_database.connect() as conn:
            assert runner.needs_migration(conn) is True

    def test_needs_migration_false(self, v1_database):
        """Should return False when already at target version."""
        runner = MigrationRunner()

        with v1_database.connect() as conn:
            runner.set_version(conn, SchemaVersion.V2)
            conn.commit()

            assert runner.needs_migration(conn, SchemaVersion.V2) is False

    def test_migrate_success(self, v1_database):
        """Should successfully apply migration."""
        runner = MigrationRunner([DummyMigration()])

        with v1_database.connect() as conn:
            result = runner.migrate(conn)

            assert result.success is True
            assert result.from_version == SchemaVersion.V1
            assert result.to_version == SchemaVersion.V2

            # Verify column was added
            row = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type='table' AND name='project_settings'"
                )
            ).fetchone()
            assert "test_column" in row[0]

    def test_migrate_already_at_version(self, v1_database):
        """Should return success when already at target version."""
        runner = MigrationRunner([DummyMigration()])

        with v1_database.connect() as conn:
            runner.set_version(conn, SchemaVersion.V2)
            conn.commit()

            result = runner.migrate(conn, SchemaVersion.V2)

            assert result.success is True
            assert "Already at target version" in result.message

    def test_migrate_failure_rolls_back(self, v1_database):
        """Should roll back on migration failure."""
        runner = MigrationRunner([FailingMigration()])

        with v1_database.connect() as conn:
            with pytest.raises(MigrationError):
                runner.migrate(conn)

            # Version should still be V1
            version = runner.get_current_version(conn)
            assert version == SchemaVersion.V1

    def test_rollback_success(self, v1_database):
        """Should successfully roll back migration."""
        runner = MigrationRunner([DummyMigration()])

        with v1_database.connect() as conn:
            # First migrate to V2
            runner.migrate(conn)

            # Then roll back to V1
            result = runner.rollback(conn, SchemaVersion.V1)

            assert result.success is True
            assert result.to_version == SchemaVersion.V1

            # Verify column was removed
            row = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type='table' AND name='project_settings'"
                )
            ).fetchone()
            assert "test_column" not in row[0]

    def test_register_migration(self, v1_database):
        """Should be able to register migrations dynamically."""
        runner = MigrationRunner()
        runner.register(DummyMigration())

        with v1_database.connect() as conn:
            assert runner.needs_migration(conn) is True


class TestMigration:
    """Tests for Migration base class."""

    def test_pre_check_default(self, v1_database):
        """Default pre_check should return True."""
        migration = DummyMigration()

        with v1_database.connect() as conn:
            assert migration.pre_check(conn) is True
