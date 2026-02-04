"""
Shared kernel - cross-cutting concerns only.

This module contains infrastructure and utilities that span multiple bounded contexts.
Following ddd-workshop pattern, this is the ONLY place for cross-context code.
"""

from src.shared.common.agent import AgentSession, TrustLevel
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import (
    CaseId,
    CategoryId,
    CodeId,
    Failure,
    FailureReason,
    FolderId,
    Result,
    SegmentId,
    SourceId,
    Success,
)

__all__ = [
    # Type IDs
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
    "OperationResult",
    # Events
    "FailureEvent",
    "FailureReason",
    # Agent
    "AgentSession",
    "TrustLevel",
]
