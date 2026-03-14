"""
Storage Context: SQLAlchemy Core Schema

Table definitions for the Storage bounded context using SQLAlchemy Core.
Defines the stg_data_store table.

Tables use the 'stg_' prefix to identify them as belonging to
the Storage bounded context.
"""

from sqlalchemy import Column, DateTime, MetaData, String, Table

# Metadata for Storage context tables
metadata = MetaData()

# stg_data_store - S3 data store configuration (singleton per project)
stg_data_store = Table(
    "stg_data_store",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("bucket_name", String(255), nullable=False),
    Column("region", String(50), nullable=False),
    Column("prefix", String(500), default=""),
    Column("dvc_remote_name", String(100), default="origin"),
    Column("created_at", DateTime),
)


def create_all(engine) -> None:
    """Create all tables for the Storage context."""
    metadata.create_all(engine)


def drop_all(engine) -> None:
    """Drop all Storage context tables (for testing)."""
    metadata.drop_all(engine)
