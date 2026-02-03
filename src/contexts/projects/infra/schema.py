"""
Projects Context: SQLAlchemy Core Schema

Table definitions for the Projects bounded context using SQLAlchemy Core.
Uses 'prj_' prefix for bounded context isolation.

Note: Source/folder tables are now in Sources context (src/contexts/sources/infra/schema.py)
      Cases tables are now in Cases context (src/contexts/cases/infra/schema.py)
"""

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
)

# Metadata for Projects context tables
metadata = MetaData()

# ============================================================
# Table Definitions (V2 - Prefixed for bounded context isolation)
# ============================================================

# prj_settings - Project-level settings and metadata
prj_settings = Table(
    "prj_settings",
    metadata,
    Column("key", String(100), primary_key=True),
    Column("value", Text),
    Column("updated_at", DateTime),
)

# Alias used by repositories
project_settings = prj_settings


def create_all(engine) -> None:
    """
    Create all tables for the Projects context (prj_settings only).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Projects context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)


def create_all_contexts(engine) -> None:
    """
    Create all tables for all bounded contexts.

    This is the main entry point for database initialization when
    creating a new project. It creates tables for all contexts:
    - Projects (prj_settings)
    - Sources (src_source, src_folder)
    - Coding (cod_category, cod_code, cod_segment)
    - Cases (cas_case, cas_attribute, cas_source_link)

    Args:
        engine: SQLAlchemy engine instance
    """
    from src.contexts.cases.infra import schema as cases_schema
    from src.contexts.coding.infra import schema as coding_schema
    from src.contexts.sources.infra import schema as sources_schema

    # Create tables in dependency order
    metadata.create_all(engine)  # Projects context
    sources_schema.metadata.create_all(engine)  # Sources context
    coding_schema.metadata.create_all(engine)  # Coding context
    cases_schema.metadata.create_all(engine)  # Cases context


def drop_all_contexts(engine) -> None:
    """
    Drop all tables for all bounded contexts (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    from src.contexts.cases.infra import schema as cases_schema
    from src.contexts.coding.infra import schema as coding_schema
    from src.contexts.sources.infra import schema as sources_schema

    # Drop in reverse order of dependencies
    cases_schema.metadata.drop_all(engine)
    coding_schema.metadata.drop_all(engine)
    sources_schema.metadata.drop_all(engine)
    metadata.drop_all(engine)
