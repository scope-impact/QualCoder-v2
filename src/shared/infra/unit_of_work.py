"""
Unit of Work - Atomic Transaction Support

Provides atomic transaction support for multi-step operations that span
multiple repository calls. Without UoW, each repo.save()/repo.delete()
commits independently. With UoW, all operations commit or rollback together.

Usage:
    with UnitOfWork(connection) as uow:
        segment_repo.delete_by_code(code_id)
        code_repo.delete(code_id)
        uow.commit()
    # Event published AFTER commit
    event_bus.publish(event)

How it works:
    Repositories call connection.commit() after each operation. The UoW
    temporarily suppresses these individual commits by replacing the
    connection's commit method with a no-op. When uow.commit() is called,
    the real commit is executed. On rollback or exception, a ROLLBACK
    is issued to undo all uncommitted changes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Connection

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Context manager for atomic multi-step operations.

    Suppresses individual repository commits and provides
    explicit commit/rollback control.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection
        self._original_commit: Any = None
        self._committed = False
        self._rolled_back = False

    def __enter__(self) -> UnitOfWork:
        # Save original commit and replace with no-op
        self._original_commit = self._conn.commit
        self._conn.commit = self._noop_commit  # type: ignore[method-assign]
        self._committed = False
        self._rolled_back = False
        logger.debug("UnitOfWork started")
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        # Restore original commit method
        if self._original_commit is not None:
            self._conn.commit = self._original_commit  # type: ignore[method-assign]
            self._original_commit = None

        # Rollback if not already committed or rolled back
        needs_rollback = not self._committed and not self._rolled_back
        if not needs_rollback:
            return

        reason = (
            f"exception: {exc_val}" if exc_type is not None else "no explicit commit"
        )
        try:
            self._conn.rollback()
            logger.debug("UnitOfWork rolled back (%s)", reason)
        except Exception:
            logger.exception("Failed to rollback UoW (%s)", reason)

    def commit(self) -> None:
        """Commit all operations in this unit of work."""
        if self._rolled_back:
            msg = "Cannot commit: UnitOfWork was already rolled back"
            raise RuntimeError(msg)
        if self._committed:
            msg = "Cannot commit: UnitOfWork was already committed"
            raise RuntimeError(msg)

        # Call the original commit
        if self._original_commit is not None:
            self._original_commit()
        self._committed = True
        logger.debug("UnitOfWork committed")

    def rollback(self) -> None:
        """Rollback all operations in this unit of work."""
        if self._committed:
            msg = "Cannot rollback: UnitOfWork was already committed"
            raise RuntimeError(msg)

        self._conn.rollback()
        self._rolled_back = True
        logger.debug("UnitOfWork rolled back explicitly")

    @staticmethod
    def _noop_commit() -> None:
        """No-op replacement for connection.commit() during UoW scope."""
