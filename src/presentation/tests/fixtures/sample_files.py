"""
Sample File Generator for QC-027 Tests.

Creates valid test files for each supported format:
- Text documents (.txt, .md)
- Images (.png, .jpg)
- Audio (minimal valid .wav header for testing)
- PDF (minimal valid structure)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SampleFiles:
    """Container for sample file paths."""

    # Text files
    txt_file: Path
    txt_unicode: Path
    txt_multiline: Path
    md_file: Path

    # Image files
    png_file: Path
    jpg_file: Path

    # Audio/Video files (minimal valid headers)
    wav_file: Path
    mp3_file: Path  # Minimal MP3 frame

    # PDF file
    pdf_file: Path

    # Directory for all fixtures
    root: Path


def create_sample_files(base_path: Path) -> SampleFiles:
    """
    Create sample files for testing.

    Args:
        base_path: Directory to create files in

    Returns:
        SampleFiles with paths to all created files
    """
    base_path.mkdir(parents=True, exist_ok=True)

    # === Text Files ===
    txt_file = base_path / "interview_01.txt"
    txt_file.write_text(
        "Interview Transcript\n"
        "====================\n\n"
        "Q: Tell me about your experience.\n"
        "A: It was very interesting. I learned a lot about the process.\n\n"
        "Q: What challenges did you face?\n"
        "A: Time management was the biggest challenge.\n",
        encoding="utf-8",
    )

    txt_unicode = base_path / "unicode_content.txt"
    txt_unicode.write_text(
        "Multilingual Content\n"
        "English: Hello World\n"
        "日本語: こんにちは世界\n"
        "Русский: Привет мир\n"
        "Emoji: 🎉 🔬 📊\n",
        encoding="utf-8",
    )

    txt_multiline = base_path / "field_notes.txt"
    txt_multiline.write_text(
        "Field Notes - Day 1\n\n"
        "Observation 1:\n"
        "  - Participants arrived at 9am\n"
        "  - Setup took 30 minutes\n\n"
        "Observation 2:\n"
        "  - Discussion was lively\n"
        "  - Key themes emerged\n",
        encoding="utf-8",
    )

    md_file = base_path / "research_notes.md"
    md_file.write_text(
        "# Research Notes\n\n"
        "## Methodology\n\n"
        "We used **qualitative coding** to analyze the data.\n\n"
        "## Key Findings\n\n"
        "1. Theme A: Collaboration\n"
        "2. Theme B: Innovation\n"
        "3. Theme C: Challenges\n",
        encoding="utf-8",
    )

    # === Image Files ===
    png_file = base_path / "sample_image.png"
    _create_minimal_png(png_file)

    jpg_file = base_path / "photo_01.jpg"
    _create_minimal_jpeg(jpg_file)

    # === Audio Files ===
    wav_file = base_path / "interview_audio.wav"
    _create_minimal_wav(wav_file, duration_seconds=2)

    mp3_file = base_path / "recording.mp3"
    _create_minimal_mp3(mp3_file)

    # === PDF File ===
    pdf_file = base_path / "document.pdf"
    _create_minimal_pdf(pdf_file)

    return SampleFiles(
        txt_file=txt_file,
        txt_unicode=txt_unicode,
        txt_multiline=txt_multiline,
        md_file=md_file,
        png_file=png_file,
        jpg_file=jpg_file,
        wav_file=wav_file,
        mp3_file=mp3_file,
        pdf_file=pdf_file,
        root=base_path,
    )


def _create_minimal_png(path: Path) -> None:
    """Create a minimal valid PNG file using Pillow."""
    from PIL import Image

    # Create a 10x10 red image
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(path, "PNG")


def _create_minimal_jpeg(path: Path) -> None:
    """Create a minimal valid JPEG file using Pillow."""
    from PIL import Image

    # Create a 10x10 blue image
    img = Image.new("RGB", (10, 10), color=(0, 0, 255))
    img.save(path, "JPEG")


def _create_minimal_wav(path: Path, duration_seconds: float = 1.0) -> None:
    """Create a minimal valid WAV file with silence."""
    sample_rate = 8000
    bits_per_sample = 8
    num_channels = 1
    num_samples = int(sample_rate * duration_seconds)

    # Audio data (silence = 128 for 8-bit)
    audio_data = bytes([128] * num_samples)

    # WAV header
    data_size = len(audio_data)
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # Subchunk1Size
        1,  # AudioFormat (PCM)
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )

    path.write_bytes(header + audio_data)


def _create_minimal_mp3(path: Path) -> None:
    """Create a minimal valid MP3 file (single frame)."""
    # MP3 frame header: sync word + layer 3 + 128kbps + 44100Hz + stereo
    # Frame header: 0xFF 0xFB (sync + MPEG1 Layer3)
    # This is a minimal valid MP3 frame
    mp3_frame = bytes(
        [
            # ID3v2 header (optional but common)
            0x49,
            0x44,
            0x33,  # "ID3"
            0x04,
            0x00,  # Version 2.4.0
            0x00,  # Flags
            0x00,
            0x00,
            0x00,
            0x00,  # Size = 0
            # MP3 frame header
            0xFF,
            0xFB,  # Sync + MPEG1 Layer3
            0x90,  # 128kbps, 44100Hz
            0x00,  # Padding, private, channel mode, etc.
            # Frame data (silence - minimal valid frame)
        ]
        + [0x00] * 417
    )  # Frame size for 128kbps at 44100Hz

    path.write_bytes(mp3_frame)


def _create_minimal_pdf(path: Path) -> None:
    """Create a minimal valid PDF file with text content."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000359 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
434
%%EOF
"""
    path.write_bytes(pdf_content)


def _crc32(data: bytes) -> int:
    """Calculate CRC32 for PNG chunks."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF
