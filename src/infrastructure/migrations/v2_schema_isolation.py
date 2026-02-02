"""
V2 Schema Isolation Migration.

Migrates from V1 (mixed context tables) to V2 (isolated bounded contexts):
- Renames tables with context prefixes (src_, cod_, cas_, prj_)
- Creates compatibility views with original names
- Adds denormalized source_name columns for cross-context display

This migration ensures:
1. Existing code continues to work via compatibility views
2. New code can use prefixed table names
3. Cross-context queries don't need JOINs for display names
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from src.infrastructure.migrations.framework import (
    Migration,
    MigrationError,
    SchemaVersion,
)

if TYPE_CHECKING:
    from sqlalchemy import Connection


class V2SchemaIsolationMigration(Migration):
    """
    Migrate to V2 schema with bounded context isolation.

    Table renames:
    - source -> src_source
    - folder -> src_folder
    - code_name -> cod_code
    - code_cat -> cod_category
    - code_text -> cod_segment
    - cases -> cas_case
    - case_attribute -> cas_attribute
    - case_source -> cas_source_link
    - project_settings -> prj_settings

    New columns:
    - cod_segment.source_name (denormalized)
    - cas_source_link.source_name (denormalized)
    """

    @property
    def from_version(self) -> SchemaVersion:
        return SchemaVersion.V1

    @property
    def to_version(self) -> SchemaVersion:
        return SchemaVersion.V2

    @property
    def description(self) -> str:
        return "Isolate schemas by bounded context with table prefixes"

    def pre_check(self, conn: Connection) -> bool:
        """Verify required tables exist for migration."""
        required_tables = ["source", "code_name", "code_cat", "code_text"]
        for table in required_tables:
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
                ).bindparams(name=table)
            )
            if not result.fetchone():
                return False
        return True

    def upgrade(self, conn: Connection) -> None:
        """Apply the V2 schema isolation migration."""
        try:
            # Phase 1: Create new tables with prefixes
            self._create_sources_tables(conn)
            self._create_coding_tables(conn)
            self._create_cases_tables(conn)
            self._create_projects_tables(conn)

            # Phase 2: Migrate data
            self._migrate_sources_data(conn)
            self._migrate_coding_data(conn)
            self._migrate_cases_data(conn)
            self._migrate_projects_data(conn)

            # Phase 3: Populate denormalized source_name columns
            self._populate_denormalized_names(conn)

            # Phase 4: Drop old tables
            self._drop_old_tables(conn)

            # Phase 5: Create compatibility views
            self._create_compatibility_views(conn)

        except Exception as e:
            raise MigrationError(f"V2 migration upgrade failed: {e}") from e

    def downgrade(self, conn: Connection) -> None:
        """Roll back to V1 schema."""
        try:
            # Phase 1: Drop compatibility views
            self._drop_compatibility_views(conn)

            # Phase 2: Recreate original tables
            self._create_original_tables(conn)

            # Phase 3: Migrate data back
            self._migrate_data_back(conn)

            # Phase 4: Drop prefixed tables
            self._drop_prefixed_tables(conn)

        except Exception as e:
            raise MigrationError(f"V2 migration downgrade failed: {e}") from e

    # =========================================================================
    # UPGRADE: Create new prefixed tables
    # =========================================================================

    def _create_sources_tables(self, conn: Connection) -> None:
        """Create src_* tables for Sources context."""
        # src_folder
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS src_folder (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    parent_id INTEGER,
                    created_at DATETIME
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_src_folder_parent ON src_folder(parent_id)"
            )
        )

        # src_source
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS src_source (
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
                    folder_id INTEGER REFERENCES src_folder(id)
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_src_source_name ON src_source(name)")
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_src_source_type ON src_source(source_type)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_src_source_folder ON src_source(folder_id)"
            )
        )

    def _create_coding_tables(self, conn: Connection) -> None:
        """Create cod_* tables for Coding context."""
        # cod_category (was code_cat)
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cod_category (
                    catid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    supercatid INTEGER REFERENCES cod_category(catid) ON DELETE SET NULL
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_cod_category_super ON cod_category(supercatid)"
            )
        )

        # cod_code (was code_name)
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cod_code (
                    cid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(7) NOT NULL DEFAULT '#999999',
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    catid INTEGER REFERENCES cod_category(catid) ON DELETE SET NULL
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_cod_code_catid ON cod_code(catid)")
        )

        # cod_segment (was code_text) - with denormalized source_name
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cod_segment (
                    ctid INTEGER PRIMARY KEY,
                    cid INTEGER NOT NULL REFERENCES cod_code(cid) ON DELETE CASCADE,
                    fid INTEGER NOT NULL,
                    pos0 INTEGER NOT NULL,
                    pos1 INTEGER NOT NULL,
                    seltext TEXT NOT NULL,
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    important INTEGER DEFAULT 0,
                    source_name VARCHAR(255)
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_cod_segment_cid ON cod_segment(cid)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_cod_segment_fid ON cod_segment(fid)")
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_cod_segment_fid_cid ON cod_segment(fid, cid)"
            )
        )

    def _create_cases_tables(self, conn: Connection) -> None:
        """Create cas_* tables for Cases context."""
        # cas_case (was cases)
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cas_case (
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
            text("CREATE INDEX IF NOT EXISTS idx_cas_case_name ON cas_case(name)")
        )

        # cas_attribute (was case_attribute)
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cas_attribute (
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
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cas_attribute_case_name "
                "ON cas_attribute(case_id, name)"
            )
        )

        # cas_source_link (was case_source) - with denormalized source_name
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cas_source_link (
                    id INTEGER PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    source_name VARCHAR(255)
                )
            """)
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_cas_source_link_unique "
                "ON cas_source_link(case_id, source_id)"
            )
        )

    def _create_projects_tables(self, conn: Connection) -> None:
        """Create prj_* tables for Projects context."""
        # prj_settings (was project_settings)
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS prj_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """)
        )

    # =========================================================================
    # UPGRADE: Migrate data to new tables
    # =========================================================================

    def _migrate_sources_data(self, conn: Connection) -> None:
        """Migrate data to src_* tables."""
        # Check if folder table exists (v2 addition)
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='folder'")
        )
        if result.fetchone():
            conn.execute(
                text("""
                    INSERT INTO src_folder (id, name, parent_id, created_at)
                    SELECT id, name, parent_id, created_at FROM folder
                """)
            )

        conn.execute(
            text("""
                INSERT INTO src_source (
                    id, name, fulltext, mediapath, memo, owner, date,
                    av_text_id, risession, source_type, status, file_size,
                    origin, folder_id
                )
                SELECT
                    id, name, fulltext, mediapath, memo, owner, date,
                    av_text_id, risession, source_type, status, file_size,
                    origin, folder_id
                FROM source
            """)
        )

    def _migrate_coding_data(self, conn: Connection) -> None:
        """Migrate data to cod_* tables."""
        conn.execute(
            text("""
                INSERT INTO cod_category (catid, name, memo, owner, date, supercatid)
                SELECT catid, name, memo, owner, date, supercatid FROM code_cat
            """)
        )

        conn.execute(
            text("""
                INSERT INTO cod_code (cid, name, color, memo, owner, date, catid)
                SELECT cid, name, color, memo, owner, date, catid FROM code_name
            """)
        )

        # Note: source_name will be populated in _populate_denormalized_names
        conn.execute(
            text("""
                INSERT INTO cod_segment (
                    ctid, cid, fid, pos0, pos1, seltext, memo, owner, date, important
                )
                SELECT ctid, cid, fid, pos0, pos1, seltext, memo, owner, date, important
                FROM code_text
            """)
        )

    def _migrate_cases_data(self, conn: Connection) -> None:
        """Migrate data to cas_* tables."""
        # Check if cases table exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
        )
        if result.fetchone():
            conn.execute(
                text("""
                    INSERT INTO cas_case (
                        id, name, description, memo, owner, created_at, updated_at
                    )
                    SELECT id, name, description, memo, owner, created_at, updated_at
                    FROM cases
                """)
            )

        # Check if case_attribute table exists
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='case_attribute'"
            )
        )
        if result.fetchone():
            conn.execute(
                text("""
                    INSERT INTO cas_attribute (
                        id, case_id, name, attr_type, value_text, value_number, value_date
                    )
                    SELECT id, case_id, name, attr_type, value_text, value_number, value_date
                    FROM case_attribute
                """)
            )

        # Check if case_source table exists
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='case_source'"
            )
        )
        if result.fetchone():
            # Note: source_name will be populated in _populate_denormalized_names
            conn.execute(
                text("""
                    INSERT INTO cas_source_link (id, case_id, source_id, owner, date)
                    SELECT id, case_id, source_id, owner, date FROM case_source
                """)
            )

    def _migrate_projects_data(self, conn: Connection) -> None:
        """Migrate data to prj_* tables."""
        conn.execute(
            text("""
                INSERT INTO prj_settings (key, value, updated_at)
                SELECT key, value, updated_at FROM project_settings
            """)
        )

    # =========================================================================
    # UPGRADE: Populate denormalized columns
    # =========================================================================

    def _populate_denormalized_names(self, conn: Connection) -> None:
        """Populate source_name columns from src_source."""
        # Update cod_segment.source_name
        conn.execute(
            text("""
                UPDATE cod_segment
                SET source_name = (
                    SELECT name FROM src_source WHERE src_source.id = cod_segment.fid
                )
            """)
        )

        # Update cas_source_link.source_name
        conn.execute(
            text("""
                UPDATE cas_source_link
                SET source_name = (
                    SELECT name FROM src_source WHERE src_source.id = cas_source_link.source_id
                )
            """)
        )

    # =========================================================================
    # UPGRADE: Drop old tables
    # =========================================================================

    def _drop_old_tables(self, conn: Connection) -> None:
        """Drop original V1 tables after data migration."""
        # Order matters due to foreign key constraints
        tables_to_drop = [
            "code_text",
            "code_name",
            "code_cat",
            "case_source",
            "case_attribute",
            "cases",
            "source",
            "folder",
            "project_settings",
        ]
        for table in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))

    # =========================================================================
    # UPGRADE: Create compatibility views
    # =========================================================================

    def _create_compatibility_views(self, conn: Connection) -> None:
        """Create views with original table names for backward compatibility."""
        # source -> src_source
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS source AS
                SELECT id, name, fulltext, mediapath, memo, owner, date,
                       av_text_id, risession, source_type, status, file_size,
                       origin, folder_id
                FROM src_source
            """)
        )

        # folder -> src_folder
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS folder AS
                SELECT id, name, parent_id, created_at
                FROM src_folder
            """)
        )

        # code_cat -> cod_category
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS code_cat AS
                SELECT catid, name, memo, owner, date, supercatid
                FROM cod_category
            """)
        )

        # code_name -> cod_code
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS code_name AS
                SELECT cid, name, color, memo, owner, date, catid
                FROM cod_code
            """)
        )

        # code_text -> cod_segment (excluding new columns)
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS code_text AS
                SELECT ctid, cid, fid, pos0, pos1, seltext, memo, owner, date, important
                FROM cod_segment
            """)
        )

        # cases -> cas_case
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS cases AS
                SELECT id, name, description, memo, owner, created_at, updated_at
                FROM cas_case
            """)
        )

        # case_attribute -> cas_attribute
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS case_attribute AS
                SELECT id, case_id, name, attr_type, value_text, value_number, value_date
                FROM cas_attribute
            """)
        )

        # case_source -> cas_source_link (excluding new columns)
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS case_source AS
                SELECT id, case_id, source_id, owner, date
                FROM cas_source_link
            """)
        )

        # project_settings -> prj_settings
        conn.execute(
            text("""
                CREATE VIEW IF NOT EXISTS project_settings AS
                SELECT key, value, updated_at
                FROM prj_settings
            """)
        )

    # =========================================================================
    # DOWNGRADE: Helpers
    # =========================================================================

    def _drop_compatibility_views(self, conn: Connection) -> None:
        """Drop compatibility views."""
        views = [
            "source",
            "folder",
            "code_cat",
            "code_name",
            "code_text",
            "cases",
            "case_attribute",
            "case_source",
            "project_settings",
        ]
        for view in views:
            conn.execute(text(f"DROP VIEW IF EXISTS {view}"))

    def _create_original_tables(self, conn: Connection) -> None:
        """Recreate original V1 tables for rollback."""
        # folder table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS folder (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    parent_id INTEGER,
                    created_at DATETIME
                )
            """)
        )

        # source table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS source (
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

        # code_cat table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS code_cat (
                    catid INTEGER PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    memo TEXT,
                    owner VARCHAR(100),
                    date VARCHAR(50),
                    supercatid INTEGER
                )
            """)
        )

        # code_name table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS code_name (
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

        # code_text table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS code_text (
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

        # cases table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS cases (
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

        # case_attribute table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS case_attribute (
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

        # case_source table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS case_source (
                    id INTEGER PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    source_id INTEGER NOT NULL,
                    owner VARCHAR(100),
                    date VARCHAR(50)
                )
            """)
        )

        # project_settings table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS project_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """)
        )

    def _migrate_data_back(self, conn: Connection) -> None:
        """Migrate data back from prefixed tables to original tables."""
        # folder
        conn.execute(
            text("""
                INSERT INTO folder (id, name, parent_id, created_at)
                SELECT id, name, parent_id, created_at FROM src_folder
            """)
        )

        # source
        conn.execute(
            text("""
                INSERT INTO source (
                    id, name, fulltext, mediapath, memo, owner, date,
                    av_text_id, risession, source_type, status, file_size,
                    origin, folder_id
                )
                SELECT
                    id, name, fulltext, mediapath, memo, owner, date,
                    av_text_id, risession, source_type, status, file_size,
                    origin, folder_id
                FROM src_source
            """)
        )

        # code_cat
        conn.execute(
            text("""
                INSERT INTO code_cat (catid, name, memo, owner, date, supercatid)
                SELECT catid, name, memo, owner, date, supercatid FROM cod_category
            """)
        )

        # code_name
        conn.execute(
            text("""
                INSERT INTO code_name (cid, name, color, memo, owner, date, catid)
                SELECT cid, name, color, memo, owner, date, catid FROM cod_code
            """)
        )

        # code_text (without denormalized column)
        conn.execute(
            text("""
                INSERT INTO code_text (
                    ctid, cid, fid, pos0, pos1, seltext, memo, owner, date, important
                )
                SELECT ctid, cid, fid, pos0, pos1, seltext, memo, owner, date, important
                FROM cod_segment
            """)
        )

        # cases
        conn.execute(
            text("""
                INSERT INTO cases (id, name, description, memo, owner, created_at, updated_at)
                SELECT id, name, description, memo, owner, created_at, updated_at FROM cas_case
            """)
        )

        # case_attribute
        conn.execute(
            text("""
                INSERT INTO case_attribute (
                    id, case_id, name, attr_type, value_text, value_number, value_date
                )
                SELECT id, case_id, name, attr_type, value_text, value_number, value_date
                FROM cas_attribute
            """)
        )

        # case_source (without denormalized column)
        conn.execute(
            text("""
                INSERT INTO case_source (id, case_id, source_id, owner, date)
                SELECT id, case_id, source_id, owner, date FROM cas_source_link
            """)
        )

        # project_settings
        conn.execute(
            text("""
                INSERT INTO project_settings (key, value, updated_at)
                SELECT key, value, updated_at FROM prj_settings
            """)
        )

    def _drop_prefixed_tables(self, conn: Connection) -> None:
        """Drop V2 prefixed tables."""
        tables_to_drop = [
            "cod_segment",
            "cod_code",
            "cod_category",
            "cas_source_link",
            "cas_attribute",
            "cas_case",
            "src_source",
            "src_folder",
            "prj_settings",
        ]
        for table in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
