"""
Tests for Session integration with command handlers.

TDD: verifies that command handlers accept and use session.commit().
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import SingletonThreadPool

from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commands import CreateCodeCommand
from src.contexts.coding.infra.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)
from src.contexts.projects.infra.schema import create_all_contexts
from src.shared.infra.event_bus import EventBus
from src.shared.infra.session import Session


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", echo=False, poolclass=SingletonThreadPool)
    create_all_contexts(eng)
    return eng


@pytest.fixture
def session(engine):
    s = Session(engine)
    yield s
    s.close()


@pytest.fixture
def repos(session):
    conn = session.connection
    return {
        "code_repo": SQLiteCodeRepository(conn),
        "category_repo": SQLiteCategoryRepository(conn),
        "segment_repo": SQLiteSegmentRepository(conn),
    }


class TestCommandHandlerWithSession:
    """Command handlers should accept optional session and call session.commit()."""

    def test_create_code_accepts_session_param(self, session, repos):
        event_bus = EventBus(history_size=10)
        command = CreateCodeCommand(name="Test Code", color="#FF0000")

        result = create_code(
            command=command,
            code_repo=repos["code_repo"],
            category_repo=repos["category_repo"],
            segment_repo=repos["segment_repo"],
            event_bus=event_bus,
            session=session,
        )

        assert result.is_success
        assert result.data.name == "Test Code"

    def test_create_code_data_persisted_via_session(self, session, repos):
        event_bus = EventBus(history_size=10)
        command = CreateCodeCommand(name="Persisted", color="#00FF00")

        create_code(
            command=command,
            code_repo=repos["code_repo"],
            category_repo=repos["category_repo"],
            segment_repo=repos["segment_repo"],
            event_bus=event_bus,
            session=session,
        )

        # Verify data is actually in DB
        codes = repos["code_repo"].get_all()
        assert len(codes) == 1
        assert codes[0].name == "Persisted"

    def test_create_code_still_works_without_session(self, session, repos):
        """Backward compatibility: handlers work without session param."""
        event_bus = EventBus(history_size=10)
        command = CreateCodeCommand(name="No Session", color="#0000FF")

        result = create_code(
            command=command,
            code_repo=repos["code_repo"],
            category_repo=repos["category_repo"],
            segment_repo=repos["segment_repo"],
            event_bus=event_bus,
        )

        assert result.is_success
