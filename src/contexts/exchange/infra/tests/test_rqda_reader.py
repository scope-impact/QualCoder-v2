"""
Exchange Infra: RQDA Reader Tests (TDD - RED phase)

Tests for reading RQDA SQLite databases.
RQDA is an R package for qualitative data analysis that stores data in SQLite.
"""

from __future__ import annotations

import sqlite3


def _create_rqda_db(path):
    """Create a minimal RQDA-compatible SQLite database."""
    conn = sqlite3.connect(str(path))
    c = conn.cursor()

    # RQDA schema (simplified)
    c.execute("""CREATE TABLE source (
        name TEXT, id INTEGER PRIMARY KEY, file TEXT,
        memo TEXT, owner TEXT, date TEXT, status INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE freecode (
        name TEXT, memo TEXT, owner TEXT, date TEXT,
        id INTEGER PRIMARY KEY, status INTEGER DEFAULT 1, color TEXT
    )""")
    c.execute("""CREATE TABLE coding (
        cid INTEGER, fid INTEGER, seltext TEXT,
        selfirst INTEGER, selend INTEGER,
        status INTEGER DEFAULT 1, owner TEXT, date TEXT,
        memo TEXT
    )""")
    c.execute("""CREATE TABLE codecat (
        name TEXT, cid INTEGER, catid INTEGER,
        owner TEXT, date TEXT, memo TEXT, status INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE cases (
        name TEXT, memo TEXT, owner TEXT, date TEXT,
        id INTEGER PRIMARY KEY, status INTEGER DEFAULT 1
    )""")

    conn.commit()
    return conn


class TestRqdaReader:
    def test_read_codes(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.execute(
            "INSERT INTO freecode (name, id, color, status) VALUES ('Joy', 1, '#00ff00', 1)"
        )
        conn.execute(
            "INSERT INTO freecode (name, id, color, status) VALUES ('Anger', 2, '#ff0000', 1)"
        )
        conn.execute(
            "INSERT INTO freecode (name, id, status) VALUES ('Deleted', 3, 0)"
        )  # deleted
        conn.commit()
        conn.close()

        result = read_rqda(db_path)

        assert len(result.codes) == 2  # Deleted excluded
        names = {c.name for c in result.codes}
        assert "Joy" in names
        assert "Anger" in names

    def test_read_sources(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('interview.txt', 1, 'Hello world.', 1)"
        )
        conn.commit()
        conn.close()

        result = read_rqda(db_path)

        assert len(result.sources) == 1
        assert result.sources[0].name == "interview.txt"
        assert result.sources[0].fulltext == "Hello world."

    def test_read_codings(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('doc.txt', 1, 'I felt happy.', 1)"
        )
        conn.execute(
            "INSERT INTO freecode (name, id, color, status) VALUES ('Joy', 1, '#00ff00', 1)"
        )
        conn.execute(
            "INSERT INTO coding (cid, fid, seltext, selfirst, selend, status) VALUES (1, 1, 'happy', 7, 12, 1)"
        )
        conn.commit()
        conn.close()

        result = read_rqda(db_path)

        assert len(result.codings) == 1
        assert result.codings[0].code_id == 1
        assert result.codings[0].source_id == 1
        assert result.codings[0].start == 7
        assert result.codings[0].end == 12
        assert result.codings[0].selected_text == "happy"

    def test_read_excludes_deleted(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('active.txt', 1, 'Active.', 1)"
        )
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('deleted.txt', 2, 'Deleted.', 0)"
        )
        conn.commit()
        conn.close()

        result = read_rqda(db_path)

        assert len(result.sources) == 1
        assert result.sources[0].name == "active.txt"

    def test_read_empty_db(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.close()

        result = read_rqda(db_path)

        assert len(result.codes) == 0
        assert len(result.sources) == 0
        assert len(result.codings) == 0
