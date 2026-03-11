"""
Exchange Context: Invariant Tests

Tests for pure validation functions in the exchange domain.
"""

from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.unit]


@allure.epic("QC-036 Exchange")
@allure.feature("QC-036 Exchange")
@allure.story("QC-036.07 Export Invariants")
class TestCodebookExportInvariants:
    """Invariants for codebook export validation."""

    @allure.title("can_export_codebook: True with codes, False without")
    def test_can_export_codebook(self):
        from src.contexts.exchange.core.invariants import can_export_codebook

        assert can_export_codebook(code_count=5) is True
        assert can_export_codebook(code_count=0) is False

    @allure.title("is_valid_output_path: valid path, empty string, nonexistent parent")
    def test_is_valid_output_path(self, tmp_path):
        from src.contexts.exchange.core.invariants import is_valid_output_path

        assert is_valid_output_path(str(tmp_path / "codebook.txt")) is True
        assert is_valid_output_path("") is False
        assert is_valid_output_path("/nonexistent/deep/path/file.txt") is False
