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


@dataclass(frozen=True)
class CodeListImported(DomainEvent):
    """A code list was imported successfully."""

    event_type: ClassVar[str] = "exchange.code_list_imported"

    source_path: str
    codes_created: int
    codes_skipped: int
    categories_created: int

    @classmethod
    def create(
        cls,
        source_path: str,
        codes_created: int,
        codes_skipped: int,
        categories_created: int,
    ) -> CodeListImported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_path=source_path,
            codes_created=codes_created,
            codes_skipped=codes_skipped,
            categories_created=categories_created,
        )


@dataclass(frozen=True)
class SurveyCSVImported(DomainEvent):
    """Survey CSV data was imported successfully."""

    event_type: ClassVar[str] = "exchange.survey_csv_imported"

    source_path: str
    cases_created: int
    attributes_per_case: int

    @classmethod
    def create(
        cls,
        source_path: str,
        cases_created: int,
        attributes_per_case: int,
    ) -> SurveyCSVImported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_path=source_path,
            cases_created=cases_created,
            attributes_per_case=attributes_per_case,
        )


@dataclass(frozen=True)
class CodedHTMLExported(DomainEvent):
    """Coded text was exported as HTML."""

    event_type: ClassVar[str] = "exchange.coded_html_exported"

    output_path: str
    source_count: int
    segment_count: int

    @classmethod
    def create(
        cls,
        output_path: str,
        source_count: int,
        segment_count: int,
    ) -> CodedHTMLExported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            output_path=output_path,
            source_count=source_count,
            segment_count=segment_count,
        )


@dataclass(frozen=True)
class RefiQdaExported(DomainEvent):
    """Project exported in REFI-QDA format."""

    event_type: ClassVar[str] = "exchange.refi_qda_exported"

    output_path: str
    code_count: int
    source_count: int
    segment_count: int

    @classmethod
    def create(
        cls,
        output_path: str,
        code_count: int,
        source_count: int,
        segment_count: int,
    ) -> RefiQdaExported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            output_path=output_path,
            code_count=code_count,
            source_count=source_count,
            segment_count=segment_count,
        )


@dataclass(frozen=True)
class RefiQdaImported(DomainEvent):
    """Project imported from REFI-QDA format."""

    event_type: ClassVar[str] = "exchange.refi_qda_imported"

    source_path: str
    codes_created: int
    sources_created: int
    segments_created: int

    @classmethod
    def create(
        cls,
        source_path: str,
        codes_created: int,
        sources_created: int,
        segments_created: int,
    ) -> RefiQdaImported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_path=source_path,
            codes_created=codes_created,
            sources_created=sources_created,
            segments_created=segments_created,
        )


@dataclass(frozen=True)
class RqdaImported(DomainEvent):
    """Project imported from RQDA format."""

    event_type: ClassVar[str] = "exchange.rqda_imported"

    source_path: str
    codes_created: int
    sources_created: int
    segments_created: int

    @classmethod
    def create(
        cls,
        source_path: str,
        codes_created: int,
        sources_created: int,
        segments_created: int,
    ) -> RqdaImported:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_path=source_path,
            codes_created=codes_created,
            sources_created=sources_created,
            segments_created=segments_created,
        )
