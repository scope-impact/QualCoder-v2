"""
Sync ID Mapping between local SQLite integer PKs and Convex document IDs.

SQLite uses integer primary keys (e.g., CodeId(42)), while Convex uses
string document IDs (e.g., "jd7a3k..."). This module provides bidirectional
mapping between the two, plus FK dependency metadata for translating
foreign key references during outbound sync.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = logging.getLogger(__name__)

# Foreign key dependencies: which fields in each entity type reference other entity types.
# Used by SyncEngine._translate_fk_ids() to convert local integer FKs to Convex document IDs.
FK_DEPENDENCIES: dict[str, dict[str, str]] = {
    "code": {"catid": "category"},
    "segment": {"cid": "code", "fid": "source"},
    "source": {"folder_id": "folder"},
    "folder": {"parent_id": "folder"},
    "category": {"supercatid": "category"},
    "attribute": {"caseId": "case"},
    "source_link": {"caseId": "case", "sourceId": "source"},
}


class SyncIdMap:
    """
    Bidirectional mapping between local SQLite IDs and Convex document IDs.

    Backed by a SQLite table for persistence across sessions, with
    in-memory caches for fast lookups during sync operations.
    """

    def __init__(self, connection: Connection, lock: threading.Lock) -> None:
        self._conn = connection
        self._lock = lock

        # In-memory caches: (entity_type, local_id) -> convex_id and reverse
        self._local_to_convex: dict[tuple[str, str], str] = {}
        self._convex_to_local: dict[tuple[str, str], str] = {}

        self._ensure_table()
        self._load_cache()

    def _ensure_table(self) -> None:
        """Create the sync_id_map table if it doesn't exist."""

        with self._lock:
            self._conn.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS sync_id_map (
                        entity_type TEXT NOT NULL,
                        local_id TEXT NOT NULL,
                        convex_id TEXT NOT NULL,
                        PRIMARY KEY (entity_type, local_id)
                    )
                """)
            )
            self._conn.execute(
                text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_id_map_convex
                    ON sync_id_map (entity_type, convex_id)
                """)
            )
            self._conn.commit()

    def _load_cache(self) -> None:
        """Load all mappings into memory."""

        with self._lock:
            rows = self._conn.execute(
                text("SELECT entity_type, local_id, convex_id FROM sync_id_map")
            ).fetchall()
            # Release SHARED lock so the main connection can write
            self._conn.commit()

        for entity_type, local_id, convex_id in rows:
            self._local_to_convex[(entity_type, local_id)] = convex_id
            self._convex_to_local[(entity_type, convex_id)] = local_id

        if rows:
            logger.debug(f"Loaded {len(rows)} ID mappings from database")

    def put(self, entity_type: str, local_id: str, convex_id: str) -> None:
        """Store a mapping between local and Convex IDs."""

        key_local = (entity_type, local_id)
        key_convex = (entity_type, convex_id)

        # Update in-memory cache
        self._local_to_convex[key_local] = convex_id
        self._convex_to_local[key_convex] = local_id

        # Persist to SQLite
        with self._lock:
            self._conn.execute(
                text("""
                    INSERT OR REPLACE INTO sync_id_map (entity_type, local_id, convex_id)
                    VALUES (:entity_type, :local_id, :convex_id)
                """),
                {
                    "entity_type": entity_type,
                    "local_id": local_id,
                    "convex_id": convex_id,
                },
            )
            self._conn.commit()

    def get_convex_id(self, entity_type: str, local_id: str) -> str | None:
        """Look up the Convex document ID for a local SQLite ID."""
        return self._local_to_convex.get((entity_type, local_id))

    def get_local_id(self, entity_type: str, convex_id: str) -> str | None:
        """Look up the local SQLite ID for a Convex document ID."""
        return self._convex_to_local.get((entity_type, convex_id))

    def has_mapping(self, entity_type: str, local_id: str) -> bool:
        """Check if a mapping exists for the given local ID."""
        return (entity_type, local_id) in self._local_to_convex

    def remove(self, entity_type: str, local_id: str) -> None:
        """Remove a mapping by local ID."""

        key_local = (entity_type, local_id)
        convex_id = self._local_to_convex.pop(key_local, None)
        if convex_id:
            self._convex_to_local.pop((entity_type, convex_id), None)

        with self._lock:
            self._conn.execute(
                text(
                    "DELETE FROM sync_id_map WHERE entity_type = :entity_type AND local_id = :local_id"
                ),
                {"entity_type": entity_type, "local_id": local_id},
            )
            self._conn.commit()
