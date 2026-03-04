"""
QC-039.05: Export Coded Text as HTML - E2E Tests

TDD: Tests written FIRST, before implementation.

Tests verify exporting coded text produces an HTML file with
code highlights and source grouping.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color, TextPosition, TextSegment
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.types import CodeId, SegmentId, SourceId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


@pytest.fixture
def coded_sources(source_repo, code_repo, segment_repo):
    """Seed sources with coded segments."""
    source = Source(
        id=SourceId.new(),
        name="interview_01.txt",
        fulltext="I felt very happy about the learning experience. It was great.",
        source_type=SourceType.TEXT,
    )
    source_repo.save(source)

    code_pos = Code(id=CodeId.new(), name="Positive", color=Color.from_hex("#00FF00"))
    code_learn = Code(id=CodeId.new(), name="Learning", color=Color.from_hex("#0000FF"))
    code_repo.save(code_pos)
    code_repo.save(code_learn)

    seg1 = TextSegment(
        id=SegmentId.new(),
        source_id=source.id,
        code_id=code_pos.id,
        position=TextPosition(start=12, end=17),
        selected_text="happy",
    )
    seg2 = TextSegment(
        id=SegmentId.new(),
        source_id=source.id,
        code_id=code_learn.id,
        position=TextPosition(start=28, end=47),
        selected_text="learning experience",
    )
    segment_repo.save(seg1)
    segment_repo.save(seg2)

    return {
        "sources": [source],
        "codes": [code_pos, code_learn],
        "segments": [seg1, seg2],
    }


@allure.story("QC-039.05 Export Coded Text as HTML")
class TestExportCodedHTML:
    @allure.title("AC #1: I can export coded text as HTML file")
    def test_ac1_export_creates_html(
        self, source_repo, code_repo, segment_repo, event_bus, coded_sources, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand

        output_path = tmp_path / "coded.html"

        with allure.step("Export coded HTML"):
            result = export_coded_html(
                command=ExportCodedHTMLCommand(output_path=str(output_path)),
                source_repo=source_repo,
                code_repo=code_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Export failed: {result.error}"

        with allure.step("Verify HTML file created"):
            assert output_path.exists()
            content = output_path.read_text()
            assert "<html" in content

    @allure.title("AC #2: HTML includes source name and coded text")
    def test_ac2_html_includes_content(
        self, source_repo, code_repo, segment_repo, event_bus, coded_sources, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand

        output_path = tmp_path / "coded.html"

        export_coded_html(
            command=ExportCodedHTMLCommand(output_path=str(output_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify source name and text present"):
            content = output_path.read_text()
            assert "interview_01.txt" in content
            assert "happy" in content
            assert "learning experience" in content

    @allure.title("AC #3: HTML highlights coded segments with colors")
    def test_ac3_html_highlights_segments(
        self, source_repo, code_repo, segment_repo, event_bus, coded_sources, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand

        output_path = tmp_path / "coded.html"

        export_coded_html(
            command=ExportCodedHTMLCommand(output_path=str(output_path)),
            source_repo=source_repo,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify highlight spans present"):
            content = output_path.read_text()
            assert "<span" in content
            # Code colors
            assert "#00ff00" in content.lower() or "#00FF00" in content
            # Code names in title attributes
            assert "Positive" in content
            assert "Learning" in content

    @allure.title("Export publishes CodedHTMLExported event")
    def test_publishes_event(
        self, source_repo, code_repo, segment_repo, event_bus, coded_sources, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand
        from src.contexts.exchange.core.events import CodedHTMLExported

        published = []
        event_bus.subscribe("exchange.coded_html_exported", published.append)

        export_coded_html(
            command=ExportCodedHTMLCommand(output_path=str(tmp_path / "out.html")),
            source_repo=source_repo,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify event"):
            assert len(published) == 1
            event = published[0]
            assert isinstance(event, CodedHTMLExported)
            assert event.source_count == 1
            assert event.segment_count == 2

    @allure.title("Export fails with no text sources")
    def test_fails_no_sources(
        self, source_repo, code_repo, segment_repo, event_bus, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.export_coded_html import (
            export_coded_html,
        )
        from src.contexts.exchange.core.commands import ExportCodedHTMLCommand

        result = export_coded_html(
            command=ExportCodedHTMLCommand(output_path=str(tmp_path / "out.html")),
            source_repo=source_repo,
            code_repo=code_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify failure"):
            assert result.is_failure
            assert "NO_SOURCES" in result.error_code
