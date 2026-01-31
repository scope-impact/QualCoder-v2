"""
Cases bounded context - Domain layer.

Provides entities, events, invariants, and derivers for managing cases
(participants, sites, organizations) in qualitative research.
"""

from src.domain.cases.derivers import (
    CaseNameTooLong,
    CaseNotFound,
    CaseState,
    DuplicateCaseName,
    EmptyCaseName,
    InvalidAttributeName,
    InvalidAttributeType,
    InvalidAttributeValue,
    derive_create_case,
    derive_remove_case,
    derive_set_case_attribute,
    derive_update_case,
)
from src.domain.cases.entities import (
    AttributeType,
    Case,
    CaseAttribute,
)
from src.domain.cases.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.domain.cases.invariants import (
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
