"""
Cases bounded context - Domain layer (Core).

Provides entities, events, invariants, and derivers for managing cases
(participants, sites, organizations) in qualitative research.
"""

from src.contexts.cases.core.derivers import (
    CaseState,
    derive_create_case,
    derive_link_source_to_case,
    derive_remove_case,
    derive_remove_case_attribute,
    derive_set_case_attribute,
    derive_unlink_source_from_case,
    derive_update_case,
)
from src.contexts.cases.core.entities import (
    AttributeType,
    Case,
    CaseAttribute,
)
from src.contexts.cases.core.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.contexts.cases.core.failure_events import (
    AttributeRemovalFailed,
    AttributeSetFailed,
    CaseCreationFailed,
    CaseDeletionFailed,
    CaseUpdateFailed,
    SourceLinkFailed,
    SourceUnlinkFailed,
)
from src.contexts.cases.core.invariants import (
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
    # Failure Events
    "CaseCreationFailed",
    "CaseUpdateFailed",
    "CaseDeletionFailed",
    "AttributeSetFailed",
    "AttributeRemovalFailed",
    "SourceLinkFailed",
    "SourceUnlinkFailed",
    # Derivers
    "derive_create_case",
    "derive_update_case",
    "derive_remove_case",
    "derive_set_case_attribute",
    "derive_remove_case_attribute",
    "derive_link_source_to_case",
    "derive_unlink_source_from_case",
    # State
    "CaseState",
    # Invariants
    "is_valid_case_name",
    "is_case_name_unique",
    "is_valid_attribute_type",
    "is_valid_attribute_name",
    "is_valid_attribute_value",
]
