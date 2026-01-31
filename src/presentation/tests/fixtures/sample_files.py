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
    """Create a minimal valid PNG file (1x1 red pixel)."""
    # PNG signature
    signature = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

    # IHDR chunk (image header)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)  # 1x1, 8-bit RGB
    ihdr_crc = _crc32(b"IHDR" + ihdr_data)
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    # IDAT chunk (image data - minimal compressed red pixel)
    # Zlib compressed: filter byte (0) + RGB (255, 0, 0)
    idat_data = bytes(
        [0x78, 0x9C, 0x62, 0xF8, 0xCF, 0xC0, 0x00, 0x00, 0x01, 0x05, 0x00, 0x82]
    )
    idat_crc = _crc32(b"IDAT" + idat_data)
    idat = (
        struct.pack(">I", len(idat_data))
        + b"IDAT"
        + idat_data
        + struct.pack(">I", idat_crc)
    )

    # IEND chunk
    iend_crc = _crc32(b"IEND")
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    path.write_bytes(signature + ihdr + idat + iend)


def _create_minimal_jpeg(path: Path) -> None:
    """Create a minimal valid JPEG file (1x1 red pixel)."""
    # Minimal JPEG with SOI, APP0, DQT, SOF0, DHT, SOS, image data, EOI
    jpeg_data = bytes(
        [
            # SOI (Start of Image)
            0xFF,
            0xD8,
            # APP0 (JFIF marker)
            0xFF,
            0xE0,
            0x00,
            0x10,
            0x4A,
            0x46,
            0x49,
            0x46,
            0x00,  # "JFIF\0"
            0x01,
            0x01,  # Version 1.1
            0x00,  # Aspect ratio units (0 = no units)
            0x00,
            0x01,
            0x00,
            0x01,  # X/Y density = 1
            0x00,
            0x00,  # No thumbnail
            # DQT (Define Quantization Table)
            0xFF,
            0xDB,
            0x00,
            0x43,
            0x00,
            0x08,
            0x06,
            0x06,
            0x07,
            0x06,
            0x05,
            0x08,
            0x07,
            0x07,
            0x07,
            0x09,
            0x09,
            0x08,
            0x0A,
            0x0C,
            0x14,
            0x0D,
            0x0C,
            0x0B,
            0x0B,
            0x0C,
            0x19,
            0x12,
            0x13,
            0x0F,
            0x14,
            0x1D,
            0x1A,
            0x1F,
            0x1E,
            0x1D,
            0x1A,
            0x1C,
            0x1C,
            0x20,
            0x24,
            0x2E,
            0x27,
            0x20,
            0x22,
            0x2C,
            0x23,
            0x1C,
            0x1C,
            0x28,
            0x37,
            0x29,
            0x2C,
            0x30,
            0x31,
            0x34,
            0x34,
            0x34,
            0x1F,
            0x27,
            0x39,
            0x3D,
            0x38,
            0x32,
            0x3C,
            0x2E,
            0x33,
            0x34,
            0x32,
            # SOF0 (Start of Frame - Baseline DCT)
            0xFF,
            0xC0,
            0x00,
            0x0B,
            0x08,
            0x00,
            0x01,
            0x00,
            0x01,  # 1x1 pixels
            0x01,  # 1 component
            0x01,
            0x11,
            0x00,  # Component 1, sampling 1x1, quant table 0
            # DHT (Define Huffman Table) - DC
            0xFF,
            0xC4,
            0x00,
            0x1F,
            0x00,
            0x00,
            0x01,
            0x05,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            # DHT - AC
            0xFF,
            0xC4,
            0x00,
            0xB5,
            0x10,
            0x00,
            0x02,
            0x01,
            0x03,
            0x03,
            0x02,
            0x04,
            0x03,
            0x05,
            0x05,
            0x04,
            0x04,
            0x00,
            0x00,
            0x01,
            0x7D,
            0x01,
            0x02,
            0x03,
            0x00,
            0x04,
            0x11,
            0x05,
            0x12,
            0x21,
            0x31,
            0x41,
            0x06,
            0x13,
            0x51,
            0x61,
            0x07,
            0x22,
            0x71,
            0x14,
            0x32,
            0x81,
            0x91,
            0xA1,
            0x08,
            0x23,
            0x42,
            0xB1,
            0xC1,
            0x15,
            0x52,
            0xD1,
            0xF0,
            0x24,
            0x33,
            0x62,
            0x72,
            0x82,
            0x09,
            0x0A,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x25,
            0x26,
            0x27,
            0x28,
            0x29,
            0x2A,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x3A,
            0x43,
            0x44,
            0x45,
            0x46,
            0x47,
            0x48,
            0x49,
            0x4A,
            0x53,
            0x54,
            0x55,
            0x56,
            0x57,
            0x58,
            0x59,
            0x5A,
            0x63,
            0x64,
            0x65,
            0x66,
            0x67,
            0x68,
            0x69,
            0x6A,
            0x73,
            0x74,
            0x75,
            0x76,
            0x77,
            0x78,
            0x79,
            0x7A,
            0x83,
            0x84,
            0x85,
            0x86,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x92,
            0x93,
            0x94,
            0x95,
            0x96,
            0x97,
            0x98,
            0x99,
            0x9A,
            0xA2,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0xA7,
            0xA8,
            0xA9,
            0xAA,
            0xB2,
            0xB3,
            0xB4,
            0xB5,
            0xB6,
            0xB7,
            0xB8,
            0xB9,
            0xBA,
            0xC2,
            0xC3,
            0xC4,
            0xC5,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0xCA,
            0xD2,
            0xD3,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0xD8,
            0xD9,
            0xDA,
            0xE1,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0xE6,
            0xE7,
            0xE8,
            0xE9,
            0xEA,
            0xF1,
            0xF2,
            0xF3,
            0xF4,
            0xF5,
            0xF6,
            0xF7,
            0xF8,
            0xF9,
            0xFA,
            # SOS (Start of Scan)
            0xFF,
            0xDA,
            0x00,
            0x08,
            0x01,
            0x01,
            0x00,
            0x00,
            0x3F,
            0x00,
            # Image data (minimal)
            0xFB,
            0xD3,
            0x28,
            0xA2,
            0x80,
            0x03,
            0xFF,
            # EOI (End of Image)
            0xFF,
            0xD9,
        ]
    )
    path.write_bytes(jpeg_data)


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
