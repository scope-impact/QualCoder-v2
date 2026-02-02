"""
DEPRECATED: Use src.contexts.shared instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

# Re-export from new location
from src.contexts.shared.core.agent import AgentSession, TrustLevel
from src.contexts.shared.core.failure_events import AnyFailureEvent, FailureEvent
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
from src.contexts.shared.core.validation import (
    ValidationFailure,
    ValidationResult,
    ValidationSuccess,
    all_exist,
    has_no_references,
    is_acyclic_hierarchy,
    is_in_range,
    is_invalid,
    is_name_unique,
    is_non_empty_string,
    is_non_negative,
    is_positive,
    is_unique_in_collection,
    is_valid,
    is_valid_hex_color,
    is_valid_range,
    is_within_bounds,
    is_within_length,
    none_exist,
    validate_all,
    validate_field,
)
