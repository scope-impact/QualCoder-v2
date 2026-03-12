"""
Tests for ImageExtractor - Infrastructure Layer.

TDD tests written BEFORE implementation.
Tests extraction of image metadata including dimensions, format, and EXIF data.
"""

from pathlib import Path

import allure
import pytest
from PIL import Image
from returns.result import Failure, Success

from src.contexts.sources.infra.image_extractor import (
    ImageExtractionResult,
    ImageExtractor,
)

pytestmark = [
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


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


@allure.story("QC-027.03 Import Image Files")
class TestImageExtraction:
    """Tests for extracting image metadata."""

    @allure.title("Extracts metadata from {format_name} image")
    @pytest.mark.parametrize(
        "fixture_name,expected_width,expected_height,format_name",
        [
            ("sample_png", 800, 600, "PNG"),
            ("sample_jpeg", 1920, 1080, "JPEG"),
            ("sample_gif", 320, 240, "GIF"),
        ],
    )
    def test_extracts_image_metadata(
        self,
        extractor: ImageExtractor,
        fixture_name: str,
        expected_width: int,
        expected_height: int,
        format_name: str,
        request: pytest.FixtureRequest,
    ):
        """Extracts width, height, format, file size, and metadata from image."""
        img_path = request.getfixturevalue(fixture_name)
        result = extractor.extract(img_path)

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data.width == expected_width
        assert data.height == expected_height
        assert data.format == format_name
        assert data.file_size == img_path.stat().st_size
        assert isinstance(data.metadata, dict)

    @allure.title("Fails for invalid file: {scenario}")
    @pytest.mark.parametrize(
        "scenario,filename,content",
        [
            ("nonexistent", "missing.png", None),
            ("non-image", "not_image.txt", b"This is not an image"),
            ("corrupted", "corrupted.png", b"PNG\x89\x00\x00\x00corrupted"),
        ],
    )
    def test_fails_for_invalid_files(
        self,
        extractor: ImageExtractor,
        tmp_path: Path,
        scenario: str,
        filename: str,
        content: bytes | None,
    ):
        """Returns failure for nonexistent, non-image, or corrupted files."""
        file_path = tmp_path / filename
        if content is not None:
            file_path.write_bytes(content)

        result = extractor.extract(file_path)

        assert isinstance(result, Failure)

    @allure.title("Handles EXIF metadata gracefully and result dataclass works")
    def test_handles_exif_and_result_dataclass(
        self, extractor: ImageExtractor, sample_png: Path, tmp_path: Path
    ):
        """Extracts EXIF when present; handles absence; result dataclass stores fields."""
        # JPEG with EXIF
        jpeg_path = tmp_path / "with_exif.jpg"
        img = Image.new("RGB", (640, 480), color=(128, 128, 128))
        exif = img.getexif()
        if exif is not None:
            img.save(jpeg_path, format="JPEG", exif=exif)
        else:
            img.save(jpeg_path, format="JPEG")

        for path in [jpeg_path, sample_png]:
            result = extractor.extract(path)
            assert isinstance(result, Success)
            assert isinstance(result.unwrap().metadata, dict)

        # ImageExtractionResult dataclass
        full = ImageExtractionResult(
            width=1920,
            height=1080,
            format="JPEG",
            file_size=204800,
            metadata={"mode": "RGB"},
        )
        assert full.width == 1920
        assert full.format == "JPEG"
        assert full.metadata == {"mode": "RGB"}

        empty = ImageExtractionResult(
            width=800,
            height=600,
            format="PNG",
            file_size=1024,
            metadata={},
        )
        assert empty.metadata == {}


@allure.story("QC-027.03 Import Image Files")
class TestSupportedFormats:
    """Tests for format support checking."""

    @allure.title("Supports common image formats and rejects non-image formats")
    @pytest.mark.parametrize(
        "ext", [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"]
    )
    def test_supports_image_formats(self, extractor: ImageExtractor, ext: str):
        """Supports common image extensions."""
        assert extractor.supports(Path(f"image{ext}"))

    @allure.title("Rejects non-image and checks case-insensitive: {filename}")
    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("doc.pdf", False),
            ("doc.txt", False),
            ("image.PNG", True),
            ("image.JpEg", True),
        ],
    )
    def test_non_image_and_case_insensitive(
        self, extractor: ImageExtractor, filename: str, expected: bool
    ):
        """Does not support non-image file types; extension checking is case-insensitive."""
        assert extractor.supports(Path(filename)) == expected
