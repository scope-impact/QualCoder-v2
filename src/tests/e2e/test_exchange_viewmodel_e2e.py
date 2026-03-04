"""
Exchange ViewModel - E2E Tests

Tests for the ExchangeViewModel which coordinates all import/export operations,
and for the FileManagerScreen integration with exchange actions.
"""
from __future__ import annotations

import allure
import pytest

from src.contexts.coding.core.entities import Code, Color
from src.contexts.sources.core.entities import Source, SourceType
from src.shared.common.types import CodeId, SourceId

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-039 Import Export Formats"),
]


@pytest.fixture
def exchange_vm(code_repo, category_repo, segment_repo, source_repo, case_repo, event_bus):
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


@allure.story("QC-039 Exchange ViewModel")
class TestExchangeViewModel:

    @allure.title("Export codebook via ViewModel")
    def test_export_codebook(self, exchange_vm, code_repo, tmp_path):
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)

        result = exchange_vm.export_codebook(str(tmp_path / "codebook.txt"))

        assert result is True
        assert exchange_vm.last_error is None
        assert (tmp_path / "codebook.txt").exists()

    @allure.title("Export codebook fails gracefully when no codes")
    def test_export_codebook_no_codes(self, exchange_vm, tmp_path):
        result = exchange_vm.export_codebook(str(tmp_path / "codebook.txt"))

        assert result is False
        assert exchange_vm.last_error is not None

    @allure.title("Import code list via ViewModel")
    def test_import_code_list(self, exchange_vm, code_repo, tmp_path):
        code_file = tmp_path / "codes.txt"
        code_file.write_text("Joy\nAnger\n")

        result = exchange_vm.import_code_list(str(code_file))

        assert result is True
        codes = code_repo.get_all()
        assert len(codes) == 2

    @allure.title("Import CSV via ViewModel")
    def test_import_csv(self, exchange_vm, case_repo, tmp_path):
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

    @allure.title("ViewModel clears error on success")
    def test_clears_error_on_success(self, exchange_vm, code_repo, tmp_path):
        # First fail
        exchange_vm.export_codebook(str(tmp_path / "fail.txt"))
        assert exchange_vm.last_error is not None

        # Then succeed
        code = Code(id=CodeId.new(), name="Joy", color=Color.from_hex("#00FF00"))
        code_repo.save(code)
        exchange_vm.export_codebook(str(tmp_path / "ok.txt"))
        assert exchange_vm.last_error is None


@allure.story("QC-039 FileManager Exchange Integration")
class TestFileManagerExchangeIntegration:

    @allure.title("FileManagerScreen accepts exchange viewmodel")
    def test_screen_has_exchange_vm(self, file_manager_screen, exchange_vm):
        assert file_manager_screen._exchange_vm is exchange_vm

    @allure.title("Toolbar has import dropdown menu")
    def test_toolbar_import_menu(self, file_manager_screen):
        toolbar = file_manager_screen._page.toolbar
        menu = toolbar._import_btn.menu()
        assert menu is not None
        actions = [a.text() for a in menu.actions() if not a.isSeparator()]
        assert "Source Files..." in actions
        assert "Code List (.txt)..." in actions
        assert "Survey CSV (.csv)..." in actions
        assert "REFI-QDA Project (.qdpx)..." in actions
        assert "RQDA Project (.rqda)..." in actions

    @allure.title("Toolbar has export dropdown menu")
    def test_toolbar_export_menu(self, file_manager_screen):
        toolbar = file_manager_screen._page.toolbar
        menu = toolbar._export_btn.menu()
        assert menu is not None
        actions = [a.text() for a in menu.actions() if not a.isSeparator()]
        assert "Selected Sources..." in actions
        assert "Codebook (.txt)..." in actions
        assert "Coded HTML (.html)..." in actions
        assert "REFI-QDA Project (.qdpx)..." in actions

    @allure.title("Screenshot: Import dropdown menu")
    def test_screenshot_import_menu(self, file_manager_screen):
        from src.tests.e2e.utils.doc_screenshot import DocScreenshot

        file_manager_screen.resize(1200, 800)
        file_manager_screen.show()

        toolbar = file_manager_screen._page.toolbar
        menu = toolbar._import_btn.menu()
        menu.popup(toolbar._import_btn.mapToGlobal(toolbar._import_btn.rect().bottomLeft()))

        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        DocScreenshot.capture(file_manager_screen, "exchange-import-menu", attach_to_allure=True)
        menu.close()

    @allure.title("Screenshot: Export dropdown menu")
    def test_screenshot_export_menu(self, file_manager_screen):
        from src.tests.e2e.utils.doc_screenshot import DocScreenshot

        file_manager_screen.resize(1200, 800)
        file_manager_screen.show()

        toolbar = file_manager_screen._page.toolbar
        menu = toolbar._export_btn.menu()
        menu.popup(toolbar._export_btn.mapToGlobal(toolbar._export_btn.rect().bottomLeft()))

        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        DocScreenshot.capture(file_manager_screen, "exchange-export-menu", attach_to_allure=True)
        menu.close()
