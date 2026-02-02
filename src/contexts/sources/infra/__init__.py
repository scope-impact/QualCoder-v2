"""
Sources Context - Infrastructure Layer

Provides:
- Source and folder repositories
- Text extraction from various file formats
- PDF extraction with multi-page support
- Image metadata extraction
- Media (audio/video) metadata extraction
- File loading and validation
"""

from src.contexts.sources.infra.folder_repository import SQLiteFolderRepository
from src.contexts.sources.infra.image_extractor import (
    ImageExtractionResult,
    ImageExtractor,
)
from src.contexts.sources.infra.media_extractor import (
    MediaExtractionResult,
    MediaExtractor,
)
from src.contexts.sources.infra.pdf_extractor import PdfExtractionResult, PdfExtractor
from src.contexts.sources.infra.schema import (
    create_all,
    drop_all,
    metadata,
    src_folder,
    src_source,
)
from src.contexts.sources.infra.source_repository import SQLiteSourceRepository
from src.contexts.sources.infra.text_extractor import ExtractionResult, TextExtractor

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
