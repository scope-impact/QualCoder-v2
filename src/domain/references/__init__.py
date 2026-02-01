"""
References bounded context - Domain layer.

Manages academic references and their links to coded segments.
"""

from src.domain.references.derivers import (
    EmptyAuthors,
    EmptyTitle,
    InvalidDoi,
    InvalidYear,
    ReferenceAlreadyLinked,
    ReferenceNotFound,
    ReferenceNotLinked,
    ReferenceState,
    derive_add_reference,
    derive_link_reference_to_segment,
    derive_remove_reference,
    derive_unlink_reference_from_segment,
    derive_update_reference,
)
from src.domain.references.entities import Reference
from src.domain.references.events import (
    ReferenceAdded,
    ReferenceLinkedToSegment,
    ReferenceRemoved,
    ReferenceUnlinkedFromSegment,
    ReferenceUpdated,
)
from src.domain.references.invariants import (
    MAX_AUTHORS_LENGTH,
    MAX_TITLE_LENGTH,
    is_valid_authors,
    is_valid_doi,
    is_valid_title,
    is_valid_year,
)

__all__ = [
    # Entities
    "Reference",
    # Events
    "ReferenceAdded",
    "ReferenceUpdated",
    "ReferenceRemoved",
    "ReferenceLinkedToSegment",
    "ReferenceUnlinkedFromSegment",
    # Derivers
    "derive_add_reference",
    "derive_update_reference",
    "derive_remove_reference",
    "derive_link_reference_to_segment",
    "derive_unlink_reference_from_segment",
    # State
    "ReferenceState",
    # Failure reasons
    "EmptyTitle",
    "EmptyAuthors",
    "InvalidYear",
    "InvalidDoi",
    "ReferenceNotFound",
    "ReferenceAlreadyLinked",
    "ReferenceNotLinked",
    # Invariants
    "is_valid_title",
    "is_valid_authors",
    "is_valid_year",
    "is_valid_doi",
    "MAX_TITLE_LENGTH",
    "MAX_AUTHORS_LENGTH",
]
