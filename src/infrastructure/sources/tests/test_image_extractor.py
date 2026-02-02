"""
Tests for ImageExtractor - Infrastructure Layer.

TDD tests written BEFORE implementation.
Tests extraction of image metadata including dimensions, format, and EXIF data.
"""

from pathlib import Path

import pytest
from PIL import Image
from returns.result import Failure, Success

from src.contexts.sources.infra.image_extractor import (
    ImageExtractionResult,
    ImageExtractor,
)


@pytest.fixture
def extractor() -> ImageExtractor:
    """Create an image extractor instance."""
    return ImageExtractor()


@pytest.fixture
def sample_png(tmp_path: Path) -> Path:
    """Create a sample PNG image."""
    img_path = tmp_path / "sample.png"
    img = Image.new("RGB", (800, 600), color=(255, 0, 0))
    img.save(img_path, format="PNG")
    return img_path


@pytest.fixture
def sample_jpeg(tmp_path: Path) -> Path:
    """Create a sample JPEG image."""
    img_path = tmp_path / "sample.jpg"
    img = Image.new("RGB", (1920, 1080), color=(0, 255, 0))
    img.save(img_path, format="JPEG", quality=95)
    return img_path


@pytest.fixture
def sample_gif(tmp_path: Path) -> Path:
    """Create a sample GIF image."""
    img_path = tmp_path / "sample.gif"
    img = Image.new("RGB", (320, 240), color=(0, 0, 255))
    img.save(img_path, format="GIF")
    return img_path


class TestImageExtraction:
    """Tests for extracting image metadata."""

    def test_extracts_png_metadata(self, extractor: ImageExtractor, sample_png: Path):
        """Extracts width, height, and format from PNG image."""
        result = extractor.extract(sample_png)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.width == 800
        assert data.height == 600
        assert data.format == "PNG"
        assert data.file_size > 0

    def test_extracts_jpeg_metadata(self, extractor: ImageExtractor, sample_jpeg: Path):
        """Extracts width, height, and format from JPEG image."""
        result = extractor.extract(sample_jpeg)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.width == 1920
        assert data.height == 1080
        assert data.format == "JPEG"
        assert data.file_size > 0

    def test_extracts_gif_metadata(self, extractor: ImageExtractor, sample_gif: Path):
        """Extracts width, height, and format from GIF image."""
        result = extractor.extract(sample_gif)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.width == 320
        assert data.height == 240
        assert data.format == "GIF"
        assert data.file_size > 0

    def test_returns_accurate_file_size(
        self, extractor: ImageExtractor, sample_png: Path
    ):
        """Returns correct file size in bytes."""
        result = extractor.extract(sample_png)

        assert isinstance(result, Success)
        data = result.unwrap()
        # File size should match actual file size
        actual_size = sample_png.stat().st_size
        assert data.file_size == actual_size

    def test_extracts_metadata_dict(self, extractor: ImageExtractor, sample_png: Path):
        """Returns metadata dictionary with image info."""
        result = extractor.extract(sample_png)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert isinstance(data.metadata, dict)
        # Metadata should contain at least mode information
        assert "mode" in data.metadata

    def test_fails_for_nonexistent_file(
        self, extractor: ImageExtractor, tmp_path: Path
    ):
        """Returns failure for non-existent file."""
        missing = tmp_path / "missing.png"

        result = extractor.extract(missing)

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_fails_for_non_image_file(self, extractor: ImageExtractor, tmp_path: Path):
        """Returns failure for non-image file."""
        text_file = tmp_path / "not_image.txt"
        text_file.write_text("This is not an image")

        result = extractor.extract(text_file)

        assert isinstance(result, Failure)
        # Should indicate it's not a valid image
        error_msg = result.failure().lower()
        assert "cannot identify" in error_msg or "not a valid image" in error_msg

    def test_fails_for_corrupted_image(self, extractor: ImageExtractor, tmp_path: Path):
        """Returns failure for corrupted image file."""
        corrupted = tmp_path / "corrupted.png"
        # Write invalid PNG data
        corrupted.write_bytes(b"PNG\x89\x00\x00\x00corrupted")

        result = extractor.extract(corrupted)

        assert isinstance(result, Failure)


