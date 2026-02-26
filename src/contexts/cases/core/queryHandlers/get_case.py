"""
Get Case Use Case (Query)

Functional query use case for getting a single case by ID.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.cases.core.commandHandlers._state import (
    CaseRepository,
    require_project,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.state import ProjectState


def get_case(
    case_id: str,
    state: ProjectState,
    case_repo: CaseRepository | None = None,
) -> OperationResult:
    """Get a single case by ID."""
    if failure := require_project(state, "CASE_NOT_FOUND/NO_PROJECT"):
        return failure

    case = case_repo.get_by_id(CaseId(value=case_id)) if case_repo else None

    if case is None:
        return OperationResult.fail(
            error=f"Case with id {case_id} not found",
            error_code="CASE_NOT_FOUND/NOT_FOUND",
            suggestions=(
                "Use list_cases to see available cases",
                "Check if the case ID is correct",
            ),
        )

    return OperationResult.ok(
        data={
            "case_id": case.id.value,
            "name": case.name,
            "description": case.description,
            "memo": case.memo,
            "attributes": [
                {
                    "name": attr.name,
                    "type": attr.attr_type.value,
                    "value": attr.value,
                }
                for attr in case.attributes
            ],
            "source_count": len(case.source_ids),
            "source_ids": list(case.source_ids),
        }
    )
