"""
Exchange Infra: REFI-QDA Reader Tests (TDD - RED phase)

Tests for parsing REFI-QDA .qdpx archives.
"""

from __future__ import annotations

import zipfile


def _make_qdpx(tmp_path, xml_content: str, source_files: dict[str, str] | None = None):
    """Helper to create a .qdpx file with given XML and optional source files."""
    qdpx_path = tmp_path / "test.qdpx"
    with zipfile.ZipFile(qdpx_path, "w") as zf:
        zf.writestr("project.qde", xml_content)
        if source_files:
            for name, content in source_files.items():
                zf.writestr(name, content)
    return qdpx_path


BASIC_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="TestProject">
  <CodeBook>
    <Codes>
      <Code guid="c1" name="Joy" isCodable="true" color="#00ff00"/>
      <Code guid="c2" name="Anger" isCodable="true" color="#ff0000"/>
    </Codes>
  </CodeBook>
  <Sources>
    <TextSource guid="s1" name="interview.txt" plainTextPath="Sources/interview.txt">
      <PlainTextContent>I felt happy today.</PlainTextContent>
    </TextSource>
  </Sources>
  <Coding guid="cod1">
    <CodeRef targetGUID="c1"/>
    <TextRange start="7" end="12" sourceGUID="s1"/>
  </Coding>
</Project>
"""


class TestRefiQdaReader:
    def test_parse_project_name(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        qdpx = _make_qdpx(
            tmp_path, BASIC_XML, {"Sources/interview.txt": "I felt happy today."}
        )
        result = read_refi_qda(qdpx)

        assert result.project_name == "TestProject"

    def test_parse_codes(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        qdpx = _make_qdpx(
            tmp_path, BASIC_XML, {"Sources/interview.txt": "I felt happy today."}
        )
        result = read_refi_qda(qdpx)

        assert len(result.codes) == 2
        code_names = {c.name for c in result.codes}
        assert "Joy" in code_names
        assert "Anger" in code_names

    def test_parse_sources(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        qdpx = _make_qdpx(
            tmp_path, BASIC_XML, {"Sources/interview.txt": "I felt happy today."}
        )
        result = read_refi_qda(qdpx)

        assert len(result.sources) == 1
        assert result.sources[0].name == "interview.txt"
        assert result.sources[0].fulltext == "I felt happy today."

    def test_parse_codings(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        qdpx = _make_qdpx(
            tmp_path, BASIC_XML, {"Sources/interview.txt": "I felt happy today."}
        )
        result = read_refi_qda(qdpx)

        assert len(result.codings) == 1
        coding = result.codings[0]
        assert coding.code_guid == "c1"
        assert coding.source_guid == "s1"
        assert coding.start == 7
        assert coding.end == 12

    def test_parse_code_colors(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        qdpx = _make_qdpx(
            tmp_path, BASIC_XML, {"Sources/interview.txt": "I felt happy today."}
        )
        result = read_refi_qda(qdpx)

        joy = next(c for c in result.codes if c.name == "Joy")
        assert joy.color == "#00ff00"

    def test_parse_nested_categories(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_reader import read_refi_qda

        xml = """\
<?xml version="1.0" encoding="utf-8"?>
<Project xmlns="urn:QDA-XML:project:1.0" name="Test">
  <CodeBook>
    <Codes>
      <Code guid="cat1" name="Emotions" isCodable="false">
        <Code guid="c1" name="Joy" isCodable="true" color="#00ff00"/>
      </Code>
    </Codes>
  </CodeBook>
  <Sources/>
</Project>
"""
        qdpx = _make_qdpx(tmp_path, xml)
        result = read_refi_qda(qdpx)

        assert len(result.categories) == 1
        assert result.categories[0].name == "Emotions"
        assert len(result.codes) == 1
        joy = result.codes[0]
        assert joy.name == "Joy"
        assert joy.category_guid == "cat1"
