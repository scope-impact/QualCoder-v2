"""
Tests for V2 Schema Isolation Migration.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text

from src.infrastructure.migrations.framework import MigrationRunner, SchemaVersion
from src.infrastructure.migrations.v2_schema_isolation import V2SchemaIsolationMigration


@pytest.fixture
def v1_database_with_data():
    """Create a V1 database with sample data for testing migration."""
    engine = create_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        # Create V1 schema
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
                CREATE TABLE folder (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    parent_id INTEGER,
                    created_at DATETIME
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE source (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    fulltext TEXT,
                    mediapath VARCHAR(500),
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    av_text_id INTEGER,
                    risession INTEGER,
                    source_type VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'imported',
                    file_size INTEGER DEFAULT 0,
                    origin VARCHAR(255),
                    folder_id INTEGER
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_cat (
                    catid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    supercatid INTEGER
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_name (
                    cid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(7) NOT NULL DEFAULT '#999999',
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    catid INTEGER
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE code_text (
                    ctid INTEGER PRIMARY KEY,
                    cid INTEGER NOT NULL,
                    fid INTEGER NOT NULL,
                    pos0 INTEGER NOT NULL,
                    pos1 INTEGER NOT NULL,
                    seltext TEXT NOT NULL,
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    important INTEGER DEFAULT 0
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE cases (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    memo TEXT,
                    owner VARCHAR(100),
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE case_attribute (
                    id INTEGER PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    attr_type VARCHAR(20) NOT NULL,
                    value_text TEXT,
                    value_number INTEGER,
                    value_date DATETIME
                )
            """)
        )
        conn.execute(
            text("""
                CREATE TABLE case_source (
                    id INTEGER PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    owner VARCHAR(100),
                    date VARCHAR(50)
                )
            """)
        )

        # Insert sample data
        conn.execute(
            text(
                "INSERT INTO project_settings (key, value) VALUES "
                "('project_name', 'Test Project')"
            )
        )
        conn.execute(text("INSERT INTO folder (id, name) VALUES (1, 'Documents')"))
        conn.execute(
            text(
                "INSERT INTO source (id, name, source_type, folder_id) VALUES "
                "(1, 'interview1.txt', 'text', 1), "
                "(2, 'interview2.txt', 'text', 1)"
            )
        )
        conn.execute(text("INSERT INTO code_cat (catid, name) VALUES (1, 'Themes')"))
        conn.execute(
            text(
                "INSERT INTO code_name (cid, name, color, catid) VALUES "
                "(1, 'Important', '#FF0000', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO code_text (ctid, cid, fid, pos0, pos1, seltext) VALUES "
                "(1, 1, 1, 0, 10, 'test text')"
            )
        )
        conn.execute(text("INSERT INTO cases (id, name) VALUES (1, 'Participant A')"))
        conn.execute(
            text(
                "INSERT INTO case_attribute (id, case_id, name, attr_type, value_text) "
                "VALUES (1, 1, 'Age', 'text', '30')"
            )
        )
        conn.execute(
            text("INSERT INTO case_source (id, case_id, source_id) VALUES (1, 1, 1)")
        )
        conn.commit()

    yield engine
    engine.dispose()


