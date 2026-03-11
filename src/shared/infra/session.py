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
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Connection, Engine

logger = logging.getLogger(__name__)

# Default busy_timeout in ms for SQLite connections.
# Shared with ProjectLifecycle._get_or_create_connection.
SQLITE_BUSY_TIMEOUT_MS = 5000


class Session:
    """
    Project-scoped database session.

    Wraps a connection factory that returns thread-local connections.
    Command handlers call session.commit() to persist changes.
    Repos never commit — they only execute.

    The connection factory must return the same connection that repos use
    (i.e., the ThreadSafeConnectionProxy's underlying connection) so that
    session.commit() commits the repos' writes.
    """

    def __init__(
        self,
        engine: Engine,
        connection_factory: Callable[[], Connection] | None = None,
    ) -> None:
        self._engine = engine
        self._connection_factory = connection_factory
        self._local = threading.local()

    @property
    def engine(self) -> Engine:
        """The underlying SQLAlchemy engine."""
        return self._engine

    @property
    def connection(self) -> Connection:
        """Thread-local connection. Same thread always gets the same one."""
        if self._connection_factory is not None:
            return self._connection_factory()
        # Fallback: create our own connection (for tests without a proxy)
        conn = getattr(self._local, "conn", None)
        if conn is None:
            from sqlalchemy import text

            conn = self._engine.connect()
            conn.execute(text(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}"))
            self._local.conn = conn
        return conn

    def execute(self, *args, **kwargs):
        """Execute SQL on the thread-local connection.

        Drop-in replacement for Connection.execute(), enabling repos
        to use Session directly instead of a raw Connection or proxy.
        """
        return self.connection.execute(*args, **kwargs)

    def commit(self) -> None:
        """Commit the current transaction. Called by command handlers."""
        self.connection.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.connection.rollback()

    def close(self) -> None:
        """Close all connections and dispose the engine."""
        self._engine.dispose()
