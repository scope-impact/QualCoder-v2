"""
Text Extractor Service - Infrastructure Layer.

Extracts text content from various document formats.
Implements QC-027.01 AC #2 and AC #4.

Usage:
    extractor = TextExtractor()
    result = extractor.extract(Path("document.txt"))
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
class ExtractionResult:
    """Result of text extraction from a document."""

    content: str
    file_size: int
    encoding: str = "utf-8"


# ============================================================
# Supported Extensions
# ============================================================


TEXT_EXTENSIONS = frozenset({".txt", ".docx", ".doc", ".odt", ".rtf", ".md"})


# ============================================================
# Text Extractor Service
# ============================================================


class TextExtractor:
    """
    Service for extracting text content from documents.

    Supports:
    - Plain text (.txt, .md)
    - Word documents (.docx, .doc)
    - OpenDocument (.odt)
    - Rich Text (.rtf)

    Example:
        extractor = TextExtractor()
        result = extractor.extract(Path("interview.txt"))
        if isinstance(result, Success):
            print(result.unwrap().content)
    """

    def supports(self, path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return path.suffix.lower() in TEXT_EXTENSIONS

    def extract(self, path: Path) -> Result[ExtractionResult, str]:
        """
        Extract text content from a document.

        Args:
            path: Path to the document file

        Returns:
            Success with ExtractionResult, or Failure with error message
        """
        if not path.exists():
            return Failure(f"File not found: {path}")

        suffix = path.suffix.lower()

        if suffix in {".txt", ".md"}:
            return self._extract_plain_text(path)
        elif suffix == ".docx":
            return self._extract_docx(path)
        elif suffix == ".rtf":
            return self._extract_rtf(path)
        elif suffix == ".odt":
            return self._extract_odt(path)
        elif suffix == ".doc":
            return self._extract_doc(path)
        else:
            return Failure(f"Unsupported format: {suffix}")

    def _extract_plain_text(self, path: Path) -> Result[ExtractionResult, str]:
        """Extract text from plain text files."""
        try:
            # Try UTF-8 first
            try:
                content = path.read_text(encoding="utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                # Fall back to latin-1 which can read any byte sequence
                content = path.read_text(encoding="latin-1")
                encoding = "latin-1"

            return Success(
                ExtractionResult(
                    content=content,
                    file_size=len(content),
                    encoding=encoding,
                )
            )
        except OSError as e:
            return Failure(f"Error reading file: {e}")

    def _extract_docx(self, path: Path) -> Result[ExtractionResult, str]:
        """Extract text from Word .docx files."""
        try:
            import docx

            doc = docx.Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs]
            content = "\n".join(paragraphs)

            return Success(
                ExtractionResult(
                    content=content,
                    file_size=path.stat().st_size,
                    encoding="utf-8",
                )
            )
        except ImportError:
            return Failure("python-docx not installed. Cannot extract .docx files.")
        except Exception as e:
            return Failure(f"Error extracting docx: {e}")

    def _extract_rtf(self, path: Path) -> Result[ExtractionResult, str]:
        """Extract text from RTF files."""
        try:
            from striprtf.striprtf import rtf_to_text

            rtf_content = path.read_text(encoding="latin-1")
            content = rtf_to_text(rtf_content)

            return Success(
                ExtractionResult(
                    content=content,
                    file_size=path.stat().st_size,
                    encoding="utf-8",
                )
            )
        except ImportError:
            return Failure("striprtf not installed. Cannot extract .rtf files.")
        except Exception as e:
            return Failure(f"Error extracting rtf: {e}")

    def _extract_odt(self, path: Path) -> Result[ExtractionResult, str]:
        """Extract text from OpenDocument files."""
        try:
            from odf import text as odf_text
            from odf.opendocument import load

            doc = load(str(path))
            paragraphs = doc.getElementsByType(odf_text.P)
            content = "\n".join(
                "".join(str(node) for node in p.childNodes) for p in paragraphs
            )

            return Success(
                ExtractionResult(
                    content=content,
                    file_size=path.stat().st_size,
                    encoding="utf-8",
                )
            )
        except ImportError:
            return Failure("odfpy not installed. Cannot extract .odt files.")
        except Exception as e:
            return Failure(f"Error extracting odt: {e}")

    def _extract_doc(self, path: Path) -> Result[ExtractionResult, str]:
        """Extract text from legacy Word .doc files."""
        # Legacy .doc format requires antiword or similar
        # For now, return a helpful error
        return Failure(
            "Legacy .doc format not supported. Please convert to .docx format."
        )
