"""
Transactional Outbox Writer for SQLite-Convex sync.

Writes domain events atomically to the sync_outbox table using the same
SQLAlchemy connection (and therefore the same transaction) as the domain
write. The SyncEngine drains the outbox in a background thread.

Key invariant: OutboxWriter NEVER calls conn.commit(). The owning
repository is responsible for the commit, ensuring domain write +
outbox write are one atomic transaction.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from src.shared.common.uuid7 import new_uuid7

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = logging.getLogger(__name__)

_OUTBOX_SQL = text("""
    INSERT INTO sync_outbox (id, entity_type, entity_id, operation, data, created_at)
    VALUES (:id, :entity_type, :entity_id, :operation, :data, :created_at)
    ON CONFLICT(entity_type, entity_id)
    DO UPDATE SET operation=excluded.operation, data=excluded.data, created_at=excluded.created_at
""")


class OutboxWriter:
    """
    Writes pending sync operations to the sync_outbox table.

    Uses the main domain connection so that outbox writes are part of the
    same SQLite transaction as the domain write. The SyncEngine drains the
    outbox asynchronously from a background thread via a separate connection.
    """

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def write_upsert(
        self, entity_type: str, entity_id: str, data: dict[str, Any]
    ) -> None:
        """
        Record an upsert (create/update) in the outbox.

        Uses INSERT OR REPLACE so a later upsert overwrites an earlier pending
        one for the same entity.  Does NOT commit -- caller is responsible.
        """
        self._write(entity_type, entity_id, "upsert", json.dumps(data))

    def write_delete(self, entity_type: str, entity_id: str) -> None:
        """
        Record a delete in the outbox.

        Does NOT commit -- caller is responsible.
        """
        self._write(entity_type, entity_id, "delete", None)

    def _write(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        data: str | None,
    ) -> None:
        """Execute the outbox INSERT ... ON CONFLICT statement."""
        try:
            self._conn.execute(
                _OUTBOX_SQL,
                {
                    "id": new_uuid7(),
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "operation": operation,
                    "data": data,
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as e:
            logger.warning(f"OutboxWriter._write failed ({operation}): {e}")
