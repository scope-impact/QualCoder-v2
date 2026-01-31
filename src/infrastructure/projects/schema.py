"""
Project Context: SQLAlchemy Core Schema

Table definitions for the Project bounded context using SQLAlchemy Core.
Compatible with QualCoder's existing source table schema.
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

# Shared metadata for Project context tables
metadata = MetaData()

# ============================================================
# Table Definitions
# ============================================================

# Folder table - organizes sources hierarchically (v2 only)
folder = Table(
    "folder",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("parent_id", Integer),  # Self-referential for hierarchy
    Column("created_at", DateTime),
    Index("idx_folder_parent", "parent_id"),
)

# Source table - stores imported files
# Compatible with QualCoder's source table
source = Table(
    "source",
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
    # Extended columns for v2
    Column("source_type", String(20)),  # text, audio, video, image, pdf
    Column("status", String(20), default="imported"),
    Column("file_size", Integer, default=0),
    Column("origin", String(255)),  # Where the source came from
    Column("folder_id", Integer),  # Reference to folder
    # Indexes
    Index("idx_source_name", "name"),
    Index("idx_source_type", "source_type"),
    Index("idx_source_folder", "folder_id"),
)

# Project settings table (v2 only)
# Stores project-level metadata not in the original schema
project_settings = Table(
    "project_settings",
    metadata,
    Column("key", String(100), primary_key=True),
    Column("value", Text),
    Column("updated_at", DateTime),
)

# Cases table - stores research units (participants, sites, etc.)
cases = Table(
    "cases",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Index("idx_cases_name", "name"),
)

# Case attributes table - stores demographic/categorical data
case_attribute = Table(
    "case_attribute",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("case_id", Integer, nullable=False),
    Column("name", String(100), nullable=False),
    Column("attr_type", String(20), nullable=False),  # text, number, date, boolean
    Column("value_text", Text),
    Column("value_number", Integer),
    Column("value_date", DateTime),
    Index("idx_case_attr", "case_id", "name", unique=True),
)

# Case-Source association table
# Compatible with QualCoder's case_text linkage
case_source = Table(
    "case_source",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("case_id", Integer, nullable=False),
    Column("source_id", Integer, nullable=False),
    Column("owner", String(100)),
    Column("date", String(50)),
    Index("idx_case_source", "case_id", "source_id", unique=True),
)


def create_all(engine) -> None:
    """
    Create all tables for the Project context.

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Project context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)
