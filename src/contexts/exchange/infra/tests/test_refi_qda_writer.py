"""
Exchange Infra: REFI-QDA Writer Tests (TDD - RED phase)

Tests for generating REFI-QDA (.qdpx) ZIP archives with project.qde XML.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile

from src.contexts.coding.core.entities import Code, Color, TextPosition, TextSegment
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.types import CodeId, SegmentId, SourceId


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

    def test_creates_valid_zip(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        output = tmp_path / "project.qdpx"
        write_refi_qda(
            codes=[],
            categories=[],
            sources=[],
            segments=[],
            output_path=output,
            project_name="Test",
        )

        assert output.exists()
        assert zipfile.is_zipfile(output)

    def test_zip_contains_project_qde(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        output = tmp_path / "project.qdpx"
        write_refi_qda(
            codes=[],
            categories=[],
            sources=[],
            segments=[],
            output_path=output,
            project_name="Test",
        )

        with zipfile.ZipFile(output) as zf:
            assert "project.qde" in zf.namelist()

    def test_xml_has_project_root(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        output = tmp_path / "project.qdpx"
        write_refi_qda(
            codes=[],
            categories=[],
            sources=[],
            segments=[],
            output_path=output,
            project_name="MyProject",
        )

        with zipfile.ZipFile(output) as zf:
            xml_content = zf.read("project.qde")
        root = ET.fromstring(xml_content)
        assert root.tag.endswith("Project") or "Project" in root.tag
        assert root.get("name") == "MyProject"

    def test_xml_includes_codes(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        code = self._make_code("Joy", "#00FF00")
        output = tmp_path / "project.qdpx"

        write_refi_qda(
            codes=[code],
            categories=[],
            sources=[],
            segments=[],
            output_path=output,
            project_name="Test",
        )

        with zipfile.ZipFile(output) as zf:
            xml_content = zf.read("project.qde")
        xml_str = xml_content.decode("utf-8")
        assert "Joy" in xml_str

    def test_xml_includes_sources(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        source = self._make_source("interview.txt", "Hello world.")
        output = tmp_path / "project.qdpx"

        write_refi_qda(
            codes=[],
            categories=[],
            sources=[source],
            segments=[],
            output_path=output,
            project_name="Test",
        )

        with zipfile.ZipFile(output) as zf:
            xml_content = zf.read("project.qde")
        xml_str = xml_content.decode("utf-8")
        assert "interview.txt" in xml_str

    def test_xml_includes_codings(self, tmp_path):
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
            project_name="Test",
        )

        with zipfile.ZipFile(output) as zf:
            xml_content = zf.read("project.qde")
        xml_str = xml_content.decode("utf-8")
        # Should have coding reference
        assert "Coding" in xml_str or "coding" in xml_str

    def test_zip_includes_source_text_files(self, tmp_path):
        from src.contexts.exchange.infra.refi_qda_writer import write_refi_qda

        source = self._make_source("interview.txt", "Hello world.")
        output = tmp_path / "project.qdpx"

        write_refi_qda(
            codes=[],
            categories=[],
            sources=[source],
            segments=[],
            output_path=output,
            project_name="Test",
        )

        with zipfile.ZipFile(output) as zf:
            names = zf.namelist()
            # Source files should be in a sources/ directory
            source_files = [n for n in names if n.startswith("Sources/")]
            assert len(source_files) >= 1
