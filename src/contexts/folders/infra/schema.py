"""
Folders Context: SQLAlchemy Core Schema

Table definition for the src_folder table.
Uses the 'src_' prefix for backward compatibility with the Sources context.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
)

# Metadata for Folders context tables
metadata = MetaData()

# src_folder - Hierarchical folder organization for sources
src_folder = Table(
    "src_folder",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("parent_id", Integer),  # Self-referential for hierarchy
    Column("created_at", DateTime),
    Index("idx_src_folder_parent", "parent_id"),
)


def create_all(engine) -> None:
    """Create all tables for the Folders context."""
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """Drop all Folders context tables (for testing)."""
    metadata.drop_all(engine)
