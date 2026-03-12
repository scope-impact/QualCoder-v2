"""
Exchange Infra: RQDA Reader Tests

Tests for reading RQDA SQLite databases.
RQDA is an R package for qualitative data analysis that stores data in SQLite.
"""

from __future__ import annotations

import sqlite3

import allure
import pytest

pytestmark = [pytest.mark.unit]


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


@allure.epic("QualCoder v2")
@allure.feature("QC-039 Import Export Formats")
@allure.story("QC-036.03 Import RQDA")
class TestRqdaReader:
    @allure.title("Reads codes, sources, and codings; excludes deleted records")
    def test_read_codes_sources_codings_excluding_deleted(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        # Codes: 2 active, 1 deleted
        conn.execute(
            "INSERT INTO freecode (name, id, color, status) VALUES ('Joy', 1, '#00ff00', 1)"
        )
        conn.execute(
            "INSERT INTO freecode (name, id, color, status) VALUES ('Anger', 2, '#ff0000', 1)"
        )
        conn.execute("INSERT INTO freecode (name, id, status) VALUES ('Deleted', 3, 0)")
        # Sources: 1 active, 1 deleted
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('interview.txt', 1, 'Hello world.', 1)"
        )
        conn.execute(
            "INSERT INTO source (name, id, file, status) VALUES ('deleted.txt', 2, 'Deleted.', 0)"
        )
        # Coding
        conn.execute(
            "INSERT INTO coding (cid, fid, seltext, selfirst, selend, status) VALUES (1, 1, 'Hello', 0, 5, 1)"
        )
        conn.commit()
        conn.close()

        result = read_rqda(db_path)

        # Codes: deleted excluded
        assert len(result.codes) == 2
        names = {c.name for c in result.codes}
        assert "Joy" in names
        assert "Anger" in names

        # Sources: deleted excluded
        assert len(result.sources) == 1
        assert result.sources[0].name == "interview.txt"
        assert result.sources[0].fulltext == "Hello world."

        # Codings
        assert len(result.codings) == 1
        assert result.codings[0].code_id == 1
        assert result.codings[0].source_id == 1
        assert result.codings[0].start == 0
        assert result.codings[0].end == 5
        assert result.codings[0].selected_text == "Hello"

    @allure.title("Empty database returns empty results")
    def test_read_empty_db(self, tmp_path):
        from src.contexts.exchange.infra.rqda_reader import read_rqda

        db_path = tmp_path / "project.rqda"
        conn = _create_rqda_db(db_path)
        conn.close()

        result = read_rqda(db_path)

        assert len(result.codes) == 0
        assert len(result.sources) == 0
        assert len(result.codings) == 0
