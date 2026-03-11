"""
QC-039 Round-Trip & Deep Verification Tests

Tests that actually prove import/export works end-to-end:
1. Export -> re-import -> verify data matches
2. Import -> verify ALL fields (segments, colors, attributes, text)
3. Import -> verify data visible via ViewModel/screen queries
"""

from __future__ import annotations

import sqlite3
import zipfile

import allure
import pytest

from src.contexts.coding.core.entities import (
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.types import CodeId, SegmentId, SourceId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


# =============================================================================
# Helpers
# =============================================================================


def _make_qdpx(tmp_path, xml_content, source_files=None):
    qdpx_path = tmp_path / "roundtrip.qdpx"
    with zipfile.ZipFile(qdpx_path, "w") as zf:
        zf.writestr("project.qde", xml_content)
        if source_files:
            for name, content in source_files.items():
                zf.writestr(name, content)
    return qdpx_path


def _create_rqda_db(path):
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

    # Source with known text
    c.execute(
        "INSERT INTO source (name, id, file, status) "
        "VALUES ('interview.txt', 1, 'I felt very happy about learning.', 1)"
    )
    # Deleted source (should be skipped)
    c.execute(
        "INSERT INTO source (name, id, file, status) "
        "VALUES ('deleted.txt', 2, 'Deleted content.', 0)"
    )
    # Codes
    c.execute(
        "INSERT INTO freecode (name, id, color, status) "
        "VALUES ('Positive', 1, '#00ff00', 1)"
    )
    c.execute(
        "INSERT INTO freecode (name, id, color, status) "
        "VALUES ('Learning', 2, '#0000ff', 1)"
    )
    # Deleted code (should be skipped)
    c.execute(
        "INSERT INTO freecode (name, id, color, status) "
        "VALUES ('Deleted', 3, '#ff0000', 0)"
    )
    # Coding segment: code 1 applied to source 1 at positions 12-17 ("happy")
    c.execute(
        "INSERT INTO coding (cid, fid, seltext, selfirst, selend, status) "
        "VALUES (1, 1, 'happy', 12, 17, 1)"
    )
    # Deleted coding (should be skipped)
    c.execute(
        "INSERT INTO coding (cid, fid, seltext, selfirst, selend, status) "
        "VALUES (2, 1, 'learning', 26, 34, 0)"
    )
    conn.commit()
    conn.close()
    return path


REFI_QDA_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="RoundTripTest">
  <CodeBook>
    <Codes>
      <Code guid="c1" name="Joy" isCodable="true" color="#00ff00"/>
      <Code guid="c2" name="Sadness" isCodable="true" color="#0000ff"/>
      <Code guid="cat1" name="Emotions" isCodable="false">
        <Code guid="c3" name="Anger" isCodable="true" color="#ff0000"/>
      </Code>
    </Codes>
  </CodeBook>
  <Sources>
    <TextSource guid="s1" name="interview.txt" plainTextPath="Sources/interview.txt">
      <PlainTextContent>I felt happy and sad today.</PlainTextContent>
    </TextSource>
  </Sources>
  <Coding guid="cod1">
    <CodeRef targetGUID="c1"/>
    <TextRange start="7" end="12" sourceGUID="s1"/>
  </Coding>
  <Coding guid="cod2">
    <CodeRef targetGUID="c2"/>
    <TextRange start="17" end="20" sourceGUID="s1"/>
  </Coding>
</Project>
"""


# =============================================================================
# Round-Trip: Export REFI-QDA -> Re-import -> Verify
# =============================================================================


@allure.story("QC-039 Round-Trip Verification")
class TestRefiQdaRoundTrip:
    @allure.title("Export REFI-QDA then re-import: codes survive round-trip")
    def test_refi_qda_round_trip_codes(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
        db_engine,
    ):
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import (
            import_refi_qda,
        )
        from src.contexts.exchange.core.commands import (
            ExportRefiQdaCommand,
            ImportRefiQdaCommand,
        )

        with allure.step("Seed project with codes, source, and segment"):
            source = Source(
                id=SourceId.new(),
                name="doc.txt",
                fulltext="I felt very happy about learning.",
                source_type=SourceType.TEXT,
            )
            source_repo.save(source)

            code_pos = Code(
                id=CodeId.new(), name="Positive", color=Color.from_hex("#00FF00")
            )
            code_learn = Code(
                id=CodeId.new(), name="Learning", color=Color.from_hex("#0000FF")
            )
            code_repo.save(code_pos)
            code_repo.save(code_learn)

            seg = TextSegment(
                id=SegmentId.new(),
                source_id=source.id,
                code_id=code_pos.id,
                position=TextPosition(start=12, end=17),
                selected_text="happy",
            )
            segment_repo.save(seg)

        original_code_names = {c.name for c in code_repo.get_all()}
        original_source_names = {s.name for s in source_repo.get_all()}

        with allure.step("Export to REFI-QDA"):
            export_path = tmp_path / "export.qdpx"
            result = export_refi_qda(
                command=ExportRefiQdaCommand(
                    output_path=str(export_path),
                    project_name="RoundTrip",
                ),
                source_repo=source_repo,
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )
            assert result.is_success, f"Export failed: {result.error}"

        # Create fresh repos from a second DB connection for re-import
        from sqlalchemy import create_engine

        from src.contexts.coding.infra.repositories import (
            SQLiteCategoryRepository,
            SQLiteCodeRepository,
            SQLiteSegmentRepository,
        )
        from src.contexts.projects.infra.schema import create_all_contexts
        from src.contexts.sources.infra.source_repository import (
            SQLiteSourceRepository,
        )

        engine2 = create_engine("sqlite:///:memory:", echo=False)
        create_all_contexts(engine2)
        conn2 = engine2.connect()

        code_repo2 = SQLiteCodeRepository(conn2)
        category_repo2 = SQLiteCategoryRepository(conn2)
        segment_repo2 = SQLiteSegmentRepository(conn2)
        source_repo2 = SQLiteSourceRepository(conn2)

        with allure.step("Re-import from exported file into fresh DB"):
            result = import_refi_qda(
                command=ImportRefiQdaCommand(source_path=str(export_path)),
                source_repo=source_repo2,
                code_repo=code_repo2,
                category_repo=category_repo2,
                segment_repo=segment_repo2,
                event_bus=event_bus,
            )
            assert result.is_success, f"Re-import failed: {result.error}"

        with allure.step("Verify codes survived round-trip"):
            reimported_code_names = {c.name for c in code_repo2.get_all()}
            assert reimported_code_names == original_code_names, (
                f"Code names don't match: {reimported_code_names} != {original_code_names}"
            )

        with allure.step("Verify source survived round-trip"):
            reimported_source_names = {s.name for s in source_repo2.get_all()}
            assert reimported_source_names == original_source_names, (
                f"Source names don't match: {reimported_source_names} != {original_source_names}"
            )

        conn2.close()
        engine2.dispose()


# =============================================================================
# Deep Import Verification: REFI-QDA
# =============================================================================


@allure.story("QC-039.02 Import REFI-QDA Project")
class TestRefiQdaDeepImport:
    @allure.title("Import REFI-QDA preserves segments, colors, categories, and source text")
    def test_import_preserves_all_aspects(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import (
            import_refi_qda,
        )
        from src.contexts.exchange.core.commands import ImportRefiQdaCommand

        qdpx = _make_qdpx(
            tmp_path,
            REFI_QDA_XML,
            {"Sources/interview.txt": "I felt happy and sad today."},
        )

        import_refi_qda(
            command=ImportRefiQdaCommand(source_path=str(qdpx)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify segments exist with correct positions"):
            all_segments = segment_repo.get_all()
            assert len(all_segments) >= 2, (
                f"Expected 2+ segments, got {len(all_segments)}"
            )
            positions = [(s.position.start, s.position.end) for s in all_segments]
            assert (7, 12) in positions, f"Missing segment 7-12 in {positions}"
            assert (17, 20) in positions, f"Missing segment 17-20 in {positions}"

        with allure.step("Verify code colors"):
            codes = code_repo.get_all()
            joy = next((c for c in codes if c.name == "Joy"), None)
            sadness = next((c for c in codes if c.name == "Sadness"), None)
            anger = next((c for c in codes if c.name == "Anger"), None)

            assert joy is not None, "Joy code not found"
            assert joy.color.to_hex().lower() == "#00ff00"
            assert sadness is not None, "Sadness code not found"
            assert sadness.color.to_hex().lower() == "#0000ff"
            assert anger is not None, "Anger code not found"
            assert anger.color.to_hex().lower() == "#ff0000"

        with allure.step("Verify Emotions category created"):
            categories = category_repo.get_all()
            cat_names = {c.name for c in categories}
            assert "Emotions" in cat_names, f"Missing 'Emotions' in {cat_names}"

        with allure.step("Verify Anger is under Emotions category"):
            assert anger.category_id is not None
            emotions_cat = next(c for c in categories if c.name == "Emotions")
            assert anger.category_id == emotions_cat.id

        with allure.step("Verify source text"):
            sources = source_repo.get_all()
            interview = next((s for s in sources if s.name == "interview.txt"), None)
            assert interview is not None
            assert interview.fulltext == "I felt happy and sad today."


# =============================================================================
# Deep Import Verification: RQDA
# =============================================================================


@allure.story("QC-039.03 Import RQDA Project")
class TestRqdaDeepImport:
    @allure.title("Import RQDA preserves segments, colors, and skips deleted items")
    def test_import_preserves_all_and_skips_deleted(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
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

        with allure.step("Verify segments with correct positions"):
            segments = segment_repo.get_all()
            assert len(segments) == 1, f"Expected 1 segment, got {len(segments)}"

            seg = segments[0]
            assert seg.position.start == 12
            assert seg.position.end == 17
            assert seg.selected_text == "happy"

        with allure.step("Verify code colors"):
            codes = code_repo.get_all()
            positive = next((c for c in codes if c.name == "Positive"), None)
            assert positive is not None
            assert positive.color.to_hex().lower() == "#00ff00"

        with allure.step("Verify deleted source skipped"):
            sources = source_repo.get_all()
            source_names = {s.name for s in sources}
            assert "deleted.txt" not in source_names

        with allure.step("Verify deleted code skipped"):
            code_names = {c.name for c in codes}
            assert "Deleted" not in code_names
            assert len(codes) == 2  # Only Positive and Learning


# =============================================================================
# Deep Import Verification: CSV
# =============================================================================


@allure.story("QC-039.06 Import Survey CSV")
class TestCsvDeepImport:
    @allure.title("Import preserves ALL attribute columns for every case")
    def test_import_all_attributes(self, case_repo, event_bus, tmp_path):
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand

        csv_file = tmp_path / "survey.csv"
        csv_file.write_text(
            "Name,Age,Gender,City,Score\n"
            "Alice,30,F,Boston,85\n"
            "Bob,25,M,Denver,92\n"
            "Carol,28,F,Austin,78\n"
        )

        import_survey_csv(
            command=ImportSurveyCSVCommand(source_path=str(csv_file)),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify all 3 cases created"):
            cases = case_repo.get_all()
            assert len(cases) == 3

        with allure.step("Verify Alice has ALL attributes"):
            alice = case_repo.get_by_name("Alice")
            assert alice.get_attribute("Age").value == "30"
            assert alice.get_attribute("Gender").value == "F"
            assert alice.get_attribute("City").value == "Boston"
            assert alice.get_attribute("Score").value == "85"

        with allure.step("Verify Bob has ALL attributes"):
            bob = case_repo.get_by_name("Bob")
            assert bob.get_attribute("Age").value == "25"
            assert bob.get_attribute("Gender").value == "M"
            assert bob.get_attribute("City").value == "Denver"
            assert bob.get_attribute("Score").value == "92"

        with allure.step("Verify Carol has ALL attributes"):
            carol = case_repo.get_by_name("Carol")
            assert carol.get_attribute("Age").value == "28"
            assert carol.get_attribute("Gender").value == "F"
            assert carol.get_attribute("City").value == "Austin"
            assert carol.get_attribute("Score").value == "78"


# =============================================================================
# Import -> ViewModel Query (data visible on screen)
# =============================================================================


@allure.story("QC-039 Import to Screen Verification")
class TestImportVisibleOnScreen:
    @allure.title("Imported codes visible via ViewModel after import")
    def test_imported_codes_visible_via_viewmodel(
        self,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_code_list import (
            import_code_list,
        )
        from src.contexts.exchange.core.commands import ImportCodeListCommand

        code_file = tmp_path / "codes.txt"
        code_file.write_text("Emotions\n  Joy\n  Anger\n  Sadness\nThemes\n  Growth\n")

        with allure.step("Import code list"):
            result = import_code_list(
                command=ImportCodeListCommand(source_path=str(code_file)),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )
            assert result.is_success

        with allure.step(
            "Verify codes available via repository (as ViewModel would query)"
        ):
            codes = code_repo.get_all()
            code_names = {c.name for c in codes}
            assert code_names == {"Joy", "Anger", "Sadness", "Growth"}

        with allure.step("Verify categories available"):
            categories = category_repo.get_all()
            cat_names = {c.name for c in categories}
            assert "Emotions" in cat_names
            assert "Themes" in cat_names

        with allure.step("Verify code-category relationships"):
            emotions_cat = next(c for c in categories if c.name == "Emotions")
            joy = next(c for c in codes if c.name == "Joy")
            anger = next(c for c in codes if c.name == "Anger")
            sadness = next(c for c in codes if c.name == "Sadness")
            assert joy.category_id == emotions_cat.id
            assert anger.category_id == emotions_cat.id
            assert sadness.category_id == emotions_cat.id

    @allure.title("Imported REFI-QDA data visible via source repository")
    def test_refi_qda_data_visible_via_repos(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import (
            import_refi_qda,
        )
        from src.contexts.exchange.core.commands import ImportRefiQdaCommand

        qdpx = _make_qdpx(
            tmp_path,
            REFI_QDA_XML,
            {"Sources/interview.txt": "I felt happy and sad today."},
        )

        import_refi_qda(
            command=ImportRefiQdaCommand(source_path=str(qdpx)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify source with text available for coding screen"):
            sources = source_repo.get_all()
            interview = next(s for s in sources if s.name == "interview.txt")
            assert interview.fulltext == "I felt happy and sad today."
            assert interview.source_type == SourceType.TEXT

        with allure.step("Verify segments linkable to source and code"):
            segments = segment_repo.get_all()
            assert len(segments) >= 2

            codes = code_repo.get_all()
            code_ids = {c.id for c in codes}

            for seg in segments:
                assert seg.source_id == interview.id, "Segment not linked to source"
                assert seg.code_id in code_ids, "Segment code_id not in imported codes"

    @allure.title("Imported CSV cases with attributes visible for case manager")
    def test_csv_cases_visible_for_case_manager(
        self,
        case_repo,
        event_bus,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.import_survey_csv import (
            import_survey_csv,
        )
        from src.contexts.exchange.core.commands import ImportSurveyCSVCommand

        csv_file = tmp_path / "participants.csv"
        csv_file.write_text(
            "Name,Role,Experience\nDr. Smith,Researcher,15\nJane Doe,Student,2\n"
        )

        import_survey_csv(
            command=ImportSurveyCSVCommand(source_path=str(csv_file)),
            case_repo=case_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify cases queryable as CaseManager would"):
            all_cases = case_repo.get_all()
            assert len(all_cases) == 2

            smith = case_repo.get_by_name("Dr. Smith")
            assert smith is not None
            assert smith.get_attribute("Role").value == "Researcher"
            assert smith.get_attribute("Experience").value == "15"

            jane = case_repo.get_by_name("Jane Doe")
            assert jane is not None
            assert jane.get_attribute("Role").value == "Student"
            assert jane.get_attribute("Experience").value == "2"


# =============================================================================
# Export Content Verification
# =============================================================================


@allure.story("QC-039.01 Export REFI-QDA Project")
class TestRefiQdaExportContent:
    @allure.title("Exported QDPX contains segments with correct positions")
    def test_export_contains_segments(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
    ):
        import xml.etree.ElementTree as ET

        source = Source(
            id=SourceId.new(),
            name="doc.txt",
            fulltext="I felt very happy about learning.",
            source_type=SourceType.TEXT,
        )
        source_repo.save(source)

        code = Code(id=CodeId.new(), name="Positive", color=Color.from_hex("#00FF00"))
        code_repo.save(code)

        seg = TextSegment(
            id=SegmentId.new(),
            source_id=source.id,
            code_id=code.id,
            position=TextPosition(start=12, end=17),
            selected_text="happy",
        )
        segment_repo.save(seg)

        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand

        output_path = tmp_path / "project.qdpx"
        export_refi_qda(
            command=ExportRefiQdaCommand(output_path=str(output_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Parse exported XML and verify segment positions"):
            with zipfile.ZipFile(output_path) as zf:
                xml_str = zf.read("project.qde").decode("utf-8")

            ns = {"qda": "urn:QDA-XML:project:1.0"}
            root = ET.fromstring(xml_str)

            codings = root.findall(".//qda:Coding", ns)
            assert len(codings) >= 1, "No Coding elements found in XML"

            ranges = root.findall(".//qda:TextRange", ns)
            assert len(ranges) >= 1, "No TextRange elements found"

            range_elem = ranges[0]
            assert range_elem.get("start") == "12"
            assert range_elem.get("end") == "17"

    @allure.title("Exported QDPX includes source file in ZIP")
    def test_export_includes_source_file(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
    ):
        source = Source(
            id=SourceId.new(),
            name="interview.txt",
            fulltext="This is the interview content.",
            source_type=SourceType.TEXT,
        )
        source_repo.save(source)

        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand

        output_path = tmp_path / "project.qdpx"
        export_refi_qda(
            command=ExportRefiQdaCommand(output_path=str(output_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with (
            allure.step("Verify source file in ZIP"),
            zipfile.ZipFile(output_path) as zf,
        ):
            names = zf.namelist()
            source_files = [n for n in names if n.startswith("Sources/")]
            assert len(source_files) >= 1, f"No source files in ZIP: {names}"
