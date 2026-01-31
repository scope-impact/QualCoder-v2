"""Shared domain types and validation utilities"""

from src.domain.shared.agent import AgentSession, TrustLevel
from src.domain.shared.types import (
    CategoryId,
    CodeId,
    CodeNotFound,
    DomainEvent,
    DuplicateName,
    EmptyName,
    Failure,
    InvalidPosition,
    Result,
    SegmentId,
    SourceId,
    SourceNotFound,
    Success,
)
from src.domain.shared.validation import (
    ValidationFailure,
    ValidationResult,
    ValidationSuccess,
    is_acyclic_hierarchy,
    is_invalid,
    is_name_unique,
    is_non_empty_string,
    is_unique_in_collection,
    is_valid,
    is_valid_hex_color,
    is_valid_range,
    is_within_bounds,
    is_within_length,
    validate_all,
    validate_field,
)
