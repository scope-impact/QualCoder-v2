"""
Shared Presentation Layer.

Cross-cutting UI infrastructure: templates, molecules, organisms, services.
"""

from src.shared.presentation.dto import (
    TextCodingDataDTO,
    create_empty_text_coding_data,
)

__all__ = [
    "TextCodingDataDTO",
    "create_empty_text_coding_data",
]
