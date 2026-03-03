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
