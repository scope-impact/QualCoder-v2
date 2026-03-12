"""
Exchange Infra: HTML Writer Tests

Tests for generating coded HTML from sources and segments.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color, TextPosition, TextSegment
from src.shared.common.types import CodeId, SegmentId, SourceId

pytestmark = [pytest.mark.unit]


@allure.epic("QualCoder v2")
@allure.feature("QC-039 Import Export Formats")
@allure.story("QC-036.08 Export HTML")
class TestHTMLWriter:
    """Tests for coded text HTML writer."""

    def _make_code(self, name: str, color: str = "#FF0000"):
        return Code(id=CodeId.new(), name=name, color=Color.from_hex(color))

    def _make_segment(self, source_id, code_id, start, end, text):
        return TextSegment(
            id=SegmentId.new(),
            source_id=source_id,
            code_id=code_id,
            position=TextPosition(start=start, end=end),
            selected_text=text,
        )

    @allure.title("Writes HTML with sources, segments, highlights, and escaped special chars")
    def test_write_html_with_sources_highlights_and_escaping(self, tmp_path):
        from src.contexts.exchange.infra.html_writer import write_coded_html

        sid1 = SourceId.new()
        sid2 = SourceId.new()
        sid3 = SourceId.new()
        code = self._make_code("Joy", "#00FF00")
        code2 = self._make_code("Important", "#FFAA00")

        sources_data = [
            {
                "name": "interview.txt",
                "fulltext": "I felt happy today.",
                "source_id": sid1,
                "segments": [
                    self._make_segment(sid1, code.id, 7, 12, "happy"),
                ],
                "codes": {code.id.value: code},
            },
            {
                "name": "doc2.txt",
                "fulltext": "Second document text.",
                "source_id": sid2,
                "segments": [],
                "codes": {},
            },
            {
                "name": "special.txt",
                "fulltext": "Use <html> & 'quotes'",
                "source_id": sid3,
                "segments": [],
                "codes": {},
            },
        ]

        output_path = tmp_path / "coded.html"
        write_coded_html(sources_data, output_path)

        content = output_path.read_text()
        # Basic HTML structure
        assert "<html" in content
        assert "interview.txt" in content
        assert "happy" in content
        assert "#00ff00" in content.lower() or "00FF00" in content
        # Multiple sources
        assert "doc2.txt" in content
        # HTML escaping
        assert "&lt;html&gt;" in content
        assert "&amp;" in content

    @allure.title("Highlights segments with colored spans and code names")
    def test_write_html_highlights_segments(self, tmp_path):
        from src.contexts.exchange.infra.html_writer import write_coded_html

        sid = SourceId.new()
        code = self._make_code("Important", "#FFAA00")

        sources_data = [
            {
                "name": "test.txt",
                "fulltext": "This is important text here.",
                "source_id": sid,
                "segments": [
                    self._make_segment(sid, code.id, 8, 17, "important"),
                ],
                "codes": {code.id.value: code},
            },
        ]

        output_path = tmp_path / "coded.html"
        write_coded_html(sources_data, output_path)

        content = output_path.read_text()
        assert "<span" in content
        assert "Important" in content
