"""
Tests for Session - project-scoped database session.

TDD: tests written first, then implementation.
"""

from __future__ import annotations

import threading

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.pool import SingletonThreadPool

from src.shared.infra.session import Session


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine with a test table."""
    eng = create_engine("sqlite:///:memory:", echo=False, poolclass=SingletonThreadPool)
    with eng.connect() as conn:
        conn.execute(text("CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.commit()
    return eng


@pytest.fixture
def session(engine):
    """Create a Session wrapping the engine."""
    s = Session(engine)
    yield s
    s.close()


class TestSessionCreation:
    """Session should wrap an engine and expose it."""

    def test_exposes_engine(self, session, engine):
        assert session.engine is engine

    def test_connection_returns_a_connection(self, session):
        conn = session.connection
        assert conn is not None

    def test_same_thread_gets_same_connection(self, session):
        conn1 = session.connection
        conn2 = session.connection
        assert conn1 is conn2


class TestSessionCommit:
    """Session.commit() should persist data."""

    def test_commit_persists_insert(self, session):
        session.connection.execute(
            text("INSERT INTO test_items (id, name) VALUES (1, 'alpha')")
        )
        session.commit()

        result = session.connection.execute(text("SELECT name FROM test_items WHERE id = 1"))
        assert result.fetchone()[0] == "alpha"

    def test_uncommitted_data_lost_on_rollback(self, session):
        session.connection.execute(
            text("INSERT INTO test_items (id, name) VALUES (2, 'beta')")
        )
        session.rollback()

        result = session.connection.execute(text("SELECT count(*) FROM test_items"))
        assert result.fetchone()[0] == 0


class TestSessionThreadSafety:
    """Each thread should get its own connection."""

    def test_different_threads_get_different_connections(self, session):
        main_conn = session.connection
        worker_conn = None

        def worker():
            nonlocal worker_conn
            worker_conn = session.connection

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert worker_conn is not None
        assert worker_conn is not main_conn

    def test_worker_thread_gets_same_connection_on_repeated_access(self, session):
        conns = []

        def worker():
            conns.append(session.connection)
            conns.append(session.connection)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert len(conns) == 2
        assert conns[0] is conns[1]


class TestSessionClose:
    """Session.close() should dispose the engine."""

    def test_close_disposes_engine(self, engine):
        s = Session(engine)
        _ = s.connection  # force connection creation
        s.close()

        # After dispose, getting a new connection should still work
        # (engine creates new pool) but the old pool is cleaned up.
        # We just verify close doesn't raise.
