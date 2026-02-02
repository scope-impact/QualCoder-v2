"""
Cases Context: SQLAlchemy Core Schema

Table definitions for the Cases bounded context using SQLAlchemy Core.
Defines cas_case, cas_attribute, and cas_source_link tables.

These tables use the 'cas_' prefix to identify them as belonging to
the Cases bounded context.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)

# Metadata for Cases context tables
metadata = MetaData()

# ============================================================
# Table Definitions
# ============================================================

# cas_case - Research units (participants, sites, etc.)
cas_case = Table(
    "cas_case",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Index("idx_cas_case_name", "name"),
)

# cas_attribute - Demographic/categorical data for cases
cas_attribute = Table(
    "cas_attribute",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("case_id", Integer, nullable=False),
    Column("name", String(100), nullable=False),
    Column("attr_type", String(20), nullable=False),  # text, number, date, boolean
    Column("value_text", Text),
    Column("value_number", Integer),
    Column("value_date", DateTime),
    Index("idx_cas_attr_case_name", "case_id", "name", unique=True),
)

# cas_source_link - Case-to-Source associations
# Contains denormalized source_name for cross-context display
cas_source_link = Table(
    "cas_source_link",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("case_id", Integer, nullable=False),
    Column("source_id", Integer, nullable=False),  # References src_source.id
    Column("owner", String(100)),
    Column("date", String(50)),
    Column("source_name", String(255)),  # Denormalized for display
    Index("idx_cas_source_link_unique", "case_id", "source_id", unique=True),
)


def create_all(engine) -> None:
    """
    Create all tables for the Cases context.

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Cases context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)
