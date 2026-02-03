"""
Sources Context: Invariants (Business Rule Predicates)

Re-exports source invariants from the projects context.
Source invariants are defined in projects/core/invariants.py as sources
are a core part of project management.
"""

from __future__ import annotations

from src.contexts.projects.core.invariants import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    VIDEO_EXTENSIONS,
    can_import_source,
    detect_source_type,
    is_source_name_unique,
    is_supported_source_type,
    is_valid_source_name,
)

__all__ = [
    # File extension mappings
    "TEXT_EXTENSIONS",
    "AUDIO_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "PDF_EXTENSIONS",
    # Source invariants
    "is_valid_source_name",
    "is_source_name_unique",
    "can_import_source",
    "is_supported_source_type",
    "detect_source_type",
]