class TestV2SchemaIsolationMigration:
    """Tests for V2 schema isolation migration."""

    def test_migration_properties(self):
        """Migration should have correct version properties."""
        migration = V2SchemaIsolationMigration()

        assert migration.from_version == SchemaVersion.V1
        assert migration.to_version == SchemaVersion.V2
        assert "bounded context" in migration.description.lower()

    def test_pre_check_passes(self, v1_database_with_data):
        """Pre-check should pass for valid V1 database."""
        migration = V2SchemaIsolationMigration()

        with v1_database_with_data.connect() as conn:
            assert migration.pre_check(conn) is True

    def test_pre_check_fails_missing_tables(self):
        """Pre-check should fail if required tables are missing."""
        engine = create_engine("sqlite:///:memory:")
        migration = V2SchemaIsolationMigration()

        with engine.connect() as conn:
            assert migration.pre_check(conn) is False

        engine.dispose()

    def test_upgrade_creates_prefixed_tables(self, v1_database_with_data):
        """Upgrade should create new prefixed tables."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            runner.migrate(conn)

            inspector = inspect(v1_database_with_data)
            tables = set(inspector.get_table_names())

            # Check new tables exist
            assert "src_source" in tables
            assert "src_folder" in tables
            assert "cod_code" in tables
            assert "cod_category" in tables
            assert "cod_segment" in tables
            assert "cas_case" in tables
            assert "cas_attribute" in tables
            assert "cas_source_link" in tables
            assert "prj_settings" in tables

    def test_upgrade_removes_old_tables(self, v1_database_with_data):
        """Upgrade should remove original unprefixed tables."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            runner.migrate(conn)

            inspector = inspect(v1_database_with_data)
            tables = set(inspector.get_table_names())

            # Old tables should be gone (replaced by views)
            # Note: SQLite reports views separately from tables
            # so we check that they're not in the tables list
            assert (
                "code_text" not in tables or "code_text" in inspector.get_view_names()
            )

    def test_upgrade_creates_compatibility_views(self, v1_database_with_data):
        """Upgrade should create compatibility views with old names."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            runner.migrate(conn)

            # Query through compatibility views should work
            result = conn.execute(text("SELECT * FROM source")).fetchall()
            assert len(result) == 2

            result = conn.execute(text("SELECT * FROM code_text")).fetchall()
            assert len(result) == 1

    def test_upgrade_migrates_data(self, v1_database_with_data):
        """Upgrade should migrate all data to new tables."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            runner.migrate(conn)

            # Check data in new tables
            sources = conn.execute(text("SELECT * FROM src_source")).fetchall()
            assert len(sources) == 2
            assert sources[0][1] == "interview1.txt"

            codes = conn.execute(text("SELECT * FROM cod_code")).fetchall()
            assert len(codes) == 1
            assert codes[0][1] == "Important"

            segments = conn.execute(text("SELECT * FROM cod_segment")).fetchall()
            assert len(segments) == 1

            settings = conn.execute(text("SELECT * FROM prj_settings")).fetchall()
            assert len(settings) >= 1

    def test_upgrade_populates_denormalized_names(self, v1_database_with_data):
        """Upgrade should populate denormalized source_name columns."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            runner.migrate(conn)

            # Check cod_segment.source_name
            result = conn.execute(
                text("SELECT source_name FROM cod_segment WHERE ctid = 1")
            ).fetchone()
            assert result[0] == "interview1.txt"

            # Check cas_source_link.source_name
            result = conn.execute(
                text("SELECT source_name FROM cas_source_link WHERE id = 1")
            ).fetchone()
            assert result[0] == "interview1.txt"

    def test_downgrade_restores_original_tables(self, v1_database_with_data):
        """Downgrade should restore original table structure."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            # Upgrade first
            runner.migrate(conn)

            # Then rollback
            runner.rollback(conn, SchemaVersion.V1)

            inspector = inspect(v1_database_with_data)
            tables = set(inspector.get_table_names())

            # Original tables should be back
            assert "source" in tables
            assert "code_text" in tables
            assert "code_name" in tables
            assert "code_cat" in tables

    def test_downgrade_preserves_data(self, v1_database_with_data):
        """Downgrade should preserve all data."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            # Upgrade then rollback
            runner.migrate(conn)
            runner.rollback(conn, SchemaVersion.V1)

            # Check data is preserved
            sources = conn.execute(text("SELECT * FROM source")).fetchall()
            assert len(sources) == 2

            codes = conn.execute(text("SELECT * FROM code_name")).fetchall()
            assert len(codes) == 1

    def test_version_tracking(self, v1_database_with_data):
        """Version should be properly tracked after migration."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            assert runner.get_current_version(conn) == SchemaVersion.V1

            runner.migrate(conn)
            assert runner.get_current_version(conn) == SchemaVersion.V2

            runner.rollback(conn, SchemaVersion.V1)
            assert runner.get_current_version(conn) == SchemaVersion.V1

    def test_idempotent_upgrade(self, v1_database_with_data):
        """Running migrate twice should be safe."""
        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with v1_database_with_data.connect() as conn:
            result1 = runner.migrate(conn)
            result2 = runner.migrate(conn)

            assert result1.success is True
            assert result2.success is True
            assert "Already at target version" in result2.message


class TestMigrationWithMissingOptionalTables:
    """Test migration handles missing optional tables gracefully."""

    def test_migration_without_folder_table(self):
        """Migration should work even if folder table doesn't exist."""
        engine = create_engine("sqlite:///:memory:")

        with engine.connect() as conn:
            # Create V1 schema without folder
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
                        name VARCHAR(255) NOT NULL,
                        fulltext TEXT,
                        mediapath VARCHAR(500),
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        av_text_id INTEGER,
                        risession INTEGER,
                        source_type VARCHAR(20),
                        status VARCHAR(20) DEFAULT 'imported',
                        file_size INTEGER DEFAULT 0,
                        origin VARCHAR(255),
                        folder_id INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_cat (
                        catid INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        supercatid INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_name (
                        cid INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        color VARCHAR(7) DEFAULT '#999999',
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        catid INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_text (
                        ctid INTEGER PRIMARY KEY,
                        cid INTEGER NOT NULL,
                        fid INTEGER NOT NULL,
                        pos0 INTEGER NOT NULL,
                        pos1 INTEGER NOT NULL,
                        seltext TEXT NOT NULL,
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        important INTEGER DEFAULT 0
                    )
                """)
            )
            conn.commit()

        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with engine.connect() as conn:
            result = runner.migrate(conn)
            assert result.success is True

        engine.dispose()

    def test_migration_without_cases_tables(self):
        """Migration should work even if cases tables don't exist."""
        engine = create_engine("sqlite:///:memory:")

        with engine.connect() as conn:
            # Create V1 schema without cases
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
                        name VARCHAR(255) NOT NULL,
                        fulltext TEXT,
                        mediapath VARCHAR(500),
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        av_text_id INTEGER,
                        risession INTEGER,
                        source_type VARCHAR(20),
                        status VARCHAR(20) DEFAULT 'imported',
                        file_size INTEGER DEFAULT 0,
                        origin VARCHAR(255),
                        folder_id INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_cat (
                        catid INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        supercatid INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_name (
                        cid INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        color VARCHAR(7) DEFAULT '#999999',
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        catid INTEGER
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE code_text (
                        ctid INTEGER PRIMARY KEY,
                        cid INTEGER NOT NULL,
                        fid INTEGER NOT NULL,
                        pos0 INTEGER NOT NULL,
                        pos1 INTEGER NOT NULL,
                        seltext TEXT NOT NULL,
                        memo TEXT,
                        owner VARCHAR(100),
                        date VARCHAR(50),
                        important INTEGER DEFAULT 0
                    )
                """)
            )
            conn.commit()

        runner = MigrationRunner([V2SchemaIsolationMigration()])

        with engine.connect() as conn:
            result = runner.migrate(conn)
            assert result.success is True

        engine.dispose()
