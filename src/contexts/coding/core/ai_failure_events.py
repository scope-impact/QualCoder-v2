"""
Coding Context: AI-Assisted Coding Failure Events

Publishable failure events for AI-assisted coding operations.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.contexts.coding.core.ai_entities import SuggestionId
from src.shared.common.failure_events import FailureEvent
from src.shared.common.types import CodeId

# ============================================================
# Code Suggestion Failure Events
# ============================================================


@dataclass(frozen=True)
class SuggestionNotCreated(FailureEvent):
    """Failure event: Code suggestion could not be created."""

    name: str | None = None
    confidence: float | None = None

    @classmethod
    def invalid_name(cls, name: str) -> SuggestionNotCreated:
        """Name is empty or invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_CREATED/INVALID_NAME",
            name=name,
        )

    @classmethod
    def duplicate_name(cls, name: str) -> SuggestionNotCreated:
        """Name conflicts with existing code."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_CREATED/DUPLICATE_NAME",
            name=name,
        )

    @classmethod
    def invalid_confidence(cls, confidence: float) -> SuggestionNotCreated:
        """Confidence value out of range."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_CREATED/INVALID_CONFIDENCE",
            confidence=confidence,
        )

    @classmethod
    def invalid_rationale(cls) -> SuggestionNotCreated:
        """Rationale is empty or too long."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_CREATED/INVALID_RATIONALE",
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "INVALID_NAME":
                return f"Invalid suggestion name: '{self.name}'"
            case "DUPLICATE_NAME":
                return f"Code with name '{self.name}' already exists"
            case "INVALID_CONFIDENCE":
                return f"Confidence must be 0.0-1.0, got {self.confidence}"
            case "INVALID_RATIONALE":
                return "Rationale must be 1-1000 characters"
            case _:
                return super().message


@dataclass(frozen=True)
class SuggestionNotApproved(FailureEvent):
    """Failure event: Code suggestion could not be approved."""

    suggestion_id: SuggestionId | None = None
    name: str | None = None
    status: str | None = None

    @classmethod
    def not_found(cls, suggestion_id: SuggestionId) -> SuggestionNotApproved:
        """Suggestion was not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_APPROVED/NOT_FOUND",
            suggestion_id=suggestion_id,
        )

    @classmethod
    def not_pending(
        cls, suggestion_id: SuggestionId, status: str
    ) -> SuggestionNotApproved:
        """Suggestion is not in pending status."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_APPROVED/NOT_PENDING",
            suggestion_id=suggestion_id,
            status=status,
        )

    @classmethod
    def duplicate_name(cls, name: str) -> SuggestionNotApproved:
        """Final name conflicts with existing code."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_APPROVED/DUPLICATE_NAME",
            name=name,
        )

    @classmethod
    def invalid_name(cls, name: str) -> SuggestionNotApproved:
        """Final name is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_APPROVED/INVALID_NAME",
            name=name,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                sid = self.suggestion_id.value if self.suggestion_id else "unknown"
                return f"Suggestion {sid} not found"
            case "NOT_PENDING":
                sid = self.suggestion_id.value if self.suggestion_id else "unknown"
                return f"Suggestion {sid} is {self.status}, not pending"
            case "DUPLICATE_NAME":
                return f"Code with name '{self.name}' already exists"
            case "INVALID_NAME":
                return f"Invalid name: '{self.name}'"
            case _:
                return super().message


@dataclass(frozen=True)
class SuggestionNotRejected(FailureEvent):
    """Failure event: Code suggestion could not be rejected."""

    suggestion_id: SuggestionId | None = None
    status: str | None = None

    @classmethod
    def not_found(cls, suggestion_id: SuggestionId) -> SuggestionNotRejected:
        """Suggestion was not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_REJECTED/NOT_FOUND",
            suggestion_id=suggestion_id,
        )

    @classmethod
    def not_pending(
        cls, suggestion_id: SuggestionId, status: str
    ) -> SuggestionNotRejected:
        """Suggestion is not in pending status."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SUGGESTION_NOT_REJECTED/NOT_PENDING",
            suggestion_id=suggestion_id,
            status=status,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                sid = self.suggestion_id.value if self.suggestion_id else "unknown"
                return f"Suggestion {sid} not found"
            case "NOT_PENDING":
                sid = self.suggestion_id.value if self.suggestion_id else "unknown"
                return f"Suggestion {sid} is {self.status}, not pending"
            case _:
                return super().message


# ============================================================
# Duplicate Detection Failure Events
# ============================================================


@dataclass(frozen=True)
class DuplicatesNotDetected(FailureEvent):
    """Failure event: Duplicate detection could not be performed."""

    threshold: float | None = None
    count: int | None = None
    minimum: int | None = None

    @classmethod
    def invalid_threshold(cls, threshold: float) -> DuplicatesNotDetected:
        """Threshold value out of range."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="DUPLICATES_NOT_DETECTED/INVALID_THRESHOLD",
            threshold=threshold,
        )

    @classmethod
    def insufficient_codes(cls, count: int, minimum: int) -> DuplicatesNotDetected:
        """Not enough codes for detection."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="DUPLICATES_NOT_DETECTED/INSUFFICIENT_CODES",
            count=count,
            minimum=minimum,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "INVALID_THRESHOLD":
                return f"Threshold must be 0.0-1.0, got {self.threshold}"
            case "INSUFFICIENT_CODES":
                return f"Need at least {self.minimum} codes, have {self.count}"
            case _:
                return super().message


# ============================================================
# Merge Failure Events
# ============================================================


@dataclass(frozen=True)
class MergeNotCreated(FailureEvent):
    """Failure event: Merge suggestion could not be created."""

    code_id: CodeId | None = None

    @classmethod
    def code_not_found(cls, code_id: CodeId) -> MergeNotCreated:
        """Code was not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="MERGE_NOT_CREATED/CODE_NOT_FOUND",
            code_id=code_id,
        )

    @classmethod
    def invalid_rationale(cls) -> MergeNotCreated:
        """Rationale is empty or too long."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="MERGE_NOT_CREATED/INVALID_RATIONALE",
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "CODE_NOT_FOUND":
                cid = self.code_id.value if self.code_id else "unknown"
                return f"Code {cid} not found for merge"
            case "INVALID_RATIONALE":
                return "Rationale must be 1-1000 characters"
            case _:
                return super().message


@dataclass(frozen=True)
class MergeNotApproved(FailureEvent):
    """Failure event: Merge could not be approved."""

    code_id: CodeId | None = None

    @classmethod
    def code_not_found(cls, code_id: CodeId) -> MergeNotApproved:
        """Code was not found."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="MERGE_NOT_APPROVED/CODE_NOT_FOUND",
            code_id=code_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "CODE_NOT_FOUND":
                cid = self.code_id.value if self.code_id else "unknown"
                return f"Code {cid} not found for merge"
            case _:
                return super().message


@dataclass(frozen=True)
class MergeNotDismissed(FailureEvent):
    """Failure event: Merge could not be dismissed."""

    code_a_id: CodeId | None = None
    code_b_id: CodeId | None = None
    status: str | None = None

    @classmethod
    def not_pending(
        cls, code_a_id: CodeId, code_b_id: CodeId, status: str
    ) -> MergeNotDismissed:
        """Duplicate pair is not in pending status."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="MERGE_NOT_DISMISSED/NOT_PENDING",
            code_a_id=code_a_id,
            code_b_id=code_b_id,
            status=status,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_PENDING":
                a_id = self.code_a_id.value if self.code_a_id else "unknown"
                b_id = self.code_b_id.value if self.code_b_id else "unknown"
                return f"Duplicate pair ({a_id}, {b_id}) is {self.status}"
            case _:
                return super().message


# ============================================================
# Type Aliases
# ============================================================

SuggestionFailureEvent = (
    SuggestionNotCreated | SuggestionNotApproved | SuggestionNotRejected
)

MergeFailureEvent = MergeNotCreated | MergeNotApproved | MergeNotDismissed

AICodingFailureEvent = (
    SuggestionFailureEvent | DuplicatesNotDetected | MergeFailureEvent
)
