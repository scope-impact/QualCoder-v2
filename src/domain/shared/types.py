"""
DEPRECATED: Use src.contexts.shared.core.types instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.shared.core.types import (
    CaseId,
    CategoryId,
    CodeId,
    CodeNotFound,
    DomainEvent,
    DuplicateName,
    EmptyName,
    Failure,
    FailureReason,
    FolderId,
    FolderNotFound,
    InvalidPosition,
    Result,
    SegmentId,
    SourceId,
    SourceNotFound,
    Success,
)

__all__ = [
    # Typed Identifiers
    "CodeId",
    "SegmentId",
    "SourceId",
    "CategoryId",
    "CaseId",
    "FolderId",
    # Result types
    "Success",
    "Failure",
    "Result",
    # Base Domain Event
    "DomainEvent",
    # Failure Reasons
    "DuplicateName",
    "CodeNotFound",
    "SourceNotFound",
    "InvalidPosition",
    "EmptyName",
    "FolderNotFound",
    "FailureReason",
]
