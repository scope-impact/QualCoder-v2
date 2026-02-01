"""
Privacy domain events.

Events emitted when privacy-related operations occur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.privacy.entities import AnonymizationSessionId, PseudonymId
from src.domain.shared.types import DomainEvent, SourceId


# =============================================================================
# Pseudonym Events
# =============================================================================


@dataclass(frozen=True)
class PseudonymCreated(DomainEvent):
    """Emitted when a new pseudonym mapping is created."""

    event_type: str = field(default="privacy.pseudonym_created", init=False)
    pseudonym_id: PseudonymId = field(default=None)
    real_name: str = field(default="")
    alias: str = field(default="")
    category: str = field(default="person")

    @classmethod
    def create(
        cls,
        pseudonym_id: PseudonymId,
        real_name: str,
        alias: str,
        category: str,
    ) -> PseudonymCreated:
        """Create a new PseudonymCreated event."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            pseudonym_id=pseudonym_id,
            real_name=real_name,
            alias=alias,
            category=category,
        )


@dataclass(frozen=True)
class PseudonymUpdated(DomainEvent):
    """Emitted when a pseudonym is edited."""

    event_type: str = field(default="privacy.pseudonym_updated", init=False)
    pseudonym_id: PseudonymId = field(default=None)
    old_alias: str = field(default="")
    new_alias: str = field(default="")

    @classmethod
    def create(
        cls,
        pseudonym_id: PseudonymId,
        old_alias: str,
        new_alias: str,
    ) -> PseudonymUpdated:
        """Create a new PseudonymUpdated event."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            pseudonym_id=pseudonym_id,
            old_alias=old_alias,
            new_alias=new_alias,
        )


@dataclass(frozen=True)
class PseudonymDeleted(DomainEvent):
    """Emitted when a pseudonym is removed."""

    event_type: str = field(default="privacy.pseudonym_deleted", init=False)
    pseudonym_id: PseudonymId = field(default=None)
    alias: str = field(default="")

    @classmethod
    def create(
        cls,
        pseudonym_id: PseudonymId,
        alias: str,
    ) -> PseudonymDeleted:
        """Create a new PseudonymDeleted event."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            pseudonym_id=pseudonym_id,
            alias=alias,
        )


# =============================================================================
# Anonymization Events
# =============================================================================


@dataclass(frozen=True)
class PseudonymsApplied(DomainEvent):
    """Emitted when pseudonyms are applied to a source."""

    event_type: str = field(default="privacy.pseudonyms_applied", init=False)
    session_id: AnonymizationSessionId = field(default=None)
    source_id: SourceId = field(default=None)
    pseudonym_count: int = field(default=0)
    replacement_count: int = field(default=0)

    @classmethod
    def create(
        cls,
        session_id: AnonymizationSessionId,
        source_id: SourceId,
        pseudonym_count: int,
        replacement_count: int,
    ) -> PseudonymsApplied:
        """Create a new PseudonymsApplied event."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            session_id=session_id,
            source_id=source_id,
            pseudonym_count=pseudonym_count,
            replacement_count=replacement_count,
        )


@dataclass(frozen=True)
class AnonymizationReverted(DomainEvent):
    """Emitted when an anonymization is reverted to original."""

    event_type: str = field(default="privacy.anonymization_reverted", init=False)
    session_id: AnonymizationSessionId = field(default=None)
    source_id: SourceId = field(default=None)

    @classmethod
    def create(
        cls,
        session_id: AnonymizationSessionId,
        source_id: SourceId,
    ) -> AnonymizationReverted:
        """Create a new AnonymizationReverted event."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            session_id=session_id,
            source_id=source_id,
        )
