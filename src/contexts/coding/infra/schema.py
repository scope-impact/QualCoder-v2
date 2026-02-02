"""
Coding Context: SQLAlchemy Core Schema

Table definitions for the Coding bounded context using SQLAlchemy Core.
Uses 'cod_' prefix for bounded context isolation.
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
# Table Definitions (V2 - Prefixed for bounded context isolation)
# ============================================================

# cod_category - Code categories (was code_cat)
cod_category = Table(
    "cod_category",
    metadata,
    Column("catid", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column(
        "supercatid",
        Integer,
        ForeignKey("cod_category.catid", ondelete="SET NULL"),
        nullable=True,
    ),
)

# cod_code - Code definitions (was code_name)
cod_code = Table(
    "cod_code",
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
        ForeignKey("cod_category.catid", ondelete="SET NULL"),
        nullable=True,
    ),
)

# cod_segment - Coded text segments (was code_text)
# Includes denormalized source_name for cross-context display
cod_segment = Table(
    "cod_segment",
    metadata,
    Column("ctid", Integer, primary_key=True),
    Column(
        "cid",
        Integer,
        ForeignKey("cod_code.cid", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("fid", Integer, nullable=False),  # References src_source.id
    Column("pos0", Integer, nullable=False),
    Column("pos1", Integer, nullable=False),
    Column("seltext", Text, nullable=False),
    Column("memo", Text),
    Column("owner", String(100)),
    Column("date", String(50)),
    Column("important", Integer, default=0),
    Column("source_name", String(255)),  # Denormalized for display
    # Indexes for common queries
    Index("idx_cod_segment_cid", "cid"),
    Index("idx_cod_segment_fid", "fid"),
    Index("idx_cod_segment_fid_cid", "fid", "cid"),
)

# Additional indexes
Index("idx_cod_code_catid", cod_code.c.catid)
Index("idx_cod_category_supercatid", cod_category.c.supercatid)

# ============================================================
# Compatibility aliases for gradual migration
# ============================================================
# These allow existing code to continue working during transition
code_cat = cod_category
code_name = cod_code
code_text = cod_segment


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
