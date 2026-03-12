"""
Exchange Infra: REFI-QDA Writer Tests

Tests for generating REFI-QDA (.qdpx) ZIP archives with project.qde XML.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color, TextPosition, TextSegment
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.types import CodeId, SegmentId, SourceId

pytestmark = [pytest.mark.unit]


@allure.epic("QualCoder v2")
@allure.feature("QC-039 Import Export Formats")
@allure.story("QC-036.02 Export REFI-QDA")
class TestRefiQdaWriter:
    """Tests for REFI-QDA .qdpx writer."""

    def _make_code(self, name: str, color: str = "#FF0000"):
        return Code(id=CodeId.new(), name=name, color=Color.from_hex(color))

    def _make_source(self, name: str, fulltext: str):
        return Source(
            id=SourceId.new(),
            name=name,
            fulltext=fulltext,
            source_type=SourceType.TEXT,
        )

    def _make_segment(self, source_id, code_id, start, end, text):
        return TextSegment(
            id=SegmentId.new(),
            source_id=source_id,
            code_id=code_id,
            position=TextPosition(start=start, end=end),
            selected_text=text,
        )

    @allure.title("Creates valid ZIP with project.qde, codes, sources, and codings")
    def test_creates_valid_archive_with_content(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        source = self._make_source("doc.txt", "I felt happy today.")
        code = self._make_code("Joy", "#00FF00")
        seg = self._make_segment(source.id, code.id, 7, 12, "happy")

        output = tmp_path / "project.qdpx"
        write_refi_qda(
            codes=[code],
            categories=[],
            sources=[source],
            segments=[seg],
            output_path=output,
            project_name="MyProject",
        )

        assert output.exists()
        assert zipfile.is_zipfile(output)

        with zipfile.ZipFile(output) as zf:
            assert "project.qde" in zf.namelist()
            xml_content = zf.read("project.qde")
            xml_str = xml_content.decode("utf-8")
            names = zf.namelist()

        root = ET.fromstring(xml_content)
        assert root.tag.endswith("Project") or "Project" in root.tag
        assert root.get("name") == "MyProject"
        assert "Joy" in xml_str
        assert "doc.txt" in xml_str
        source_files = [n for n in names if n.startswith("Sources/")]
        assert len(source_files) >= 1
        assert "Coding" in xml_str or "coding" in xml_str

    @allure.title("Empty export produces valid archive")
    def test_empty_export_valid(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        output = tmp_path / "project.qdpx"
        write_refi_qda(
            codes=[],
            categories=[],
            sources=[],
            segments=[],
            output_path=output,
            project_name="Empty",
        )

        assert output.exists()
        with zipfile.ZipFile(output) as zf:
            assert "project.qde" in zf.namelist()
