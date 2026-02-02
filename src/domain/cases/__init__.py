"""
Cases bounded context - Domain layer.

DEPRECATED: This module re-exports from src.contexts.cases.core for backward compatibility.
Use src.contexts.cases.core directly in new code.
"""

from src.contexts.cases.core import (
    AttributeType,
    Case,
    CaseAttribute,
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseNameTooLong,
    CaseNotFound,
    CaseRemoved,
    CaseState,
    CaseUpdated,
    DuplicateCaseName,
    EmptyCaseName,
    InvalidAttributeName,
    InvalidAttributeType,
    InvalidAttributeValue,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
    derive_create_case,
    derive_link_source_to_case,
    derive_remove_case,
    derive_set_case_attribute,
    derive_unlink_source_from_case,
    derive_update_case,
    is_case_name_unique,
    is_valid_attribute_name,
    is_valid_attribute_type,
    is_valid_attribute_value,
    is_valid_case_name,
)

__all__ = [
    # Entities
    "Case",
    "CaseAttribute",
    "AttributeType",
    # Events
    "CaseCreated",
    "CaseUpdated",
    "CaseRemoved",
    "CaseAttributeSet",
    "CaseAttributeRemoved",
    "SourceLinkedToCase",
    "SourceUnlinkedFromCase",
    # Derivers
    "derive_create_case",
    "derive_update_case",
    "derive_remove_case",
    "derive_set_case_attribute",
    "derive_link_source_to_case",
    "derive_unlink_source_from_case",
    # State
    "CaseState",
    # Failure reasons
    "EmptyCaseName",
    "CaseNameTooLong",
    "DuplicateCaseName",
    "CaseNotFound",
    "InvalidAttributeType",
    "InvalidAttributeValue",
    "InvalidAttributeName",
    # Invariants
    "is_valid_case_name",
    "is_case_name_unique",
    "is_valid_attribute_type",
    "is_valid_attribute_name",
    "is_valid_attribute_value",
]
