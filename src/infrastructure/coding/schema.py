"""
Coding Context: SQLAlchemy Core Schema

Table definitions for the Coding bounded context using SQLAlchemy Core.
Compatible with QualCoder's existing schema where applicable.
"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)

# Shared metadata for all Coding context tables
metadata = MetaData()

# ============================================================
# Table Definitions
# ============================================================

code_cat = Table(
    "code_cat",
    metadata,
    Column("catid", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column(
        "supercatid",
        Integer,
        ForeignKey("code_cat.catid", ondelete="SET NULL"),
        nullable=True,
    ),
)

code_name = Table(
    "code_name",
    metadata,
    Column("cid", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
    Column("color", String(7), nullable=False, default="#999999"),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column(
        "catid",
        Integer,
        ForeignKey("code_cat.catid", ondelete="SET NULL"),
        nullable=True,
    ),
)

code_text = Table(
    "code_text",
    metadata,
    Column("ctid", Integer, primary_key=True),
    Column(
        "cid",
        Integer,
        ForeignKey("code_name.cid", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("fid", Integer, nullable=False),  # Foreign key to source table
    Column("pos0", Integer, nullable=False),
    Column("pos1", Integer, nullable=False),
    Column("seltext", Text, nullable=False),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column("important", Integer, default=0),
    # Indexes for common queries
    Index("idx_code_text_cid", "cid"),
    Index("idx_code_text_fid", "fid"),
    Index("idx_code_text_fid_cid", "fid", "cid"),
)

# Additional indexes
Index("idx_code_name_catid", code_name.c.catid)
Index("idx_code_cat_supercatid", code_cat.c.supercatid)


def create_all(engine) -> None:
    """
    Create all tables for the Coding context.

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Coding context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)
