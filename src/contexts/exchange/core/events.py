"""
Exchange Context: Domain Events

Immutable records of import/export operations that happened.
Event type convention: exchange.{entity}_{action}
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.shared.common.types import DomainEvent


@dataclass(frozen=True)
class CodebookExported(DomainEvent):
    """A codebook was exported successfully."""

    event_type: ClassVar[str] = "exchange.codebook_exported"

    output_path: str
    code_count: int
    category_count: int
    include_memos: bool

    @classmethod
    def create(
        cls,
        output_path: str,
        code_count: int,
        category_count: int,
        include_memos: bool,
    ) -> CodebookExported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            output_path=output_path,
            code_count=code_count,
            category_count=category_count,
            include_memos=include_memos,
        )
