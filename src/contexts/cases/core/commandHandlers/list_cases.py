"""
List Cases Use Case (Query)

Functional query use case for listing all cases.
Returns OperationResult for consistent handling in UI and AI consumers.
"""

from __future__ import annotations

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.shared.common.operation_result import OperationResult
from src.shared.infra.state import ProjectState


def list_cases(
    state: ProjectState,
    case_repo: CaseRepository | None = None,
) -> OperationResult:
    """
    List all cases in the current project.

    Args:
        state: Project state (for project check)
        case_repo: Repository for case queries (source of truth)

    Returns:
        OperationResult with list of Case entities on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="CASES_NOT_LISTED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Get cases from repo (source of truth)
    cases = case_repo.get_all() if case_repo else []

    return OperationResult.ok(
        data={
            "total_count": len(cases),
            "cases": [
                {
                    "case_id": c.id.value,
                    "name": c.name,
                    "description": c.description,
                    "attribute_count": len(c.attributes),
                    "source_count": len(c.source_ids),
                }
                for c in cases
            ],
        }
    )
