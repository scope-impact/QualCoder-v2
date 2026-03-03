"""
Exchange Context: Invariant Tests (TDD - RED phase)

Tests for pure validation functions in the exchange domain.
"""
from __future__ import annotations

import pytest


class TestCodebookExportInvariants:
    """Invariants for codebook export validation."""

    def test_can_export_codebook_with_codes(self):
        from src.contexts.exchange.core.invariants import can_export_codebook

        assert can_export_codebook(code_count=5) is True

    def test_cannot_export_codebook_with_no_codes(self):
        from src.contexts.exchange.core.invariants import can_export_codebook

        assert can_export_codebook(code_count=0) is False

    def test_is_valid_output_path_with_valid_path(self, tmp_path):
        from src.contexts.exchange.core.invariants import is_valid_output_path

        assert is_valid_output_path(str(tmp_path / "codebook.txt")) is True

    def test_is_valid_output_path_with_empty_string(self):
        from src.contexts.exchange.core.invariants import is_valid_output_path

        assert is_valid_output_path("") is False

    def test_is_valid_output_path_with_nonexistent_parent(self):
        from src.contexts.exchange.core.invariants import is_valid_output_path

        assert is_valid_output_path("/nonexistent/deep/path/file.txt") is False
