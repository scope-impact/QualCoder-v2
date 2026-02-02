"""
Tests for PdfExtractor - Infrastructure Layer.

Implements QC-027.02: Import PDF Document
- AC #2: Text is extracted from PDF pages
- AC #4: Multi-page PDFs are handled correctly
"""

from pathlib import Path

import pytest
from returns.result import Failure

from src.contexts.sources.infra.pdf_extractor import PdfExtractionResult, PdfExtractor


@pytest.fixture
def extractor() -> PdfExtractor:
    """Create a PDF extractor instance."""
    return PdfExtractor()


class TestPdfExtraction:
    """Tests for extracting text from PDF documents."""

    def test_supports_pdf_extension(self, extractor: PdfExtractor):
        """Supports .pdf extension."""
        assert extractor.supports(Path("document.pdf"))

    def test_does_not_support_other_extensions(self, extractor: PdfExtractor):
        """Does not support non-PDF files."""
        assert not extractor.supports(Path("document.txt"))
        assert not extractor.supports(Path("document.docx"))

    def test_fails_for_nonexistent_file(self, extractor: PdfExtractor, tmp_path: Path):
        """Returns failure for non-existent file."""
        missing = tmp_path / "missing.pdf"

        result = extractor.extract(missing)

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()


class TestPdfExtractionResult:
    """Tests for PdfExtractionResult data class."""

    def test_has_required_fields(self):
        """PdfExtractionResult has content, page_count, and file_size."""
        result = PdfExtractionResult(
            content="test content",
            page_count=1,
            file_size=1024,
        )

        assert result.content == "test content"
        assert result.page_count == 1
        assert result.file_size == 1024

    def test_multi_page_content(self):
        """AC #4: Can store multi-page content."""
        result = PdfExtractionResult(
            content="Page 1 content\n\n--- Page 2 ---\n\nPage 2 content",
            page_count=2,
            file_size=2048,
        )

        assert result.page_count == 2
        assert "Page 1" in result.content
        assert "Page 2" in result.content
