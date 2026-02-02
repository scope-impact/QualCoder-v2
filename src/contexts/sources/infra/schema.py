"""
Sources Context: SQLAlchemy Core Schema

Table definitions for the Sources bounded context using SQLAlchemy Core.
Defines src_source and src_folder tables.

These tables use the 'src_' prefix to identify them as belonging to
the Sources bounded context.
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

# Metadata for Sources context tables
metadata = MetaData()

# ============================================================
# Table Definitions
# ============================================================

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

# src_source - Imported source files
src_source = Table(
    "src_source",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("fulltext", Text),  # Content for text sources
    Column("mediapath", String(500)),  # Path to media file
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column("av_text_id", Integer),  # For A/V transcripts
    Column("risession", Integer),  # For external links
    Column("source_type", String(20)),  # text, audio, video, image, pdf
    Column("status", String(20), default="imported"),
    Column("file_size", Integer, default=0),
    Column("origin", String(255)),  # Where the source came from
    Column("folder_id", Integer),  # Reference to src_folder
    # Indexes
    Index("idx_src_source_name", "name"),
    Index("idx_src_source_type", "source_type"),
    Index("idx_src_source_folder", "folder_id"),
)


def create_all(engine) -> None:
    """
    Create all tables for the Sources context.

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Sources context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)
