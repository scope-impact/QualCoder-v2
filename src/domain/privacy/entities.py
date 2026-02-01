"""
Privacy domain entities.

Provides Pseudonym, AnonymizationSession, and related value objects
for managing data anonymization in qualitative research.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from src.domain.shared.types import SourceId


# =============================================================================
# Typed Identifiers
# =============================================================================


@dataclass(frozen=True)
class PseudonymId:
    """Typed identifier for Pseudonym entities."""

    value: int

    @classmethod
    def new(cls) -> PseudonymId:
        """Generate a new unique ID."""
        return cls(value=int(uuid4().int % 1_000_000))


@dataclass(frozen=True)
class AnonymizationSessionId:
    """Typed identifier for anonymization sessions."""

    value: str

    @classmethod
    def new(cls) -> AnonymizationSessionId:
        """Generate a new unique ID with anon_ prefix."""
        return cls(value=f"anon_{uuid4().hex[:12]}")


# =============================================================================
# Enums
# =============================================================================


class PseudonymCategory(str, Enum):
    """Categories of identifiers that can be pseudonymized."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    OTHER = "other"


# =============================================================================
# Value Objects
# =============================================================================


@dataclass(frozen=True)
class TextReplacement:
    """
    Records a single text replacement for reversal.

    Stores the original and replacement text along with all positions
    where the replacement was applied in the original text.
    """

    original_text: str
    replacement_text: str
    positions: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class DetectedIdentifier:
    """
    A potential identifier detected in text.

    Used for AI-suggested anonymization candidates with confidence scores.
    """

    text: str
    category: PseudonymCategory
    positions: tuple[tuple[int, int], ...]
    confidence: float
    suggested_alias: str | None = None


# =============================================================================
# Entities
# =============================================================================


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class Pseudonym:
    """
    A pseudonym mapping from real name to alias.

    Core entity for the Privacy bounded context.
    Stores the reversible mapping between real identifiers
    and their anonymized versions.
    """

    id: PseudonymId
    real_name: str
    alias: str
    category: PseudonymCategory
    notes: str | None = None
    created_at: datetime = field(default_factory=_now)

    def with_alias(self, new_alias: str) -> Pseudonym:
        """Return new Pseudonym with updated alias."""
        return Pseudonym(
            id=self.id,
            real_name=self.real_name,
            alias=new_alias,
            category=self.category,
            notes=self.notes,
            created_at=self.created_at,
        )

    def with_notes(self, new_notes: str | None) -> Pseudonym:
        """Return new Pseudonym with updated notes."""
        return Pseudonym(
            id=self.id,
            real_name=self.real_name,
            alias=self.alias,
            category=self.category,
            notes=new_notes,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class AnonymizationSession:
    """
    Tracks an anonymization operation for undo capability.

    Stores the original text and positions of replacements
    to enable reversibility.
    """

    id: AnonymizationSessionId
    source_id: SourceId
    original_text: str
    pseudonym_ids: tuple[PseudonymId, ...]
    replacements: tuple[TextReplacement, ...]
    created_at: datetime = field(default_factory=_now)
    reverted_at: datetime | None = None

    def is_reversible(self) -> bool:
        """Check if this session can be reverted."""
        return self.reverted_at is None
