"""
Infrastructure layer for source file handling.

DEPRECATED: This module is a re-export for backward compatibility.
New code should import from src.contexts.sources.infra

Provides:
- Source and folder repositories
- Text extraction from various file formats
- PDF extraction with multi-page support
- Image metadata extraction
- Media (audio/video) metadata extraction
- File loading and validation
"""

from src.contexts.sources.infra import (
    ExtractionResult,
    ImageExtractionResult,
    ImageExtractor,
    MediaExtractionResult,
    MediaExtractor,
    PdfExtractionResult,
    PdfExtractor,
    SQLiteFolderRepository,
    SQLiteSourceRepository,
    TextExtractor,
    create_all,
    drop_all,
    metadata,
    src_folder,
    src_source,
)

__all__ = [
    # Repositories
    "SQLiteFolderRepository",
    "SQLiteSourceRepository",
    # Schema
    "create_all",
    "drop_all",
    "metadata",
    "src_folder",
    "src_source",
    # Extractors
    "ExtractionResult",
    "ImageExtractionResult",
    "ImageExtractor",
    "MediaExtractionResult",
    "MediaExtractor",
    "PdfExtractionResult",
    "PdfExtractor",
    "TextExtractor",
]
