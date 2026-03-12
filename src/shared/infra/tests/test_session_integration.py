"""
Tests for Session integration with command handlers.

TDD: verifies that command handlers accept and use session.commit().
"""

from __future__ import annotations

import allure
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

pytestmark = [pytest.mark.unit]


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


@allure.epic("QualCoder v2")
@allure.feature("Shared Infrastructure")
@allure.story("QC-000.09 Session Management")
class TestCommandHandlerWithSession:
    """Command handlers should accept optional session and call session.commit()."""

    @allure.title("create_code accepts session, persists data, and works without session")
    def test_create_code_with_and_without_session(self, session, repos):
        event_bus = EventBus(history_size=10)

        # With session
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

        # Verify data is persisted
        command2 = CreateCodeCommand(name="Persisted", color="#00FF00")
        create_code(
            command=command2,
            code_repo=repos["code_repo"],
            category_repo=repos["category_repo"],
            segment_repo=repos["segment_repo"],
            event_bus=event_bus,
            session=session,
        )
        codes = repos["code_repo"].get_all()
        assert any(c.name == "Persisted" for c in codes)

        # Without session (backward compatibility)
        command3 = CreateCodeCommand(name="No Session", color="#0000FF")
        result3 = create_code(
            command=command3,
            code_repo=repos["code_repo"],
            category_repo=repos["category_repo"],
            segment_repo=repos["segment_repo"],
            event_bus=event_bus,
        )
        assert result3.is_success
