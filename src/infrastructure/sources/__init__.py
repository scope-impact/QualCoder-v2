"""
Infrastructure layer for source file handling.

Provides services for:
- Text extraction from various file formats
- PDF extraction with multi-page support
- File loading and validation
"""

from src.infrastructure.sources.pdf_extractor import PdfExtractionResult, PdfExtractor
from src.infrastructure.sources.text_extractor import ExtractionResult, TextExtractor

__all__ = [
    "ExtractionResult",
    "PdfExtractionResult",
    "PdfExtractor",
    "TextExtractor",
]
