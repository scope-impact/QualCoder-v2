"""
Privacy Context: SQLAlchemy Core Schema

Table definitions for the Privacy bounded context using SQLAlchemy Core.
Stores pseudonym mappings and anonymization session data.
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

# Shared metadata for Privacy context tables
metadata = MetaData()

# ============================================================
# Table Definitions
# ============================================================

# Pseudonym table - stores real name to alias mappings
pseudonym = Table(
    "pseudonym",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("real_name", Text, nullable=False),  # The original identifier
    Column("alias", String(255), nullable=False),  # The pseudonym to use
    Column("category", String(50), nullable=False),  # person, organization, etc.
    Column("notes", Text),
    Column("owner", String(100)),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Index("idx_pseudonym_alias", "alias"),
    Index("idx_pseudonym_category", "category"),
)

# Anonymization session - tracks an anonymization operation for undo
anonymization_session = Table(
    "anonymization_session",
    metadata,
    Column("id", String(50), primary_key=True),  # anon_xxxxx format
    Column("source_id", Integer, nullable=False),
    Column("original_text", Text, nullable=False),  # Full original for reversal
    Column("pseudonym_ids_json", Text),  # JSON array of pseudonym IDs used
    Column("created_at", DateTime),
    Column("reverted_at", DateTime),  # NULL if not reverted
    Index("idx_anon_session_source", "source_id"),
)

# Anonymization replacement - records individual replacements
anonymization_replacement = Table(
    "anonymization_replacement",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("session_id", String(50), nullable=False),
    Column("pseudonym_id", Integer, nullable=False),
    Column("original_text", Text, nullable=False),
    Column("replacement_text", Text, nullable=False),
    Column("positions_json", Text, nullable=False),  # JSON array of {start, end}
    Index("idx_anon_repl_session", "session_id"),
)


def create_all(engine) -> None:
    """
    Create all tables for the Privacy context.

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """
    Drop all Privacy context tables (for testing).

    Args:
        engine: SQLAlchemy engine instance
    """
    metadata.drop_all(engine)
