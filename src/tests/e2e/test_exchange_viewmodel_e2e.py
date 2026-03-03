"""
Exchange ViewModel - E2E Tests

Tests for the ExchangeViewModel which coordinates all import/export operations.
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
    from src.contexts.exchange.presentation.viewmodels.exchange_viewmodel import (
        ExchangeViewModel,
    )

    return ExchangeViewModel(
        code_repo=code_repo,
        category_repo=category_repo,
        segment_repo=segment_repo,
        source_repo=source_repo,
        case_repo=case_repo,
        event_bus=event_bus,
    )


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
