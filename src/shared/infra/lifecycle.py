"""
Project Lifecycle - Database Connection Management

Handles the lifecycle of project databases:
- Opening existing databases
- Creating new databases
- Closing connections

This extracts database management from the controller into a focused module.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

logger = logging.getLogger("qualcoder.shared.lifecycle")

if TYPE_CHECKING:
    from sqlalchemy import Connection, Engine

    from src.contexts.projects.core.entities import Project

from src.shared.infra.session import Session


class ProjectLifecycle:
    """
    Manages database lifecycle for project files.

    Responsibilities:
    - Open database connections for .qda files
    - Create new project databases with schema
    - Close connections cleanly
    - Provide per-thread connections via connection_factory

    This class owns the SQLAlchemy engine and connection.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._engine: Engine | None = None
        self._connection: Connection | None = None
        self._session: Session | None = None
        self._current_path: Path | None = None
        self._thread_local: threading.local = threading.local()
        self._connection_factory: Callable[[], Connection] | None = None

    @property
    def connection(self) -> Connection | None:
        """Get the current database connection."""
        return self._connection

    @property
    def engine(self) -> Engine | None:
        """Get the current SQLAlchemy engine."""
        return self._engine

    @property
    def session(self) -> Session | None:
        """Get the current Session (project-scoped, thread-safe)."""
        return self._session

    @property
    def connection_factory(self) -> Callable[[], Connection] | None:
        """Get the per-thread connection factory.

        Returns a callable that provides thread-local connections with
        busy_timeout set. Same thread always gets the same connection.
        None when no project is open.
        """
        return self._connection_factory

    @property
    def current_path(self) -> Path | None:
        """Get the path of the currently open database."""
        return self._current_path

    @property
    def is_open(self) -> bool:
        """Check if a database is currently open."""
        return self._connection is not None

    def open_database(self, path: Path) -> Result[Connection, str]:
        """
        Open an existing project database.

        Args:
            path: Path to the .qda SQLite database file

        Returns:
            Success with Connection, or Failure with error message
        """
        from sqlalchemy import create_engine

        logger.debug("Opening database: %s", path)

        # Validate file exists
        if not path.exists():
            logger.error("Database file not found: %s", path)
            return Failure(f"Database file not found: {path}")

        # Close any existing connection first
        self.close_database()

        try:
            from sqlalchemy.pool import SingletonThreadPool

            # Create engine with SingletonThreadPool for safe multi-thread access.
            # SingletonThreadPool gives each thread its own DBAPI connection,
            # enabling MCP asyncio.to_thread() calls alongside Qt main thread.
            db_url = f"sqlite:///{path}"
            self._engine = create_engine(
                db_url, echo=False, poolclass=SingletonThreadPool
            )

            # Enable automatic SQL query tracing
            from src.shared.infra.telemetry import instrument_sqlalchemy

            instrument_sqlalchemy(self._engine)

            from sqlalchemy import text

            # Enable WAL mode before creating connections.
            # WAL allows concurrent readers + writer, eliminating most
            # "database is locked" errors in multi-threaded access.
            with self._engine.connect() as setup_conn:
                setup_conn.execute(text("PRAGMA journal_mode=WAL"))
                setup_conn.commit()

            self._connection = self._engine.connect()
            self._current_path = path

            # Store main-thread connection in thread-local for the factory
            self._thread_local.connection = self._connection
            self._connection_factory = self._get_or_create_connection

            # Session uses the same connection factory so session.commit()
            # commits the same connection that repos use via the proxy.
            self._session = Session(
                self._engine,
                connection_factory=self._get_or_create_connection,
            )

            logger.info("Database opened: %s", path)
            return Success(self._connection)

        except Exception as e:
            logger.error("Failed to open database %s: %s", path, e, exc_info=True)
            self._cleanup()
            return Failure(f"Failed to open database: {e}")

    def create_database(self, path: Path, name: str) -> Result[Project, str]:
        """
        Create a new project database with schema.

        Args:
            path: Path for the new .qda database file
            name: Name for the project

        Returns:
            Success with Project entity, or Failure with error message
        """
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        # Validate path doesn't exist
        if path.exists():
            return Failure(f"Database file already exists: {path}")

        # Validate parent directory exists
        if not path.parent.exists():
            return Failure(f"Parent directory does not exist: {path.parent}")

        try:
            # Create the database using the repository
            repo = SQLiteProjectRepository()
            project = repo.create_database(path, name)

            # Open the newly created database
            result = self.open_database(path)
            if isinstance(result, Failure):
                return result

            logger.info("Database created: %s (name=%s)", path, name)
            return Success(project)

        except (FileExistsError, ValueError, PermissionError) as e:
            logger.error("Failed to create database %s: %s", path, e)
            return Failure(str(e))
        except Exception as e:
            logger.error("Failed to create database %s: %s", path, e, exc_info=True)
            return Failure(f"Failed to create database: {e}")

    def close_database(self) -> None:
        """Close the current database connection."""
        if self._current_path:
            logger.info("Closing database: %s", self._current_path)
        self._cleanup()

    def _get_or_create_connection(self) -> Connection:
        """Return a thread-local connection, creating one if needed.

        Each thread gets its own connection via SingletonThreadPool.
        Worker-thread connections have busy_timeout set to avoid
        immediate "database is locked" errors.
        """
        conn = getattr(self._thread_local, "connection", None)
        if conn is not None:
            return conn

        from sqlalchemy import text

        conn = self._engine.connect()
        from src.shared.infra.session import SQLITE_BUSY_TIMEOUT_MS

        conn.execute(text(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}"))
        conn.commit()
        self._thread_local.connection = conn
        return conn

    def _cleanup(self) -> None:
        """Clean up connection and engine resources."""
        # Clear the factory, session, and thread-local state
        self._connection_factory = None
        self._session = None
        self._thread_local = threading.local()

        # Close connection
        if self._connection is not None:
            with contextlib.suppress(Exception):
                self._connection.close()
            self._connection = None

        # Dispose engine (also cleans up all pooled connections)
        if self._engine is not None:
            with contextlib.suppress(Exception):
                self._engine.dispose()
            self._engine = None

        self._current_path = None
