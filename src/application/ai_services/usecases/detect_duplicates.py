"""
Detect Duplicates Use Case

Query use case for detecting potentially duplicate codes.
This is a pure query - no database side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import DetectDuplicatesCommand
from src.contexts.ai_services.core.entities import DetectionId, DuplicateCandidate
from src.contexts.ai_services.core.events import DuplicatesDetected

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.ai_services.core.protocols import CodeComparatorProtocol
    from src.contexts.coding.core.entities import Code


def detect_duplicates(
    command: DetectDuplicatesCommand,
    code_comparator: CodeComparatorProtocol,
    existing_codes: tuple[Code, ...],
    event_bus: EventBus,
) -> Result[list[DuplicateCandidate], str]:
    """
    Detect potentially duplicate codes using AI comparison.

    This is a query use case - no database persistence.
    Candidates are returned to the caller (typically ViewModel)
    for user review before merge approval.

    Args:
        command: Command with detection threshold
        code_comparator: AI service for comparing codes
        existing_codes: All codes to compare
        event_bus: Event bus for publishing detection event

    Returns:
        Success with list of duplicate candidates, or Failure with error
    """
    # Step 1: Validate
    if command.threshold < 0.0 or command.threshold > 1.0:
        return Failure("Threshold must be between 0.0 and 1.0")

    if len(existing_codes) < 2:
        return Success([])

    # Step 2: Call AI service (infrastructure)
    result = code_comparator.find_duplicates(
        codes=existing_codes,
        threshold=command.threshold,
    )

    if isinstance(result, Failure):
        return result

    candidates = result.unwrap()

    # Step 3: Publish detection event
    if candidates:
        event = DuplicatesDetected.create(
            detection_id=DetectionId.new(),
            candidates=tuple(candidates),
            threshold=command.threshold,
            codes_analyzed=len(existing_codes),
        )
        event_bus.publish(event)

    return Success(candidates)