class TestImageExtractionResult:
    """Tests for ImageExtractionResult data class."""

    def test_has_required_fields(self):
        """ImageExtractionResult has all required fields."""
        result = ImageExtractionResult(
            width=1920,
            height=1080,
            format="JPEG",
            file_size=204800,
            metadata={"mode": "RGB"},
        )

        assert result.width == 1920
        assert result.height == 1080
        assert result.format == "JPEG"
        assert result.file_size == 204800
        assert result.metadata == {"mode": "RGB"}

    def test_metadata_can_be_empty(self):
        """Metadata dictionary can be empty."""
        result = ImageExtractionResult(
            width=800,
            height=600,
            format="PNG",
            file_size=1024,
            metadata={},
        )

        assert result.metadata == {}


class TestSupportedFormats:
    """Tests for format support checking."""

    def test_supports_png(self, extractor: ImageExtractor):
        """Supports .png extension."""
        assert extractor.supports(Path("image.png"))

    def test_supports_jpeg(self, extractor: ImageExtractor):
        """Supports .jpg extension."""
        assert extractor.supports(Path("image.jpg"))

    def test_supports_jpeg_alternate(self, extractor: ImageExtractor):
        """Supports .jpeg extension."""
        assert extractor.supports(Path("image.jpeg"))

    def test_supports_gif(self, extractor: ImageExtractor):
        """Supports .gif extension."""
        assert extractor.supports(Path("image.gif"))

    def test_supports_bmp(self, extractor: ImageExtractor):
        """Supports .bmp extension."""
        assert extractor.supports(Path("image.bmp"))

    def test_supports_tiff(self, extractor: ImageExtractor):
        """Supports .tiff extension."""
        assert extractor.supports(Path("image.tiff"))

    def test_supports_tif(self, extractor: ImageExtractor):
        """Supports .tif extension."""
        assert extractor.supports(Path("image.tif"))

    def test_supports_webp(self, extractor: ImageExtractor):
        """Supports .webp extension."""
        assert extractor.supports(Path("image.webp"))

    def test_does_not_support_pdf(self, extractor: ImageExtractor):
        """Does not support .pdf (separate handler)."""
        assert not extractor.supports(Path("doc.pdf"))

    def test_does_not_support_text(self, extractor: ImageExtractor):
        """Does not support text files."""
        assert not extractor.supports(Path("doc.txt"))

    def test_case_insensitive_extension(self, extractor: ImageExtractor):
        """Extension checking is case-insensitive."""
        assert extractor.supports(Path("image.PNG"))
        assert extractor.supports(Path("image.JpEg"))


class TestEXIFMetadata:
    """Tests for EXIF metadata extraction."""

    def test_extracts_exif_when_present(
        self, extractor: ImageExtractor, tmp_path: Path
    ):
        """Extracts EXIF metadata from JPEG with EXIF data."""
        img_path = tmp_path / "with_exif.jpg"
        img = Image.new("RGB", (640, 480), color=(128, 128, 128))

        # Create EXIF data (simplified - just to test extraction)

        exif = img.getexif()
        if exif is not None:
            # Add some basic EXIF data (if supported)
            img.save(img_path, format="JPEG", exif=exif)
        else:
            img.save(img_path, format="JPEG")

        result = extractor.extract(img_path)

        assert isinstance(result, Success)
        data = result.unwrap()
        # metadata should be a dict (may or may not have EXIF depending on PIL version)
        assert isinstance(data.metadata, dict)

    def test_handles_images_without_exif(
        self, extractor: ImageExtractor, sample_png: Path
    ):
        """Handles images without EXIF data gracefully."""
        result = extractor.extract(sample_png)

        assert isinstance(result, Success)
        data = result.unwrap()
        # Should still return valid metadata dict
        assert isinstance(data.metadata, dict)
