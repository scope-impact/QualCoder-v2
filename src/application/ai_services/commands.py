"""
AI Services Commands - Command DTOs for AI operations.

These dataclasses represent the input for use case operations.
All commands are immutable (frozen) and contain only primitive types.
"""

from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# Code Suggestion Commands
# ============================================================


@dataclass(frozen=True)
class SuggestCodesCommand:
    """Command to request code suggestions for text."""

    text: str
    source_id: int
    max_suggestions: int = 5


@dataclass(frozen=True)
class ApproveCodeSuggestionCommand:
    """Command to approve a code suggestion and create the code."""

    suggestion_id: str
    name: str
    color: str  # hex color
    memo: str | None = None


@dataclass(frozen=True)
class RejectCodeSuggestionCommand:
    """Command to reject a code suggestion."""

    suggestion_id: str
    reason: str | None = None


# ============================================================
# Duplicate Detection Commands
# ============================================================


@dataclass(frozen=True)
class DetectDuplicatesCommand:
    """Command to detect duplicate codes."""

    threshold: float = 0.8


@dataclass(frozen=True)
class ApproveMergeCommand:
    """Command to approve merging duplicate codes."""

    source_code_id: int  # Code to merge from (will be deleted)
    target_code_id: int  # Code to merge into (will remain)


@dataclass(frozen=True)
class DismissMergeCommand:
    """Command to dismiss a merge suggestion."""

    code_a_id: int
    code_b_id: int
    reason: str | None = None
