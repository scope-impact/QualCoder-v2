"""
QC-039.07: Import Code List - E2E Tests

TDD: Tests written FIRST, before implementation.

Tests verify importing a plain-text code list creates codes and
categories in the repository.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


@allure.story("QC-039.07 Import Code List")
class TestImportCodeList:
    @allure.title("AC #1: Import flat code list and publish CodeListImported event")
    def test_ac1_import_flat_code_list_with_event(
        self, code_repo, category_repo, segment_repo, event_bus, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.import_code_list import (
            import_code_list,
        )
        from src.contexts.exchange.core.commands import ImportCodeListCommand
        from src.contexts.exchange.core.events import CodeListImported

        published = []
        event_bus.subscribe("exchange.code_list_imported", published.append)

        code_list_file = tmp_path / "codes.txt"
        code_list_file.write_text("Joy\nAnger\nSadness\n")

        with allure.step("Import code list"):
            result = import_code_list(
                command=ImportCodeListCommand(source_path=str(code_list_file)),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify success"):
            assert result.is_success, f"Import failed: {result.error}"

        with allure.step("Verify codes created in repository"):
            codes = code_repo.get_all()
            code_names = {c.name for c in codes}
            assert "Joy" in code_names
            assert "Anger" in code_names
            assert "Sadness" in code_names

        with allure.step("Verify event"):
            assert len(published) == 1
            event = published[0]
            assert isinstance(event, CodeListImported)
            assert event.codes_created == 3

    @allure.title("AC #2+#3: Import with categories and skip duplicates")
    def test_ac2_ac3_categories_and_duplicates(
        self, code_repo, category_repo, segment_repo, event_bus, tmp_path
    ):
        from src.contexts.coding.core.entities import Code, Color
        from src.contexts.exchange.core.commandHandlers.import_code_list import (
            import_code_list,
        )
        from src.contexts.exchange.core.commands import ImportCodeListCommand
        from src.shared.common.types import CodeId

        with allure.step("Import indented code list with categories"):
            code_list_file = tmp_path / "codes.txt"
            code_list_file.write_text("Emotions\n  Joy\n  Anger\nActions\n  Helping\n")

            import_code_list(
                command=ImportCodeListCommand(source_path=str(code_list_file)),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )

        with allure.step("Verify categories created"):
            categories = category_repo.get_all()
            cat_names = {c.name for c in categories}
            assert "Emotions" in cat_names
            assert "Actions" in cat_names

        with allure.step("Verify codes belong to categories"):
            codes = code_repo.get_all()
            emotions_cat = next(c for c in categories if c.name == "Emotions")
            joy = next(c for c in codes if c.name == "Joy")
            assert joy.category_id == emotions_cat.id

        with allure.step("Import again with duplicate — Joy should not be duplicated"):
            # Pre-existing Joy code already exists from above import
            code_list_file2 = tmp_path / "codes2.txt"
            code_list_file2.write_text("Joy\nNewCode\n")

            result = import_code_list(
                command=ImportCodeListCommand(source_path=str(code_list_file2)),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )
            assert result.is_success

        with allure.step("Verify no duplicate Joy"):
            codes = code_repo.get_all()
            joy_codes = [c for c in codes if c.name == "Joy"]
            assert len(joy_codes) == 1

        with allure.step("Verify NewCode was added"):
            code_names = {c.name for c in codes}
            assert "NewCode" in code_names

    @allure.title("Import fails with empty or nonexistent file")
    def test_fails_invalid_input(
        self, code_repo, category_repo, segment_repo, event_bus, tmp_path
    ):
        from src.contexts.exchange.core.commandHandlers.import_code_list import (
            import_code_list,
        )
        from src.contexts.exchange.core.commands import ImportCodeListCommand

        with allure.step("Verify failure with empty file"):
            empty_file = tmp_path / "empty.txt"
            empty_file.write_text("")

            result = import_code_list(
                command=ImportCodeListCommand(source_path=str(empty_file)),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )
            assert result.is_failure
            assert result.error_code == "CODE_LIST_NOT_IMPORTED/EMPTY_LIST"

        with allure.step("Verify failure with nonexistent file"):
            result = import_code_list(
                command=ImportCodeListCommand(source_path=str(tmp_path / "missing.txt")),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
            )
            assert result.is_failure
            assert "FILE_NOT_FOUND" in result.error_code
