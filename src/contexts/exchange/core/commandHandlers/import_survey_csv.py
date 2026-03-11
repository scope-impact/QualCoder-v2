"""
Import Survey CSV Use Case.

Parses a CSV file and creates cases with attributes
from each row. First column (or specified column) becomes the case name.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.core.events import CaseCreated
from src.contexts.exchange.core.commands import ImportSurveyCSVCommand
from src.contexts.exchange.core.events import SurveyCSVImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.csv_parser import parse_survey_csv
from src.shared import CaseId
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.cases.core.commandHandlers._state import CaseRepository
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.exchange.core")


def import_survey_csv(
    command: ImportSurveyCSVCommand,
    case_repo: CaseRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Import survey data from a CSV file.

    1. Read and parse CSV
    2. Create cases from rows
    3. Add attributes from columns
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
    cases_created = 0

    for row in parsed.rows:
        case_name = row.get(name_col, "").strip() if name_col else ""
        if not case_name:
            continue

        # Build attributes from remaining columns
        attributes = []
        for col in attribute_columns:
            value = row.get(col, "")
            if value:
                attributes.append(
                    CaseAttribute(
                        name=col,
                        attr_type=AttributeType.TEXT,
                        value=value,
                    )
                )

        case = Case(
            id=CaseId.new(),
            name=case_name,
            attributes=tuple(attributes),
        )
        case_repo.save(case)
        event_bus.publish(CaseCreated.create(name=case_name, case_id=case.id))
        cases_created += 1

    if session:
        session.commit()

    event = SurveyCSVImported.create(
        source_path=command.source_path,
        cases_created=cases_created,
        attributes_per_case=len(attribute_columns),
    )
    event_bus.publish(event)

    logger.info(
        "Survey CSV imported: %d cases, %d attributes each from %s",
        cases_created,
        len(attribute_columns),
        command.source_path,
    )

    return OperationResult.ok(data=event)
