"""
Exchange Infra: HTML Writer Tests (TDD - RED phase)

Tests for generating coded HTML from sources and segments.
"""
from __future__ import annotations

import pytest

from src.contexts.coding.core.entities import Code, Color, TextPosition, TextSegment
from src.shared.common.types import CodeId, SegmentId, SourceId


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

    def test_write_basic_html(self, tmp_path):
        from src.contexts.exchange.infra.html_writer import write_coded_html

        source_id = SourceId.new()
        code = self._make_code("Joy", "#00FF00")

        sources_data = [
            {
                "name": "interview.txt",
                "fulltext": "I felt happy today.",
                "source_id": source_id,
                "segments": [
                    self._make_segment(source_id, code.id, 7, 12, "happy"),
                ],
                "codes": {code.id.value: code},
            }
        ]

        output_path = tmp_path / "coded.html"
        write_coded_html(sources_data, output_path)

        content = output_path.read_text()
        assert "<html" in content
        assert "interview.txt" in content
        assert "happy" in content
        assert "#00ff00" in content.lower() or "00FF00" in content

    def test_write_html_with_multiple_sources(self, tmp_path):
        from src.contexts.exchange.infra.html_writer import write_coded_html

        sid1 = SourceId.new()
        sid2 = SourceId.new()
        code = self._make_code("Theme", "#0000FF")

        sources_data = [
            {
                "name": "doc1.txt",
                "fulltext": "First document text.",
                "source_id": sid1,
                "segments": [],
                "codes": {},
            },
            {
                "name": "doc2.txt",
                "fulltext": "Second document text.",
                "source_id": sid2,
                "segments": [
                    self._make_segment(sid2, code.id, 0, 6, "Second"),
                ],
                "codes": {code.id.value: code},
            },
        ]

        output_path = tmp_path / "coded.html"
        write_coded_html(sources_data, output_path)

        content = output_path.read_text()
        assert "doc1.txt" in content
        assert "doc2.txt" in content

    def test_write_html_escapes_special_chars(self, tmp_path):
        from src.contexts.exchange.infra.html_writer import write_coded_html

        sid = SourceId.new()
        sources_data = [
            {
                "name": "test.txt",
                "fulltext": "Use <html> & 'quotes'",
                "source_id": sid,
                "segments": [],
                "codes": {},
            },
        ]

        output_path = tmp_path / "coded.html"
        write_coded_html(sources_data, output_path)

        content = output_path.read_text()
        assert "&lt;html&gt;" in content
        assert "&amp;" in content

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
        # The coded span should have a background color and title
        assert "<span" in content
        assert "Important" in content  # Code name should appear in title
