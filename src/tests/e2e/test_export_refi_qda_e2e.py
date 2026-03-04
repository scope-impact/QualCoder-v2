"""
QC-039.01: Export REFI-QDA Project - E2E Tests

TDD: Tests written FIRST, before implementation.
"""

from __future__ import annotations

import zipfile

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
def project_data(source_repo, code_repo, segment_repo):
    """Seed a complete project for export."""
    source = Source(
        id=SourceId.new(),
        name="interview_01.txt",
        fulltext="I felt very happy about the learning experience.",
        source_type=SourceType.TEXT,
    )
    source_repo.save(source)

    code1 = Code(id=CodeId.new(), name="Positive", color=Color.from_hex("#00FF00"))
    code2 = Code(id=CodeId.new(), name="Learning", color=Color.from_hex("#0000FF"))
    code_repo.save(code1)
    code_repo.save(code2)

    seg = TextSegment(
        id=SegmentId.new(),
        source_id=source.id,
        code_id=code1.id,
        position=TextPosition(start=12, end=17),
        selected_text="happy",
    )
    segment_repo.save(seg)

    return {"sources": [source], "codes": [code1, code2], "segments": [seg]}


@allure.story("QC-039.01 Export REFI-QDA Project")
class TestExportRefiQDA:
    @allure.title("AC #1: I can export project as .qdpx file")
    def test_ac1_export_creates_qdpx(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        project_data,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand

        output_path = tmp_path / "project.qdpx"

        with allure.step("Export project"):
            result = export_refi_qda(
                command=ExportRefiQdaCommand(
                    output_path=str(output_path),
                    project_name="Test Project",
                ),
                source_repo=source_repo,
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Export failed: {result.error}"

        with allure.step("Verify .qdpx is a valid ZIP"):
            assert output_path.exists()
            assert zipfile.is_zipfile(output_path)

    @allure.title("AC #2: QDPX contains project.qde with codes and sources")
    def test_ac2_qdpx_contains_project_data(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        project_data,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand

        output_path = tmp_path / "project.qdpx"

        export_refi_qda(
            command=ExportRefiQdaCommand(
                output_path=str(output_path),
                project_name="Test Project",
            ),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify XML content"):
            with zipfile.ZipFile(output_path) as zf:
                xml_content = zf.read("project.qde").decode("utf-8")

            assert "Positive" in xml_content
            assert "Learning" in xml_content
            assert "interview_01.txt" in xml_content

    @allure.title("Export publishes RefiQdaExported event")
    def test_publishes_event(
        self,
        source_repo,
        code_repo,
        category_repo,
        segment_repo,
        event_bus,
        project_data,
        tmp_path,
    ):
        from src.contexts.exchange.core.commandHandlers.export_refi_qda import (
            export_refi_qda,
        )
        from src.contexts.exchange.core.commands import ExportRefiQdaCommand
        from src.contexts.exchange.core.events import RefiQdaExported

        published = []
        event_bus.subscribe("exchange.refi_qda_exported", published.append)

        export_refi_qda(
            command=ExportRefiQdaCommand(
                output_path=str(tmp_path / "project.qdpx"),
                project_name="Test",
            ),
            source_repo=source_repo,
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify event"):
            assert len(published) == 1
            event = published[0]
            assert isinstance(event, RefiQdaExported)
            assert event.code_count == 2
            assert event.source_count == 1
