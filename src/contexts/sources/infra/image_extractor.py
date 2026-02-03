"""
Image Extractor Service - Infrastructure Layer.

Extracts metadata from image files including dimensions, format, and EXIF data.

Usage:
    extractor = ImageExtractor()
    result = extractor.extract(Path("photo.jpg"))
    if isinstance(result, Success):
        metadata = result.unwrap()
        print(f"Dimensions: {metadata.width}x{metadata.height}")
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
from returns.result import Failure, Result, Success

# Register HEIC/HEIF support with Pillow
register_heif_opener()

# ============================================================
# Data Types
# ============================================================


@dataclass(frozen=True)
class ImageExtractionResult:
    """Result of image metadata extraction."""

    width: int
    height: int
    format: str
    file_size: int
    metadata: dict[str, Any]


# ============================================================
# Supported Extensions
# ============================================================


IMAGE_EXTENSIONS = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".heic",
        ".heif",
    }
)


# ============================================================
# Image Extractor Service
# ============================================================


class ImageExtractor:
    """
    Service for extracting metadata from image files.

    Supports:
    - JPEG (.jpg, .jpeg)
    - PNG (.png)
    - GIF (.gif)
    - BMP (.bmp)
    - TIFF (.tiff, .tif)
    - WebP (.webp)
    - HEIC/HEIF (.heic, .heif)

    Example:
        extractor = ImageExtractor()
        result = extractor.extract(Path("photo.jpg"))
        if isinstance(result, Success):
            data = result.unwrap()
            print(f"{data.width}x{data.height} {data.format}")
    """

    def supports(self, path: Path) -> bool:
        """Check if this extractor supports the given file format."""
        return path.suffix.lower() in IMAGE_EXTENSIONS

    def extract(self, path: Path) -> Result[ImageExtractionResult, str]:
        """
        Extract metadata from an image file.

        Args:
            path: Path to the image file

        Returns:
            Success with ImageExtractionResult, or Failure with error message
        """
        if not path.exists():
            return Failure(f"File not found: {path}")

        try:
            # Open image and extract basic metadata
            with Image.open(path) as img:
                width, height = img.size
                img_format = img.format or "Unknown"
                file_size = path.stat().st_size

                # Extract metadata dictionary
                metadata = self._extract_metadata(img)

                return Success(
                    ImageExtractionResult(
                        width=width,
                        height=height,
                        format=img_format,
                        file_size=file_size,
                        metadata=metadata,
                    )
                )
        except FileNotFoundError:
            return Failure(f"File not found: {path}")
        except Exception as e:
            error_msg = str(e).lower()
            if "cannot identify" in error_msg:
                return Failure(f"Cannot identify image file: {path}")
            return Failure(f"Error extracting image metadata: {e}")

    def _extract_metadata(self, img: Image.Image) -> dict[str, Any]:
        """
        Extract metadata dictionary from PIL Image.

        Includes mode, EXIF data (if present), and other image info.
        """
        metadata: dict[str, Any] = {}

        # Add basic image mode
        if img.mode:
            metadata["mode"] = img.mode

        # Extract EXIF data if present
        try:
            exif_data = img.getexif()
            if exif_data:
                exif_dict = {}
                for tag_id, value in exif_data.items():
                    # Convert tag ID to human-readable name
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    # Convert bytes to string for JSON compatibility
                    if isinstance(value, bytes):
                        try:
                            value = value.decode("utf-8", errors="ignore")
                        except Exception:
                            value = str(value)
                    exif_dict[tag_name] = value
                if exif_dict:
                    metadata["exif"] = exif_dict
        except Exception:
            # If EXIF extraction fails, continue without it
            pass

        # Add other image info
        if hasattr(img, "info") and img.info:
            # Filter out non-serializable values
            info_dict = {}
            for key, value in img.info.items():
                if isinstance(value, str | int | float | bool):
                    info_dict[key] = value
                elif isinstance(value, bytes):
                    with contextlib.suppress(Exception):
                        info_dict[key] = value.decode("utf-8", errors="ignore")
            if info_dict:
                metadata["info"] = info_dict

        return metadata
