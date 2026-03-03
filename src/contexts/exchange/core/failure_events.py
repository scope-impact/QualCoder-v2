"""
Exchange Context: Failure Events

Publishable failure events for import/export operations.
Event naming: {ENTITY}_NOT_{OPERATION}/{REASON}
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent


@dataclass(frozen=True)
class ExportFailed(FailureEvent):
    """An export operation failed."""

    suggestions: tuple[str, ...] = ()

    @classmethod
    def no_codes(cls) -> ExportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODEBOOK_NOT_EXPORTED/NO_CODES",
            suggestions=("Create codes before exporting", "Import a code list first"),
        )

    @classmethod
    def invalid_path(cls, path: str) -> ExportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODEBOOK_NOT_EXPORTED/INVALID_PATH",
            suggestions=("Provide a valid file path", "Ensure the directory exists"),
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        if "NO_CODES" in self.event_type:
            return "Cannot export codebook: no codes exist in the project"
        if "INVALID_PATH" in self.event_type:
            return "Cannot export codebook: invalid output path"
        return super().message


@dataclass(frozen=True)
class ImportFailed(FailureEvent):
    """An import operation failed."""

    suggestions: tuple[str, ...] = ()

    @classmethod
    def empty_list(cls) -> ImportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_LIST_NOT_IMPORTED/EMPTY_LIST",
            suggestions=("Provide a file with at least one code name",),
        )

    @classmethod
    def file_not_found(cls, path: str) -> ImportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_LIST_NOT_IMPORTED/FILE_NOT_FOUND",
            suggestions=(f"Check that the file exists: {path}",),
        )

    @classmethod
    def empty_csv(cls) -> ImportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CSV_NOT_IMPORTED/EMPTY",
            suggestions=("Provide a CSV file with a header row and data rows",),
        )

    @classmethod
    def csv_file_not_found(cls, path: str) -> ImportFailed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CSV_NOT_IMPORTED/FILE_NOT_FOUND",
            suggestions=(f"Check that the file exists: {path}",),
        )

    @property
    def message(self) -> str:
        if "EMPTY_LIST" in self.event_type:
            return "Cannot import code list: file contains no code names"
        if "EMPTY" in self.event_type and "CSV" in self.event_type:
            return "Cannot import CSV: file is empty or has no data rows"
        if "FILE_NOT_FOUND" in self.event_type:
            return "Cannot import: file not found"
        return super().message
