"""
DEPRECATED: Use src.contexts.cases.core.derivers instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.cases.core.derivers import (
    CaseNameTooLong,
    CaseNotFound,
    CaseState,
    DuplicateCaseName,
    EmptyCaseName,
    InvalidAttributeName,
    InvalidAttributeType,
    InvalidAttributeValue,
    SourceAlreadyLinked,
    SourceNotLinked,
    derive_create_case,
    derive_link_source_to_case,
    derive_remove_case,
    derive_set_case_attribute,
    derive_unlink_source_from_case,
    derive_update_case,
)

__all__ = [
    # State Container
    "CaseState",
    # Failure Reasons
    "EmptyCaseName",
    "CaseNameTooLong",
    "DuplicateCaseName",
    "CaseNotFound",
    "InvalidAttributeType",
    "InvalidAttributeValue",
    "InvalidAttributeName",
    "SourceAlreadyLinked",
    "SourceNotLinked",
    # Derivers
    "derive_create_case",
    "derive_update_case",
    "derive_remove_case",
    "derive_set_case_attribute",
    "derive_link_source_to_case",
    "derive_unlink_source_from_case",
]
