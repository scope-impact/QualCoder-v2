"""
Import Code List Use Case.

Parses a plain-text code list and creates codes/categories
by delegating to the coding context's create_code handler.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers.create_category import create_category
from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commands import CreateCategoryCommand, CreateCodeCommand
from src.contexts.exchange.core.commands import (
    DEFAULT_IMPORT_COLOR,
    ImportCodeListCommand,
)
from src.contexts.exchange.core.events import CodeListImported
from src.contexts.exchange.core.failure_events import ImportFailed
from src.contexts.exchange.infra.code_list_parser import parse_code_list
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.coding.core.commandHandlers._state import (
        CategoryRepository,
        CodeRepository,
        SegmentRepository,
    )
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.exchange.core")


def import_code_list(
    command: ImportCodeListCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Import codes from a plain-text code list.

    1. Read and parse the file
    2. Create categories first
    3. Create codes (delegating to create_code handler)
    4. Publish summary event
    """
    logger.debug("import_code_list: path=%s", command.source_path)

    # 1. Read file
    source_path = Path(command.source_path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failure = ImportFailed.file_not_found(command.source_path)
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)
    parsed = parse_code_list(text)

    if not parsed.codes and not parsed.categories:
        failure = ImportFailed.empty_list()
        event_bus.publish(failure)
        return OperationResult.from_failure(failure)

    # 2. Create categories (look up or create)
    category_name_to_id: dict[str, str] = {}
    categories_created = 0

    existing_categories = category_repo.get_all()
    existing_cat_names = {c.name.lower(): c for c in existing_categories}

    for parsed_cat in parsed.categories:
        lower_name = parsed_cat.name.lower()
        if lower_name in existing_cat_names:
            category_name_to_id[parsed_cat.name] = existing_cat_names[
                lower_name
            ].id.value
        else:
            cat_result = create_category(
                command=CreateCategoryCommand(name=parsed_cat.name),
                code_repo=code_repo,
                category_repo=category_repo,
                segment_repo=segment_repo,
                event_bus=event_bus,
                session=session,
            )
            if cat_result.is_success:
                category_name_to_id[parsed_cat.name] = cat_result.data.id.value
                categories_created += 1

    # 3. Create codes (reuse existing create_code handler)
    codes_created = 0
    codes_skipped = 0

    for parsed_code in parsed.codes:
        category_id = None
        if (
            parsed_code.category_name
            and parsed_code.category_name in category_name_to_id
        ):
            category_id = category_name_to_id[parsed_code.category_name]

        result = create_code(
            command=CreateCodeCommand(
                name=parsed_code.name,
                color=DEFAULT_IMPORT_COLOR,
                category_id=category_id,
            ),
            code_repo=code_repo,
            category_repo=category_repo,
            segment_repo=segment_repo,
            event_bus=event_bus,
            session=session,
        )

        if result.is_success:
            codes_created += 1
        else:
            codes_skipped += 1
            logger.debug("Skipped code '%s': %s", parsed_code.name, result.error)

    # 4. Publish summary event
    event = CodeListImported.create(
        source_path=command.source_path,
        codes_created=codes_created,
        codes_skipped=codes_skipped,
        categories_created=categories_created,
    )
    event_bus.publish(event)

    logger.info(
        "Code list imported: %d created, %d skipped, %d categories from %s",
        codes_created,
        codes_skipped,
        categories_created,
        command.source_path,
    )

    return OperationResult.ok(data=event)
