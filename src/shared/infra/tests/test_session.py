"""
Tests for Session - project-scoped database session.

TDD: tests written first, then implementation.
"""

from __future__ import annotations

import threading

import allure
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import SingletonThreadPool

from src.shared.infra.session import Session

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Shared Infrastructure"),
]


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with a test table."""
    eng = create_engine("sqlite:///:memory:", echo=False, poolclass=SingletonThreadPool)
    with eng.connect() as conn:
        conn.execute(
            text("CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)")
        )
        conn.commit()
    return eng


@pytest.fixture
def session(engine):
    """Create a Session wrapping the engine."""
    s = Session(engine)
    yield s
    s.close()


@allure.story("QC-000.01 Session Management")
class TestSessionCreationAndConnection:
    """Session creation, engine exposure, and connection identity."""

    @allure.title(
        "Exposes engine, returns connection, and reuses same-thread connection"
    )
    def test_engine_and_connection(self, session, engine):
        assert session.engine is engine

        conn = session.connection
        assert conn is not None

        # Same thread gets same connection
        conn2 = session.connection
        assert conn is conn2


@allure.story("QC-000.01 Session Management")
class TestSessionCommitAndRollback:
    """Session commit persists data, rollback discards it."""

    @allure.title("Commit persists insert, rollback discards uncommitted data")
    def test_commit_and_rollback(self, session):
        # Commit persists
        session.connection.execute(
            text("INSERT INTO test_items (id, name) VALUES (1, 'alpha')")
        )
        session.commit()

        result = session.connection.execute(
            text("SELECT name FROM test_items WHERE id = 1")
        )
        assert result.fetchone()[0] == "alpha"

        # Rollback discards
        session.connection.execute(
            text("INSERT INTO test_items (id, name) VALUES (2, 'beta')")
        )
        session.rollback()

        result = session.connection.execute(
            text("SELECT count(*) FROM test_items WHERE id = 2")
        )
        assert result.fetchone()[0] == 0


@allure.story("QC-000.01 Session Management")
class TestSessionThreadSafety:
    """Each thread gets its own connection, reused within that thread."""

    @allure.title("Different threads get different connections, same thread reuses")
    def test_thread_connection_isolation(self, session):
        main_conn = session.connection
        worker_conns = []

        def worker():
            worker_conns.append(session.connection)
            worker_conns.append(session.connection)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        # Worker thread gets different connection from main
        assert len(worker_conns) == 2
        assert worker_conns[0] is not main_conn
        # Worker thread reuses its own connection
        assert worker_conns[0] is worker_conns[1]


@allure.story("QC-000.01 Session Management")
class TestSessionExecuteAndClose:
    """Session.execute() delegates to connection, close() disposes engine."""

    @allure.title("Execute runs SQL and close disposes engine without error")
    def test_execute_and_close(self, engine):
        s = Session(engine)

        s.execute(text("INSERT INTO test_items (id, name) VALUES (10, 'gamma')"))
        s.commit()

        result = s.execute(text("SELECT name FROM test_items WHERE id = 10"))
        assert result.fetchone()[0] == "gamma"

        result = s.execute(text("SELECT count(*) FROM test_items"))
        assert result.fetchone()[0] >= 1

        # Close disposes engine without raising
        _ = s.connection  # force connection creation
        s.close()
