"""
QC-039.03: Import RQDA Project - E2E Tests

TDD: Tests written FIRST, before implementation.
"""
from __future__ import annotations

import sqlite3

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


def _create_rqda_db(path):
    """Create a populated RQDA database for testing."""
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
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
        status INTEGER DEFAULT 1, owner TEXT, date TEXT, memo TEXT
    )""")
    c.execute("""CREATE TABLE codecat (
        name TEXT, cid INTEGER, catid INTEGER,
        owner TEXT, date TEXT, memo TEXT, status INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE cases (
        name TEXT, memo TEXT, owner TEXT, date TEXT,
        id INTEGER PRIMARY KEY, status INTEGER DEFAULT 1
    )""")

    # Seed data
    c.execute("INSERT INTO source (name, id, file, status) VALUES ('interview.txt', 1, 'I felt very happy about learning.', 1)")
    c.execute("INSERT INTO freecode (name, id, color, status) VALUES ('Positive', 1, '#00ff00', 1)")
    c.execute("INSERT INTO freecode (name, id, color, status) VALUES ('Learning', 2, '#0000ff', 1)")
    c.execute("INSERT INTO coding (cid, fid, seltext, selfirst, selend, status) VALUES (1, 1, 'happy', 12, 17, 1)")

    conn.commit()
    conn.close()
    return path


@allure.story("QC-039.03 Import RQDA Project")
class TestImportRQDA:

    @allure.title("AC #1: I can import an RQDA database")
    def test_ac1_import_rqda(
        self, source_repo, code_repo, category_repo, segment_repo, event_bus, tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand

        rqda_path = _create_rqda_db(tmp_path / "project.rqda")

        with allure.step("Import RQDA"):
            result = import_rqda(
                command=ImportRqdaCommand(source_path=str(rqda_path)),
                source_repo=source_repo,
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Import failed: {result.error}"

    @allure.title("AC #2: Import creates codes from RQDA")
    def test_ac2_creates_codes(
        self, source_repo, code_repo, category_repo, segment_repo, event_bus, tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand

        rqda_path = _create_rqda_db(tmp_path / "project.rqda")

        import_rqda(
            command=ImportRqdaCommand(source_path=str(rqda_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify codes"):
            codes = code_repo.get_all()
            code_names = {c.name for c in codes}
            assert "Positive" in code_names
            assert "Learning" in code_names

    @allure.title("AC #3: Import creates sources from RQDA")
    def test_ac3_creates_sources(
        self, source_repo, code_repo, category_repo, segment_repo, event_bus, tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand

        rqda_path = _create_rqda_db(tmp_path / "project.rqda")

        import_rqda(
            command=ImportRqdaCommand(source_path=str(rqda_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify sources"):
            sources = source_repo.get_all()
            assert any(s.name == "interview.txt" for s in sources)

    @allure.title("Import publishes RqdaImported event")
    def test_publishes_event(
        self, source_repo, code_repo, category_repo, segment_repo, event_bus, tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand
        from src.contexts.exchange.core.events import RqdaImported

        published = []
        event_bus.subscribe("exchange.rqda_imported", published.append)

        rqda_path = _create_rqda_db(tmp_path / "project.rqda")

        import_rqda(
            command=ImportRqdaCommand(source_path=str(rqda_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify event"):
            assert len(published) == 1
            assert isinstance(published[0], RqdaImported)
            assert published[0].codes_created == 2
            assert published[0].sources_created == 1

    @allure.title("Import fails with nonexistent file")
    def test_fails_nonexistent(
        self, source_repo, code_repo, category_repo, segment_repo, event_bus, tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_rqda import import_rqda
        from src.contexts.exchange.core.commands import ImportRqdaCommand

        result = import_rqda(
            command=ImportRqdaCommand(source_path=str(tmp_path / "missing.rqda")),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert result.is_failure
        assert "FILE_NOT_FOUND" in result.error_code
