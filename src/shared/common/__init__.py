"""
Shared common types and utilities.

Contains fundamental types used across all bounded contexts.
"""

from src.shared.common.agent import AgentSession, TrustLevel
from src.shared.common.failure_events import FailureEvent
from src.shared.common.mcp_types import ToolDefinition, ToolParameter
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import (
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
    "DomainEvent",
    # Failure reasons
    "FailureReason",
    "DuplicateName",
    "CodeNotFound",
    "SourceNotFound",
    "InvalidPosition",
    "EmptyName",
    "FolderNotFound",
    # Agent
    "AgentSession",
    "TrustLevel",
    # MCP types
    "ToolDefinition",
    "ToolParameter",
]
