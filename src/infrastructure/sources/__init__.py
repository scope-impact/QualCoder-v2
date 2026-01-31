"""
Infrastructure layer for source file handling.

Provides services for:
- Text extraction from various file formats
- File loading and validation
"""

from src.infrastructure.sources.text_extractor import TextExtractor, ExtractionResult

__all__ = [
    "TextExtractor",
    "ExtractionResult",
]
