"""
QC-039.04: Export Codebook - E2E Tests

TDD: Tests written FIRST, before implementation.

Tests verify codebook export produces a document containing
all codes, categories, and optionally memos.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Category, Code, Color
from src.shared.common.types import CategoryId, CodeId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def codes_and_categories(code_repo, category_repo):
    """Seed codes and categories for codebook export tests."""
    # Create categories
    cat_emotions = Category(
        id=CategoryId.new(),
        name="Emotions",
        memo="Codes related to emotional responses",
    )
    cat_actions = Category(
        id=CategoryId.new(),
        name="Actions",
        memo="Codes related to participant actions",
    )
    category_repo.save(cat_emotions)
    category_repo.save(cat_actions)

    # Create codes
    code_joy = Code(
        id=CodeId.new(),
        name="Joy",
        color=Color.from_hex("#00FF00"),
        memo="Positive emotional response",
        category_id=cat_emotions.id,
    )
    code_anger = Code(
        id=CodeId.new(),
        name="Anger",
        color=Color.from_hex("#FF0000"),
        memo="Negative emotional response",
        category_id=cat_emotions.id,
    )
    code_helping = Code(
        id=CodeId.new(),
        name="Helping",
        color=Color.from_hex("#0000FF"),
        category_id=cat_actions.id,
    )
    code_uncategorized = Code(
        id=CodeId.new(),
        name="Misc",
        color=Color.from_hex("#999999"),
    )
    code_repo.save(code_joy)
    code_repo.save(code_anger)
    code_repo.save(code_helping)
    code_repo.save(code_uncategorized)

    return {
        "categories": [cat_emotions, cat_actions],
        "codes": [code_joy, code_anger, code_helping, code_uncategorized],
    }


# =============================================================================
# QC-039.04: Export Codebook
# =============================================================================


@allure.story("QC-039.04 Export Codebook")
class TestExportCodebook:
    @allure.title("AC #1: I can export codebook as document (ODT)")
    def test_ac1_export_codebook_creates_file(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Export codebook produces a file at the specified path."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        output_path = tmp_path / "codebook.txt"

        with allure.step("Export codebook"):
            result = export_codebook(
                command=ExportCodebookCommand(
                    output_path=str(output_path),
                    include_memos=True,
                ),
                code_repo=code_repo,
                category_repo=category_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Export failed: {result.error}"

        with allure.step("Verify file created"):
            assert output_path.exists()
            content = output_path.read_text()
            assert len(content) > 0

    @allure.title("AC #2: Export includes code names and descriptions")
    def test_ac2_export_includes_code_names(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Exported codebook contains all code names."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        output_path = tmp_path / "codebook.txt"

        export_codebook(
            command=ExportCodebookCommand(
                output_path=str(output_path),
                include_memos=False,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify all code names present"):
            content = output_path.read_text()
            for code in codes_and_categories["codes"]:
                assert code.name in content, f"Code '{code.name}' not found in export"

        with allure.step("Verify category names present"):
            for cat in codes_and_categories["categories"]:
                assert cat.name in content, f"Category '{cat.name}' not found in export"

    @allure.title("AC #3: Export can include memos")
    def test_ac3_export_includes_memos(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Exported codebook includes memos when requested."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        output_with_memos = tmp_path / "with_memos.txt"
        output_without_memos = tmp_path / "without_memos.txt"

        with allure.step("Export with memos"):
            export_codebook(
                command=ExportCodebookCommand(
                    output_path=str(output_with_memos),
                    include_memos=True,
                ),
                code_repo=code_repo,
                category_repo=category_repo,
                event_bus=event_bus,
            )

        with allure.step("Export without memos"):
            export_codebook(
                command=ExportCodebookCommand(
                    output_path=str(output_without_memos),
                    include_memos=False,
                ),
                code_repo=code_repo,
                category_repo=category_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify memos present in memo export"):
            content_with = output_with_memos.read_text()
            assert "Positive emotional response" in content_with
            assert "Codes related to emotional responses" in content_with

        with allure.step("Verify memos absent in no-memo export"):
            content_without = output_without_memos.read_text()
            assert "Positive emotional response" not in content_without

    @allure.title("Export publishes CodebookExported event")
    def test_export_publishes_event(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Successful export publishes a CodebookExported domain event."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand
        from src.contexts.exchange.core.events import CodebookExported

        published_events = []
        event_bus.subscribe("exchange.codebook_exported", published_events.append)

        export_codebook(
            command=ExportCodebookCommand(
                output_path=str(tmp_path / "codebook.txt"),
                include_memos=False,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify event published"):
            assert len(published_events) == 1
            event = published_events[0]
            assert isinstance(event, CodebookExported)
            assert event.code_count == 4
            assert event.category_count == 2

    @allure.title("Export fails gracefully with no codes")
    def test_export_fails_with_no_codes(
        self, code_repo, category_repo, event_bus, tmp_path
    ):
        """Export fails with helpful error when project has no codes."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        result = export_codebook(
            command=ExportCodebookCommand(
                output_path=str(tmp_path / "empty.txt"),
                include_memos=False,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify failure with helpful error"):
            assert result.is_failure
            assert result.error_code == "CODEBOOK_NOT_EXPORTED/NO_CODES"
            assert len(result.suggestions) > 0

    @allure.title("Export includes color information")
    def test_export_includes_colors(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Exported codebook includes code colors for reference."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        output_path = tmp_path / "codebook.txt"

        export_codebook(
            command=ExportCodebookCommand(
                output_path=str(output_path),
                include_memos=False,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify colors present"):
            content = output_path.read_text()
            # Colors should appear as hex
            assert "#00ff00" in content.lower() or "#00FF00" in content

    @allure.title("Export groups codes under their categories")
    def test_export_groups_codes_by_category(
        self, code_repo, category_repo, event_bus, codes_and_categories, tmp_path
    ):
        """Exported codebook organizes codes under category headings."""
        from src.contexts.exchange.core.commandHandlers.export_codebook import (
            export_codebook,
        )
        from src.contexts.exchange.core.commands import ExportCodebookCommand

        output_path = tmp_path / "codebook.txt"

        export_codebook(
            command=ExportCodebookCommand(
                output_path=str(output_path),
                include_memos=True,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            event_bus=event_bus,
        )

        with allure.step("Verify category grouping"):
            content = output_path.read_text()
            # Category "Emotions" should appear before its codes
            emotions_pos = content.index("Emotions")
            joy_pos = content.index("Joy")
            anger_pos = content.index("Anger")
            assert emotions_pos < joy_pos
            assert emotions_pos < anger_pos
