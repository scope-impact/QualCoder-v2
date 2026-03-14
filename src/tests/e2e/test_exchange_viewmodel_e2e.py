"""
Exchange ViewModel - E2E Tests

Tests for the ExchangeViewModel which coordinates all import/export operations,
and for the FileManagerScreen integration with exchange actions.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color
from src.shared.common.types import CodeId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


@pytest.fixture
def exchange_vm(
    code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus
):
    from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator
    from src.contexts.exchange.presentation.viewmodels.exchange_viewmodel import (
        ExchangeViewModel,
    )

    coordinator = ExchangeCoordinator(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
        source_repo=source_repo,
        case_repo=case_repo,
        event_bus=event_bus,
    )
    return ExchangeViewModel(coordinator=coordinator)


@pytest.fixture
def file_manager_screen(qapp, exchange_vm):
    """FileManagerScreen with exchange viewmodel wired."""
    from src.contexts.sources.presentation import FileManagerScreen

    screen = FileManagerScreen()
    screen.set_exchange_viewmodel(exchange_vm)
    return screen


@allure.story("QC-039 Import Export Formats")
class TestExchangeViewModel:
    @allure.title("Export codebook succeeds and fails gracefully when no codes")
    def test_export_codebook_success_and_failure(
        self, exchange_vm, code_repo, tmp_path
    ):
        # Fail when no codes
        result = exchange_vm.export_codebook(str(tmp_path / "codebook.txt"))
        assert result is False
        assert exchange_vm.last_error is not None

        # Succeed after adding code (also tests error clearing)
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)
        result = exchange_vm.export_codebook(str(tmp_path / "codebook.txt"))
        assert result is True
        assert exchange_vm.last_error is None
        assert (tmp_path / "codebook.txt").exists()

    @allure.title("Import code list and CSV via ViewModel")
    def test_import_code_list_and_csv(
        self, exchange_vm, code_repo, case_repo, tmp_path
    ):
        code_file = tmp_path / "codes.txt"
        code_file.write_text("Joy\nAnger\n")
        result = exchange_vm.import_code_list(str(code_file))
        assert result is True
        codes = code_repo.get_all()
        assert len(codes) == 2

        csv_file = tmp_path / "survey.csv"
        csv_file.write_text("Name,Age\nAlice,30\nBob,25\n")
        result = exchange_vm.import_survey_csv(str(csv_file))
        assert result is True
        cases = case_repo.get_all()
        assert len(cases) == 2

    @allure.title("Export REFI-QDA via ViewModel")
    def test_export_refi_qda(self, exchange_vm, tmp_path):
        result = exchange_vm.export_refi_qda(str(tmp_path / "project.qdpx"))
        assert result is True
        assert (tmp_path / "project.qdpx").exists()


@allure.story("QC-039 Import Export Formats")
class TestFileManagerExchangeIntegration:
    @allure.title(
        "FileManagerScreen wired with exchange VM and has import/export menus"
    )
    def test_screen_wiring_and_menus(self, file_manager_screen, exchange_vm):
        assert file_manager_screen._exchange_vm is exchange_vm

        toolbar = file_manager_screen._page.toolbar

        # Import menu
        import_menu = toolbar._import_btn.menu()
        assert import_menu is not None
        import_actions = [
            a.text() for a in import_menu.actions() if not a.isSeparator()
        ]
        assert "Source Files..." in import_actions
        assert "Code List (.txt)..." in import_actions
        assert "Survey CSV (.csv)..." in import_actions
        assert "REFI-QDA Project (.qdpx)..." in import_actions
        assert "RQDA Project (.rqda)..." in import_actions

        # Export menu
        export_menu = toolbar._export_btn.menu()
        assert export_menu is not None
        export_actions = [
            a.text() for a in export_menu.actions() if not a.isSeparator()
        ]
        assert "Selected Sources..." in export_actions
        assert "Codebook (.txt)..." in export_actions
        assert "Coded HTML (.html)..." in export_actions
        assert "REFI-QDA Project (.qdpx)..." in export_actions

    @allure.title("Screenshot: Import and Export dropdown menus")
    def test_screenshot_import_and_export_menus(self, file_manager_screen):
        from PySide6.QtWidgets import QApplication

        from src.tests.e2e.utils.doc_screenshot import DocScreenshot

        file_manager_screen.resize(1200, 800)
        file_manager_screen.show()

        toolbar = file_manager_screen._page.toolbar

        # Import menu screenshot
        import_menu = toolbar._import_btn.menu()
        import_menu.popup(
            toolbar._import_btn.mapToGlobal(toolbar._import_btn.rect().bottomLeft())
        )
        QApplication.processEvents()
        DocScreenshot.capture(
            file_manager_screen, "exchange-import-menu", attach_to_allure=True
        )
        import_menu.close()

        # Export menu screenshot
        export_menu = toolbar._export_btn.menu()
        export_menu.popup(
            toolbar._export_btn.mapToGlobal(toolbar._export_btn.rect().bottomLeft())
        )
        QApplication.processEvents()
        DocScreenshot.capture(
            file_manager_screen, "exchange-export-menu", attach_to_allure=True
        )
        export_menu.close()
