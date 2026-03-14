"""
Import Survey CSV Use Case.

Parses a CSV file and creates cases with attributes
from each row. First column (or specified column) becomes the case name.

Supports:
- Type inference: auto-detects NUMBER, DATE, BOOLEAN, TEXT
- Case merge: updates existing cases instead of creating duplicates
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.cases.core.entities import Case, CaseAttribute
from src.contexts.cases.core.events import CaseCreated
from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
from src.contexts.exchange.core.events import SurveyCSVImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.csv_parser import (
    infer_column_types,
    parse_survey_csv,
)
from src.shared import CaseId
from src.shared.common.operation_result import OperationResult
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.contexts.cases.core.commandHandlers._state import CaseRepository
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.exchange.core")


@metered_command("import_survey_csv")
def import_survey_csv(
    command: ImportSurveyCSVCommand,
    case_repo: CaseRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Import survey data from a CSV file.

    1. Read and parse CSV
    2. Infer attribute types per column
    3. Create or merge cases from rows
    4. Publish event
    """
    logger.debug("import_survey_csv: path=%s", command.source_path)

    source_path = Path(command.source_path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failure = ImportFailed.csv_file_not_found(command.source_path)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)
    parsed = parse_survey_csv(text, name_column=command.name_column)

    if not parsed.rows:
        failure = ImportFailed.empty_csv()
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    name_col = parsed.name_column
    attribute_columns = [h for h in parsed.headers if h != name_col]

    # Infer types for each attribute column
    column_types = infer_column_types(parsed)

    cases_created = 0
    cases_updated = 0

    for row in parsed.rows:
        case_name = row.get(name_col, "").strip() if name_col else ""
        if not case_name:
            continue

        # Build typed attributes from remaining columns
        attributes = []
        for col in attribute_columns:
            value = row.get(col, "")
            if value:
                attr_type = column_types.get(col)
                attributes.append(
                    CaseAttribute(
                        name=col,
                        attr_type=attr_type,
                        value=value,
                    )
                )

        # Check for existing case (merge behavior)
        existing = case_repo.get_by_name(case_name)
        if existing is not None:
            # Merge: update/add attributes on existing case
            for attr in attributes:
                case_repo.save_attribute(existing.id, attr)
            cases_updated += 1
        else:
            # Create new case
            case = Case(
                id=CaseId.new(),
                name=case_name,
                attributes=tuple(attributes),
            )
            case_repo.save(case)
            event_bus.publish(CaseCreated.create(name=case_name, case_id=case.id))
            cases_created += 1

    event = SurveyCSVImported.create(
        source_path=command.source_path,
        cases_created=cases_created,
        attributes_per_case=len(attribute_columns),
        cases_updated=cases_updated,
    )
    event_bus.publish(event)

    logger.info(
        "Survey CSV imported: %d created, %d updated, %d attributes each from %s",
        cases_created,
        cases_updated,
        len(attribute_columns),
        command.source_path,
    )

    return OperationResult.ok(data=event)
