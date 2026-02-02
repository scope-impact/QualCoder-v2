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

from src.contexts.shared import CaseId


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
    source_ids: tuple[int, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_name(self, new_name: str) -> Case:
        """Return new Case with updated name."""
        return Case(
            id=self.id,
            name=new_name,
            description=self.description,
            memo=self.memo,
            attributes=self.attributes,
            source_ids=self.source_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_description(self, new_description: str | None) -> Case:
        """Return new Case with updated description."""
        return Case(
            id=self.id,
            name=self.name,
            description=new_description,
            memo=self.memo,
            attributes=self.attributes,
            source_ids=self.source_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_memo(self, new_memo: str | None) -> Case:
        """Return new Case with updated memo."""
        return Case(
            id=self.id,
            name=self.name,
            description=self.description,
            memo=new_memo,
            attributes=self.attributes,
            source_ids=self.source_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_attribute(self, attribute: CaseAttribute) -> Case:
        """Return new Case with added/updated attribute."""
        # Remove existing attribute with same name, then add new one
        filtered = tuple(a for a in self.attributes if a.name != attribute.name)
        return Case(
            id=self.id,
            name=self.name,
            description=self.description,
            memo=self.memo,
            attributes=filtered + (attribute,),
            source_ids=self.source_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def without_attribute(self, attr_name: str) -> Case:
        """Return new Case with attribute removed."""
        return Case(
            id=self.id,
            name=self.name,
            description=self.description,
            memo=self.memo,
            attributes=tuple(a for a in self.attributes if a.name != attr_name),
            source_ids=self.source_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_source(self, source_id: int) -> Case:
        """Return new Case with source linked."""
        if source_id in self.source_ids:
            return self
        return Case(
            id=self.id,
            name=self.name,
            description=self.description,
            memo=self.memo,
            attributes=self.attributes,
            source_ids=self.source_ids + (source_id,),
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def without_source(self, source_id: int) -> Case:
        """Return new Case with source unlinked."""
        return Case(
            id=self.id,
            name=self.name,
            description=self.description,
            memo=self.memo,
            attributes=self.attributes,
            source_ids=tuple(s for s in self.source_ids if s != source_id),
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def get_attribute(self, attr_name: str) -> CaseAttribute | None:
        """Get attribute by name."""
        for attr in self.attributes:
            if attr.name == attr_name:
                return attr
        return None
