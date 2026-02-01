"""
Settings Repository - SQLAlchemy Core Implementation.

Implements the repository for project-level settings using SQLAlchemy Core.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.infrastructure.projects.schema import project_settings

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteProjectSettingsRepository:
    """
    Repository for project-level settings.

    Stores key-value pairs for project metadata.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get(self, key: str) -> str | None:
        """Get a setting value by key."""
        stmt = select(project_settings.c.value).where(project_settings.c.key == key)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return row.value if row else None

    def set(self, key: str, value: str) -> None:
        """Set a setting value."""
        exists_stmt = select(func.count()).where(project_settings.c.key == key)
        exists = self._conn.execute(exists_stmt).scalar() > 0

        if exists:
            stmt = (
                update(project_settings)
                .where(project_settings.c.key == key)
                .values(value=value, updated_at=datetime.now(UTC))
            )
        else:
            stmt = project_settings.insert().values(
                key=key,
                value=value,
                updated_at=datetime.now(UTC),
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, key: str) -> None:
        """Delete a setting."""
        stmt = delete(project_settings).where(project_settings.c.key == key)
        self._conn.execute(stmt)
        self._conn.commit()

    def get_all(self) -> dict[str, str]:
        """Get all settings as a dictionary."""
        stmt = select(project_settings)
        result = self._conn.execute(stmt)
        return {row.key: row.value for row in result}

    # Convenience methods for common settings

    def get_project_name(self) -> str | None:
        """Get the project name."""
        return self.get("project_name")

    def set_project_name(self, name: str) -> None:
        """Set the project name."""
        self.set("project_name", name)

    def get_project_memo(self) -> str | None:
        """Get the project memo."""
        return self.get("project_memo")

    def set_project_memo(self, memo: str) -> None:
        """Set the project memo."""
        self.set("project_memo", memo)
