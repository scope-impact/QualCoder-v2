"""
References Context: Domain Entities

Immutable entities representing academic references in qualitative research.
References store bibliographic information and can be linked to coded segments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.shared.types import ReferenceId


@dataclass(frozen=True)
class Reference:
    """
    Reference entity - Aggregate root for the References context.

    A reference represents a bibliographic entry (article, book, etc.)
    that can be linked to coded segments for citation purposes.
    """

    id: ReferenceId
    title: str
    authors: str
    year: int | None = None
    source: str | None = None  # Journal, publisher, etc.
    doi: str | None = None
    url: str | None = None
    memo: str | None = None
    segment_ids: tuple[int, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def with_title(self, new_title: str) -> Reference:
        """Return new Reference with updated title."""
        return Reference(
            id=self.id,
            title=new_title,
            authors=self.authors,
            year=self.year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=self.memo,
            segment_ids=self.segment_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_authors(self, new_authors: str) -> Reference:
        """Return new Reference with updated authors."""
        return Reference(
            id=self.id,
            title=self.title,
            authors=new_authors,
            year=self.year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=self.memo,
            segment_ids=self.segment_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_year(self, new_year: int | None) -> Reference:
        """Return new Reference with updated year."""
        return Reference(
            id=self.id,
            title=self.title,
            authors=self.authors,
            year=new_year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=self.memo,
            segment_ids=self.segment_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_memo(self, new_memo: str | None) -> Reference:
        """Return new Reference with updated memo."""
        return Reference(
            id=self.id,
            title=self.title,
            authors=self.authors,
            year=self.year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=new_memo,
            segment_ids=self.segment_ids,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def with_segment(self, segment_id: int) -> Reference:
        """Return new Reference with segment linked."""
        if segment_id in self.segment_ids:
            return self
        return Reference(
            id=self.id,
            title=self.title,
            authors=self.authors,
            year=self.year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=self.memo,
            segment_ids=self.segment_ids + (segment_id,),
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )

    def without_segment(self, segment_id: int) -> Reference:
        """Return new Reference with segment unlinked."""
        return Reference(
            id=self.id,
            title=self.title,
            authors=self.authors,
            year=self.year,
            source=self.source,
            doi=self.doi,
            url=self.url,
            memo=self.memo,
            segment_ids=tuple(s for s in self.segment_ids if s != segment_id),
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )
