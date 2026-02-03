"""
Sources Context: Invariants (Business Rule Predicates)

Pure predicate functions that validate business rules for source operations.
These are composed by Derivers to determine if an operation is valid.

Note: For backward compatibility, the actual invariant definitions are in
projects/core/invariants.py. This module re-exports them for use in the
Sources bounded context. A future migration will move the definitions here.
"""

from __future__ import annotations

# Re-export from projects for backward compatibility
# These invariants conceptually belong to Sources but are currently defined in Projects
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
