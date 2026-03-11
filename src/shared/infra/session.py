"""
Session - Project-scoped database session.

Provides thread-local connections via SingletonThreadPool.
Owns the commit — repos never commit, command handlers do.

Replaces ThreadSafeConnectionProxy and UnitOfWork with a single,
simpler abstraction.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection, Engine

logger = logging.getLogger(__name__)


class Session:
    """
    Project-scoped database session.

    Each thread gets its own connection (thread-local storage).
    Command handlers call session.commit() to persist changes.
    Repos never commit — they only execute.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._local = threading.local()

    @property
    def engine(self) -> Engine:
        """The underlying SQLAlchemy engine."""
        return self._engine

    @property
    def connection(self) -> Connection:
        """Thread-local connection. Same thread always gets the same one."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            from sqlalchemy import text

            conn = self._engine.connect()
            conn.execute(text("PRAGMA busy_timeout = 5000"))
            self._local.conn = conn
        return conn

    def commit(self) -> None:
        """Commit the current transaction. Called by command handlers."""
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.connection.rollback()

    def close(self) -> None:
        """Close all connections and dispose the engine."""
        self._engine.dispose()
