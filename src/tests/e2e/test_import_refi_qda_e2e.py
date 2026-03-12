"""
QC-039.02: Import REFI-QDA Project - E2E Tests

TDD: Tests written FIRST, before implementation.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


IMPORT_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="ImportTest">
  <CodeBook>
    <Codes>
      <Code guid="c1" name="Joy" isCodable="true" color="#00ff00"/>
      <Code guid="c2" name="Sadness" isCodable="true" color="#0000ff"/>
    </Codes>
  </CodeBook>
  <Sources>
    <TextSource guid="s1" name="doc.txt" plainTextPath="Sources/doc.txt">
      <PlainTextContent>I felt happy today.</PlainTextContent>
    </TextSource>
  </Sources>
  <Coding guid="cod1">
    <CodeRef targetGUID="c1"/>
    <TextRange start="7" end="12" sourceGUID="s1"/>
  </Coding>
</Project>
"""


@allure.story("QC-039.02 Import REFI-QDA Project")
class TestImportRefiQDA:
    @allure.title(
        "AC #1+#2+#3: Import QDPX creates codes, sources, and publishes event"
    )
    def test_import_qdpx_full(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        tmp_path,
        make_qdpx,
    ):
        from src.contexts.exchange.core.commandHandlers.import_refi_qda import (
            import_refi_qda,
        )
        from src.contexts.exchange.core.commands import ImportRefiQdaCommand
        from src.contexts.exchange.core.events import RefiQdaImported

        published = []
        event_bus.subscribe("exchange.refi_qda_imported", published.append)

        qdpx = make_qdpx(
            tmp_path, IMPORT_XML, {"Sources/doc.txt": "I felt happy today."}
        )

        with allure.step("Import QDPX"):
            result = import_refi_qda(
                command=ImportRefiQdaCommand(source_path=str(qdpx)),
                source_repo=source_repo,
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Import failed: {result.error}"

        with allure.step("Verify codes"):
            codes = code_repo.get_all()
            code_names = {c.name for c in codes}
            assert "Joy" in code_names
            assert "Sadness" in code_names

        with allure.step("Verify sources"):
            sources = source_repo.get_all()
            assert len(sources) >= 1
            assert any(s.name == "doc.txt" for s in sources)

        with allure.step("Verify event"):
            assert len(published) == 1
            event = published[0]
            assert isinstance(event, RefiQdaImported)
            assert event.codes_created == 2
            assert event.sources_created == 1

    @allure.title("Import fails with nonexistent file")
    def test_fails_nonexistent(
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

        result = import_refi_qda(
            command=ImportRefiQdaCommand(source_path=str(tmp_path / "missing.qdpx")),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        assert result.is_failure
        assert "FILE_NOT_FOUND" in result.error_code
