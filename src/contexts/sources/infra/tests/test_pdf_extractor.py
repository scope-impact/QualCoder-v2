"""
Tests for PdfExtractor - Infrastructure Layer.

Implements QC-027.02: Import PDF Document
- AC #2: Text is extracted from PDF pages
- AC #4: Multi-page PDFs are handled correctly
"""

from pathlib import Path

import allure
import pytest
from returns.result import Failure

from src.contexts.sources.infra.pdf_extractor import PdfExtractionResult, PdfExtractor

pytestmark = [
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


@pytest.fixture
def extractor() -> PdfExtractor:
    """Create a PDF extractor instance."""
    return PdfExtractor()


@allure.story("QC-027.02 Import PDF Document")
class TestPdfExtraction:
    """Tests for extracting text from PDF documents."""

    @allure.title("Supports .pdf but not other extensions; fails for nonexistent file")
    def test_supports_and_fails_for_nonexistent(
        self, extractor: PdfExtractor, tmp_path: Path
    ):
        """Supports .pdf extension; rejects non-PDF; fails for missing file."""
        assert extractor.supports(Path("document.pdf"))
        assert not extractor.supports(Path("document.txt"))
        assert not extractor.supports(Path("document.docx"))

        missing = tmp_path / "missing.pdf"
        result = extractor.extract(missing)
        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()


@allure.story("QC-027.02 Import PDF Document")
class TestPdfExtractionResult:
    """Tests for PdfExtractionResult data class."""

    @allure.title("Has required fields and supports multi-page content")
    def test_fields_and_multi_page(self):
        """PdfExtractionResult stores content, page_count, file_size; handles multi-page."""
        result = PdfExtractionResult(
            content="test content",
            page_count=1,
            file_size=1024,
        )
        assert result.content == "test content"
        assert result.page_count == 1
        assert result.file_size == 1024

        # Multi-page content
        multi = PdfExtractionResult(
            content="Page 1 content\n\n--- Page 2 ---\n\nPage 2 content",
            page_count=2,
            file_size=2048,
        )
        assert multi.page_count == 2
        assert "Page 1" in multi.content
        assert "Page 2" in multi.content
