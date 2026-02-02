"""
Tests for TextExtractor - Infrastructure Layer.

Implements QC-027.01: Import Text Document
- AC #2: Document text is extracted and stored
- AC #4: Original formatting is preserved where possible
"""

from pathlib import Path

import pytest
from returns.result import Failure, Success

from src.contexts.sources.infra.text_extractor import ExtractionResult, TextExtractor


@pytest.fixture
def extractor() -> TextExtractor:
    """Create a text extractor instance."""
    return TextExtractor()


class TestTextExtraction:
    """Tests for extracting text from documents."""

    def test_extracts_txt_file(self, extractor: TextExtractor, tmp_path: Path):
        """AC #2: Extracts text from .txt file."""
        txt_file = tmp_path / "sample.txt"
        txt_file.write_text("Hello, World!\nThis is a test.", encoding="utf-8")

        result = extractor.extract(txt_file)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.content == "Hello, World!\nThis is a test."
        assert data.file_size > 0

    def test_preserves_line_breaks(self, extractor: TextExtractor, tmp_path: Path):
        """AC #4: Preserves formatting - line breaks."""
        txt_file = tmp_path / "multiline.txt"
        content = "Line 1\n\nLine 3\nLine 4"
        txt_file.write_text(content, encoding="utf-8")

        result = extractor.extract(txt_file)

        assert isinstance(result, Success)
        assert result.unwrap().content == content

    def test_handles_unicode(self, extractor: TextExtractor, tmp_path: Path):
        """Handles Unicode characters correctly."""
        txt_file = tmp_path / "unicode.txt"
        content = "Hello 世界! Привет мир! 🎉"
        txt_file.write_text(content, encoding="utf-8")

        result = extractor.extract(txt_file)

        assert isinstance(result, Success)
        assert result.unwrap().content == content

    def test_returns_file_size(self, extractor: TextExtractor, tmp_path: Path):
        """Returns correct file size."""
        txt_file = tmp_path / "sized.txt"
        content = "A" * 100
        txt_file.write_text(content, encoding="utf-8")

        result = extractor.extract(txt_file)

        assert isinstance(result, Success)
        assert result.unwrap().file_size == 100

    def test_fails_for_nonexistent_file(self, extractor: TextExtractor, tmp_path: Path):
        """Returns failure for non-existent file."""
        missing = tmp_path / "missing.txt"

        result = extractor.extract(missing)

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_detects_encoding(self, extractor: TextExtractor, tmp_path: Path):
        """Detects and handles different encodings."""
        txt_file = tmp_path / "latin1.txt"
        content = "Café résumé"
        txt_file.write_bytes(content.encode("latin-1"))

        result = extractor.extract(txt_file)

        # Should still extract even if encoding differs
        assert isinstance(result, Success)
        # Content should be readable (may need encoding detection)


class TestExtractionResult:
    """Tests for ExtractionResult data class."""

    def test_has_required_fields(self):
        """ExtractionResult has content and file_size."""
        result = ExtractionResult(
            content="test",
            file_size=4,
            encoding="utf-8",
        )

        assert result.content == "test"
        assert result.file_size == 4
        assert result.encoding == "utf-8"

    def test_encoding_is_optional(self):
        """Encoding field has sensible default."""
        result = ExtractionResult(
            content="test",
            file_size=4,
        )

        assert result.encoding is not None  # Should have default


class TestSupportedFormats:
    """Tests for format support checking."""

    def test_supports_txt(self, extractor: TextExtractor):
        """Supports .txt extension."""
        assert extractor.supports(Path("doc.txt"))

    def test_supports_docx(self, extractor: TextExtractor):
        """Supports .docx extension."""
        assert extractor.supports(Path("doc.docx"))

    def test_supports_rtf(self, extractor: TextExtractor):
        """Supports .rtf extension."""
        assert extractor.supports(Path("doc.rtf"))

    def test_does_not_support_pdf(self, extractor: TextExtractor):
        """Does not support .pdf (separate handler)."""
        assert not extractor.supports(Path("doc.pdf"))

    def test_does_not_support_image(self, extractor: TextExtractor):
        """Does not support image files."""
        assert not extractor.supports(Path("image.png"))
