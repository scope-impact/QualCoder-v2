"""
Shared state building for cases use cases.

Following DDD workshop pattern: handlers receive specific repositories,
not entire bounded contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case, CaseAttribute
    from src.shared.common.types import CaseId, SourceId


# ============================================================
# Repository Protocol (for DI)
# ============================================================


@runtime_checkable
class CaseRepository(Protocol):
    """Protocol for case repository operations needed by command handlers."""

    def get_all(self) -> list[Case]: ...
    def get_by_id(self, case_id: CaseId) -> Case | None: ...
    def save(self, case: Case) -> None: ...
    def delete(self, case_id: CaseId) -> None: ...
    def link_source(
        self, case_id: CaseId, source_id: SourceId, source_name: str
    ) -> None: ...
    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> None: ...
    def save_attribute(self, case_id: CaseId, attribute: CaseAttribute) -> None: ...
    def delete_attribute(self, case_id: CaseId, attr_name: str) -> None: ...
