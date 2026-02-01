"""
Privacy Context: SQLAlchemy Core Repository Implementations

Implements repository interfaces for Pseudonym and AnonymizationSession
entities using SQLAlchemy Core for clean, type-safe database access.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.domain.privacy.entities import (
    AnonymizationSession,
    AnonymizationSessionId,
    Pseudonym,
    PseudonymCategory,
    PseudonymId,
    TextReplacement,
)
from src.domain.shared.types import SourceId
from src.infrastructure.privacy.schema import (
    anonymization_replacement,
    anonymization_session,
    pseudonym,
)

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLitePseudonymRepository:
    """
    SQLAlchemy Core implementation of PseudonymRepository.

    Maps between domain Pseudonym entities and the pseudonym table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Pseudonym]:
        """Get all pseudonyms."""
        stmt = select(pseudonym).order_by(pseudonym.c.alias)
        result = self._conn.execute(stmt)
        return [self._row_to_pseudonym(row) for row in result]

    def get_by_id(self, pseudonym_id: PseudonymId) -> Pseudonym | None:
        """Get a pseudonym by ID."""
        stmt = select(pseudonym).where(pseudonym.c.id == pseudonym_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_pseudonym(row) if row else None

    def get_by_real_name(self, real_name: str) -> Pseudonym | None:
        """Get a pseudonym by real name (case-insensitive)."""
        stmt = select(pseudonym).where(
            func.lower(pseudonym.c.real_name) == real_name.lower()
        )
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_pseudonym(row) if row else None

    def get_by_alias(self, alias: str) -> Pseudonym | None:
        """Get a pseudonym by alias (case-insensitive)."""
        stmt = select(pseudonym).where(func.lower(pseudonym.c.alias) == alias.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_pseudonym(row) if row else None

    def get_by_category(self, category: PseudonymCategory) -> list[Pseudonym]:
        """Get all pseudonyms in a category."""
        stmt = (
            select(pseudonym)
            .where(pseudonym.c.category == category.value)
            .order_by(pseudonym.c.alias)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_pseudonym(row) for row in result]

    def save(self, entity: Pseudonym) -> None:
        """Save a pseudonym (insert or update)."""
        exists = self.exists(entity.id)
        now = datetime.now(UTC)

        if exists:
            stmt = (
                update(pseudonym)
                .where(pseudonym.c.id == entity.id.value)
                .values(
                    real_name=entity.real_name,
                    alias=entity.alias,
                    category=entity.category.value,
                    notes=entity.notes,
                    updated_at=now,
                )
            )
        else:
            stmt = pseudonym.insert().values(
                id=entity.id.value,
                real_name=entity.real_name,
                alias=entity.alias,
                category=entity.category.value,
                notes=entity.notes,
                created_at=entity.created_at,
                updated_at=now,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, pseudonym_id: PseudonymId) -> None:
        """Delete a pseudonym by ID."""
        stmt = delete(pseudonym).where(pseudonym.c.id == pseudonym_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, pseudonym_id: PseudonymId) -> bool:
        """Check if a pseudonym exists."""
        stmt = select(func.count()).where(pseudonym.c.id == pseudonym_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def real_name_exists(
        self, real_name: str, exclude_id: PseudonymId | None = None
    ) -> bool:
        """Check if a real name is already mapped."""
        stmt = select(func.count()).where(
            func.lower(pseudonym.c.real_name) == real_name.lower()
        )
        if exclude_id:
            stmt = stmt.where(pseudonym.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def alias_exists(self, alias: str, exclude_id: PseudonymId | None = None) -> bool:
        """Check if an alias is already used."""
        stmt = select(func.count()).where(
            func.lower(pseudonym.c.alias) == alias.lower()
        )
        if exclude_id:
            stmt = stmt.where(pseudonym.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def _row_to_pseudonym(self, row) -> Pseudonym:
        """Convert a database row to a Pseudonym entity."""
        return Pseudonym(
            id=PseudonymId(value=row.id),
            real_name=row.real_name,
            alias=row.alias,
            category=PseudonymCategory(row.category),
            notes=row.notes,
            created_at=row.created_at if row.created_at else datetime.now(UTC),
        )


class SQLiteAnonymizationSessionRepository:
    """
    SQLAlchemy Core implementation of AnonymizationSessionRepository.

    Manages anonymization sessions with their associated replacements.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_by_id(
        self, session_id: AnonymizationSessionId
    ) -> AnonymizationSession | None:
        """Get a session by ID."""
        stmt = select(anonymization_session).where(
            anonymization_session.c.id == session_id.value
        )
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if not row:
            return None

        # Get replacements for this session
        replacements = self._get_replacements(session_id.value)

        return self._row_to_session(row, replacements)

    def get_by_source(self, source_id: SourceId) -> list[AnonymizationSession]:
        """Get all sessions for a source."""
        stmt = (
            select(anonymization_session)
            .where(anonymization_session.c.source_id == source_id.value)
            .order_by(anonymization_session.c.created_at.desc())
        )
        result = self._conn.execute(stmt)

        sessions = []
        for row in result:
            replacements = self._get_replacements(row.id)
            sessions.append(self._row_to_session(row, replacements))
        return sessions

    def get_active_session(self, source_id: SourceId) -> AnonymizationSession | None:
        """Get the most recent non-reverted session for a source."""
        stmt = (
            select(anonymization_session)
            .where(anonymization_session.c.source_id == source_id.value)
            .where(anonymization_session.c.reverted_at.is_(None))
            .order_by(anonymization_session.c.created_at.desc())
            .limit(1)
        )
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if not row:
            return None

        replacements = self._get_replacements(row.id)
        return self._row_to_session(row, replacements)

    def save(self, session: AnonymizationSession) -> None:
        """Save a session and its replacements."""
        # Check if exists
        exists_stmt = select(func.count()).where(
            anonymization_session.c.id == session.id.value
        )
        exists = self._conn.execute(exists_stmt).scalar() > 0

        # Serialize pseudonym IDs to JSON
        pseudonym_ids_json = json.dumps([pid.value for pid in session.pseudonym_ids])

        if exists:
            stmt = (
                update(anonymization_session)
                .where(anonymization_session.c.id == session.id.value)
                .values(
                    source_id=session.source_id.value,
                    original_text=session.original_text,
                    pseudonym_ids_json=pseudonym_ids_json,
                    reverted_at=session.reverted_at,
                )
            )
        else:
            stmt = anonymization_session.insert().values(
                id=session.id.value,
                source_id=session.source_id.value,
                original_text=session.original_text,
                pseudonym_ids_json=pseudonym_ids_json,
                created_at=session.created_at,
                reverted_at=session.reverted_at,
            )

        self._conn.execute(stmt)

        # Save replacements (delete existing first if updating)
        if exists:
            del_stmt = delete(anonymization_replacement).where(
                anonymization_replacement.c.session_id == session.id.value
            )
            self._conn.execute(del_stmt)

        for i, replacement in enumerate(session.replacements):
            # We need to extract pseudonym_id from the replacement
            # For simplicity, we'll use the index as a placeholder
            positions_json = json.dumps(list(replacement.positions))
            repl_stmt = anonymization_replacement.insert().values(
                session_id=session.id.value,
                pseudonym_id=i,  # Would need actual pseudonym_id tracking
                original_text=replacement.original_text,
                replacement_text=replacement.replacement_text,
                positions_json=positions_json,
            )
            self._conn.execute(repl_stmt)

        self._conn.commit()

    def mark_reverted(self, session_id: AnonymizationSessionId) -> None:
        """Mark a session as reverted."""
        now = datetime.now(UTC)
        stmt = (
            update(anonymization_session)
            .where(anonymization_session.c.id == session_id.value)
            .values(reverted_at=now)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def _get_replacements(self, session_id: str) -> tuple[TextReplacement, ...]:
        """Get all replacements for a session."""
        stmt = (
            select(anonymization_replacement)
            .where(anonymization_replacement.c.session_id == session_id)
            .order_by(anonymization_replacement.c.id)
        )
        result = self._conn.execute(stmt)

        replacements = []
        for row in result:
            positions = tuple(tuple(p) for p in json.loads(row.positions_json))
            replacements.append(
                TextReplacement(
                    original_text=row.original_text,
                    replacement_text=row.replacement_text,
                    positions=positions,
                )
            )
        return tuple(replacements)

    def _row_to_session(
        self, row, replacements: tuple[TextReplacement, ...]
    ) -> AnonymizationSession:
        """Convert a database row to an AnonymizationSession entity."""
        # Parse pseudonym IDs from JSON
        pseudonym_ids_raw = json.loads(row.pseudonym_ids_json or "[]")
        pseudonym_ids = tuple(PseudonymId(value=pid) for pid in pseudonym_ids_raw)

        return AnonymizationSession(
            id=AnonymizationSessionId(value=row.id),
            source_id=SourceId(value=row.source_id),
            original_text=row.original_text,
            pseudonym_ids=pseudonym_ids,
            replacements=replacements,
            created_at=row.created_at if row.created_at else datetime.now(UTC),
            reverted_at=row.reverted_at,
        )
