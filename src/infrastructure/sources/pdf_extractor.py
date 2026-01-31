"""
PDF Extractor Service - Infrastructure Layer.

Extracts text content from PDF documents.
Implements QC-027.02 AC #2 and AC #4.

Usage:
    extractor = PdfExtractor()
    result = extractor.extract(Path("document.pdf"))
    if isinstance(result, Success):
        content = result.unwrap().content
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.result import Failure, Result, Success


# ============================================================
# Data Types
# ============================================================


@dataclass(frozen=True)
class PdfExtractionResult:
    """Result of text extraction from a PDF document."""

    content: str
    page_count: int
    file_size: int


# ============================================================
# PDF Extractor Service
# ============================================================


class PdfExtractor:
    """
    Service for extracting text content from PDF documents.

    Supports multi-page PDFs with page separation markers.
    Uses pypdf (formerly PyPDF2) for extraction.

    Example:
        extractor = PdfExtractor()
        result = extractor.extract(Path("research_paper.pdf"))
        if isinstance(result, Success):
            print(f"Extracted {result.unwrap().page_count} pages")
    """

    def supports(self, path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return path.suffix.lower() == ".pdf"

    def extract(self, path: Path) -> Result[PdfExtractionResult, str]:
        """
        Extract text content from a PDF document.

        Args:
            path: Path to the PDF file

        Returns:
            Success with PdfExtractionResult, or Failure with error message
        """
        if not path.exists():
            return Failure(f"File not found: {path}")

        try:
            return self._extract_with_pypdf(path)
        except ImportError:
            return self._extract_fallback(path)
        except Exception as e:
            return Failure(f"Error extracting PDF: {e}")

    def _extract_with_pypdf(self, path: Path) -> Result[PdfExtractionResult, str]:
        """Extract using pypdf library."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            page_texts = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    page_texts.append(text)

            content = "\n\n".join(page_texts)
            file_size = path.stat().st_size

            return Success(
                PdfExtractionResult(
                    content=content,
                    page_count=len(reader.pages),
                    file_size=file_size,
                )
            )
        except ImportError:
            raise
        except Exception as e:
            return Failure(f"pypdf error: {e}")

    def _extract_fallback(self, path: Path) -> Result[PdfExtractionResult, str]:
        """Fallback when pypdf is not available."""
        # Try pdfplumber as alternative
        try:
            import pdfplumber

            page_texts = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        page_texts.append(text)

                content = "\n\n".join(page_texts)
                page_count = len(pdf.pages)

            return Success(
                PdfExtractionResult(
                    content=content,
                    page_count=page_count,
                    file_size=path.stat().st_size,
                )
            )
        except ImportError:
            return Failure(
                "No PDF library available. Install pypdf or pdfplumber to extract PDF content."
            )
        except Exception as e:
            return Failure(f"pdfplumber error: {e}")
