"""
Store Repository - SQLAlchemy Core Implementation for Storage Context.

Implements the repository for DataStore configuration using the stg_data_store table.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select

from src.contexts.storage.core.entities import DataStore, StoreId
from src.contexts.storage.infra.schema import stg_data_store

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = logging.getLogger("qualcoder.storage.infra")


class SQLiteStoreRepository:
    """
    SQLAlchemy Core implementation of StoreRepository.

    Maps between domain DataStore entities and the stg_data_store table.
    Singleton pattern: only one store config per project.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get(self) -> DataStore | None:
        """Get the current data store configuration (singleton)."""
        stmt = select(stg_data_store).limit(1)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def save(self, store: DataStore) -> None:
        """Save the data store configuration (insert or replace)."""
        logger.debug("save: %s (bucket=%s)", store.id.value, store.bucket_name)

        # Delete existing config (singleton — only one store per project)
        self._conn.execute(delete(stg_data_store))

        # Insert new config
        stmt = stg_data_store.insert().values(
            id=store.id.value,
            bucket_name=store.bucket_name,
            region=store.region,
            prefix=store.prefix,
            dvc_remote_name=store.dvc_remote_name,
            created_at=store.created_at,
        )
        self._conn.execute(stmt)

    def exists(self) -> bool:
        """Check if a store configuration exists."""
        stmt = select(func.count()).select_from(stg_data_store)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def _row_to_entity(self, row) -> DataStore:
        """Map database row to domain DataStore entity."""
        return DataStore(
            id=StoreId(value=row.id),
            bucket_name=row.bucket_name,
            region=row.region,
            prefix=row.prefix or "",
            dvc_remote_name=row.dvc_remote_name or "origin",
            created_at=row.created_at,
        )
