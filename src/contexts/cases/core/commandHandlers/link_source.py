"""
Link Source to Case Use Case

Functional use case for linking a source to a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import (
    CaseRepository,
    build_case_state,
    require_project,
)
from src.contexts.cases.core.derivers import derive_link_source_to_case
from src.contexts.cases.core.failure_events import SourceLinkFailed
from src.contexts.projects.core.commands import (
    LinkSourceToCaseCommand,
    UnlinkSourceFromCaseCommand,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId, SourceId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session
    from src.shared.infra.state import ProjectState


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("link_source_to_case")
def link_source_to_case(
    command: LinkSourceToCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """Link a source to a case."""
    logger.debug(
        "link_source_to_case: case_id=%s, source_id=%s",
        command.case_id,
        command.source_id,
    )
    if failure := require_project(state, "SOURCE_NOT_LINKED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)
    source_id = SourceId(value=command.source_id)

    result = derive_link_source_to_case(
        case_id=case_id,
        source_id=source_id,
        state=build_case_state(case_repo),
    )

    if isinstance(result, SourceLinkFailed):
        logger.error("link_source_to_case failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        case_repo.link_source(case_id, source_id, "")

    event_bus.publish(event)

    logger.info(
        "Source linked: case_id=%s, source_id=%s", command.case_id, command.source_id
    )
    return OperationResult.ok(
        data=event,
        rollback=UnlinkSourceFromCaseCommand(
            case_id=command.case_id, source_id=command.source_id
        ),
    )
