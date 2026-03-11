"""
Thread-safe connection proxy for multi-threaded repository access.

Wraps a connection factory (from ProjectLifecycle) to provide per-thread
SQLAlchemy connections. Repos receive this proxy instead of a raw Connection,
enabling safe concurrent access from Qt main thread and MCP worker threads.

The proxy implements the same interface repos use (execute, commit) so no
repository code changes are needed.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Connection


class ThreadSafeConnectionProxy:
    """
    Proxy that delegates execute/commit to thread-local connections.

    Each thread gets its own Connection from the factory, cached in
    thread-local storage. The main thread's connection is stored at
    construction time so it's always available without calling the factory.
    """

    def __init__(
        self,
        main_connection: Connection,
        factory: Callable[[], Connection],
    ) -> None:
        self._factory = factory
        self._local = threading.local()
        # Cache the main thread's connection immediately
        self._local.connection = main_connection

    def _get_connection(self) -> Connection:
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = self._factory()
            self._local.connection = conn
        return conn

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Delegate to the thread-local connection."""
        return self._get_connection().execute(*args, **kwargs)

    def commit(self) -> None:
        """Delegate to the thread-local connection."""
        self._get_connection().commit()

    def rollback(self) -> None:
        """Delegate to the thread-local connection."""
        self._get_connection().rollback()

    @property
    def engine(self) -> Any:
        """Expose the engine for code that needs it (e.g., SyncEngine)."""
        return self._get_connection().engine
