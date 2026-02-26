"""
Cases Context: Domain Entities

Immutable entities representing cases and case attributes in qualitative research.
Cases organize data by participant, site, or other groupings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.shared import CaseId


class AttributeType(str, Enum):
    """Types of case attributes."""

    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"


@dataclass(frozen=True)
class CaseAttribute:
    """
    Value object representing a case attribute.

    Attributes store demographic or categorical data about cases.
    """

    name: str
    attr_type: AttributeType
    value: Any

    def with_value(self, new_value: Any) -> CaseAttribute:
        """Return new attribute with updated value."""
        return CaseAttribute(
            name=self.name,
            attr_type=self.attr_type,
            value=new_value,
        )


@dataclass(frozen=True)
class Case:
    """
    Case entity - Aggregate root for the Cases context.

    A case represents a unit of analysis (participant, site, organization, etc.)
    that groups related sources and coded segments.
    """

    id: CaseId
    name: str
    description: str | None = None
    memo: str | None = None
    attributes: tuple[CaseAttribute, ...] = field(default_factory=tuple)
    source_ids: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def _evolve(self, **changes: Any) -> Case:
        """Return a new Case with the given fields replaced and updated_at refreshed."""
        defaults = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "memo": self.memo,
            "attributes": self.attributes,
            "source_ids": self.source_ids,
            "created_at": self.created_at,
            "updated_at": datetime.now(UTC),
        }
        defaults.update(changes)
        return Case(**defaults)

    def with_name(self, new_name: str) -> Case:
        """Return new Case with updated name."""
        return self._evolve(name=new_name)

    def with_description(self, new_description: str | None) -> Case:
        """Return new Case with updated description."""
        return self._evolve(description=new_description)

    def with_memo(self, new_memo: str | None) -> Case:
        """Return new Case with updated memo."""
        return self._evolve(memo=new_memo)

    def with_attribute(self, attribute: CaseAttribute) -> Case:
        """Return new Case with added/updated attribute."""
        filtered = tuple(a for a in self.attributes if a.name != attribute.name)
        return self._evolve(attributes=filtered + (attribute,))

    def without_attribute(self, attr_name: str) -> Case:
        """Return new Case with attribute removed."""
        return self._evolve(
            attributes=tuple(a for a in self.attributes if a.name != attr_name),
        )

    def with_source(self, source_id: str) -> Case:
        """Return new Case with source linked."""
        if source_id in self.source_ids:
            return self
        return self._evolve(source_ids=self.source_ids + (source_id,))

    def without_source(self, source_id: str) -> Case:
        """Return new Case with source unlinked."""
        return self._evolve(
            source_ids=tuple(s for s in self.source_ids if s != source_id),
        )

    def get_attribute(self, attr_name: str) -> CaseAttribute | None:
        """Get attribute by name."""
        for attr in self.attributes:
            if attr.name == attr_name:
                return attr
        return None
