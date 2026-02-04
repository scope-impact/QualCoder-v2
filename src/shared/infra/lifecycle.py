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
from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from sqlalchemy import Connection, Engine

    from src.contexts.projects.core.entities import Project


class ProjectLifecycle:
    """
    Manages database lifecycle for project files.

    Responsibilities:
    - Open database connections for .qda files
    - Create new project databases with schema
    - Close connections cleanly

    This class owns the SQLAlchemy engine and connection.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._engine: Engine | None = None
        self._connection: Connection | None = None
        self._current_path: Path | None = None

    @property
    def connection(self) -> Connection | None:
        """Get the current database connection."""
        return self._connection

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

        # Validate file exists
        if not path.exists():
            return Failure(f"Database file not found: {path}")

        # Close any existing connection first
        self.close_database()

        try:
            # Create engine and connection
            db_url = f"sqlite:///{path}"
            self._engine = create_engine(db_url, echo=False)

            # Enable automatic SQL query tracing
            from src.shared.infra.telemetry import instrument_sqlalchemy

            instrument_sqlalchemy(self._engine)

            self._connection = self._engine.connect()
            self._current_path = path

            return Success(self._connection)

        except Exception as e:
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

            return Success(project)

        except (FileExistsError, ValueError, PermissionError) as e:
            return Failure(str(e))
        except Exception as e:
            return Failure(f"Failed to create database: {e}")

    def close_database(self) -> None:
        """Close the current database connection."""
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up connection and engine resources."""
        # Close connection
        if self._connection is not None:
            with contextlib.suppress(Exception):
                self._connection.close()
            self._connection = None

        # Dispose engine
        if self._engine is not None:
            with contextlib.suppress(Exception):
                self._engine.dispose()
            self._engine = None

        self._current_path = None
