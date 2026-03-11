"""
Tests for TextExtractor - Infrastructure Layer.

Implements QC-027.01: Import Text Document
- AC #2: Document text is extracted and stored
- AC #4: Original formatting is preserved where possible
"""

from pathlib import Path

import allure
import pytest
from returns.result import Failure, Success

from src.contexts.sources.infra.text_extractor import ExtractionResult, TextExtractor

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


@pytest.fixture
def extractor() -> TextExtractor:
    """Create a text extractor instance."""
    return TextExtractor()


@allure.story("QC-027.01 Import Text Document")
class TestTextExtraction:
    """Tests for extracting text from documents."""

    @allure.title("Extracts text preserving content, line breaks, unicode, and file size")
    def test_extracts_text_with_formatting_and_metadata(self, extractor: TextExtractor, tmp_path: Path):
        """AC #2 & #4: Extracts text and preserves formatting."""
        # Basic text extraction
        txt_file = tmp_path / "sample.txt"
        txt_file.write_text("Hello, World!\nThis is a test.", encoding="utf-8")

        result = extractor.extract(txt_file)
        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.content == "Hello, World!\nThis is a test."
        assert data.file_size > 0

        # Preserves line breaks
        multiline = tmp_path / "multiline.txt"
        content = "Line 1\n\nLine 3\nLine 4"
        multiline.write_text(content, encoding="utf-8")

        result = extractor.extract(multiline)
        assert isinstance(result, Success)
        assert result.unwrap().content == content

        # Handles unicode
        unicode_file = tmp_path / "unicode.txt"
        unicode_content = "Hello 世界! Привет мир! 🎉"
        unicode_file.write_text(unicode_content, encoding="utf-8")

        result = extractor.extract(unicode_file)
        assert isinstance(result, Success)
        assert result.unwrap().content == unicode_content

        # Returns correct file size
        sized_file = tmp_path / "sized.txt"
        sized_content = "A" * 100
        sized_file.write_text(sized_content, encoding="utf-8")

        result = extractor.extract(sized_file)
        assert isinstance(result, Success)
        assert result.unwrap().file_size == 100

    @allure.title("Fails for nonexistent file")
    def test_fails_for_nonexistent_file(self, extractor: TextExtractor, tmp_path: Path):
        missing = tmp_path / "missing.txt"
        result = extractor.extract(missing)
        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    @allure.title("Detects and handles different encodings")
    def test_detects_encoding(self, extractor: TextExtractor, tmp_path: Path):
        txt_file = tmp_path / "latin1.txt"
        content = "Café résumé"
        txt_file.write_bytes(content.encode("latin-1"))

        result = extractor.extract(txt_file)
        assert isinstance(result, Success)


@allure.story("QC-027.01 Import Text Document")
class TestExtractionResult:
    """Tests for ExtractionResult data class."""

    @allure.title("Has required fields and encoding defaults correctly")
    def test_fields_and_defaults(self):
        result = ExtractionResult(content="test", file_size=4, encoding="utf-8")
        assert result.content == "test"
        assert result.file_size == 4
        assert result.encoding == "utf-8"

        # Encoding has sensible default
        result_default = ExtractionResult(content="test", file_size=4)
        assert result_default.encoding is not None


@allure.story("QC-027.01 Import Text Document")
class TestSupportedFormats:
    """Tests for format support checking."""

    @allure.title("Supports text formats and rejects non-text formats")
    @pytest.mark.parametrize(
        "filename, expected",
        [
            pytest.param("doc.txt", True, id="txt"),
            pytest.param("doc.docx", True, id="docx"),
            pytest.param("doc.rtf", True, id="rtf"),
            pytest.param("doc.pdf", False, id="pdf"),
            pytest.param("image.png", False, id="png"),
        ],
    )
    def test_format_support(self, extractor: TextExtractor, filename: str, expected: bool):
        assert extractor.supports(Path(filename)) == expected
