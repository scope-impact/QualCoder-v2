"""
Category and Code Management Tool Handlers

Handlers for: create_category, move_code_to_category, list_categories,
merge_codes, rename_code, update_code_memo, delete_code.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.commandHandlers import (
    create_category,
    delete_code,
    get_all_categories,
    merge_codes,
    move_code_to_category,
    rename_code,
    update_code_memo,
)
from src.contexts.coding.core.commands import (
    CreateCategoryCommand,
    DeleteCodeCommand,
    MergeCodesCommand,
    MoveCodeToCategoryCommand,
    RenameCodeCommand,
    UpdateCodeMemoCommand,
)
from src.contexts.coding.core.entities import Category
from src.shared.common.operation_result import OperationResult

from .base import HandlerContext, missing_param_error, no_context_error


def _serialize_category(category: Category, code_count: int = 0) -> dict[str, Any]:
    """Serialize Category entity to JSON-compatible dict."""
    return {
        "id": category.id.value,
        "name": category.name,
        "parent_id": category.parent_id.value if category.parent_id else None,
        "memo": category.memo,
        "owner": category.owner,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "code_count": code_count,
    }


def handle_rename_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Rename an existing code via the rename_code command handler."""
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("RENAME_CODE", "code_id")

    new_name = arguments.get("new_name")
    if new_name is None:
        return missing_param_error("RENAME_CODE", "new_name")

    if ctx.code_repo is None:
        return no_context_error("RENAME_CODE")

    command = RenameCodeCommand(code_id=str(code_id), new_name=str(new_name))
    result = rename_code(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        event = result.data
        return OperationResult.ok(
            data={
                "code_id": str(code_id),
                "old_name": event.old_name,
                "new_name": event.new_name,
            }
        ).to_dict()

    return result.to_dict()


def handle_update_code_memo(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Update a code's memo via the update_code_memo command handler."""
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("UPDATE_CODE_MEMO", "code_id")

    memo = arguments.get("memo")
    # memo can be None (to clear it), so we don't validate it

    if ctx.code_repo is None:
        return no_context_error("UPDATE_CODE_MEMO")

    command = UpdateCodeMemoCommand(code_id=str(code_id), new_memo=memo)
    result = update_code_memo(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        event = result.data
        return OperationResult.ok(
            data={
                "code_id": str(code_id),
                "old_memo": event.old_memo,
                "new_memo": event.new_memo,
            }
        ).to_dict()

    return result.to_dict()


def handle_create_category(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Create a new category via the create_category command handler."""
    name = arguments.get("name")
    if name is None:
        return missing_param_error("CREATE_CATEGORY", "name")

    if ctx.category_repo is None:
        return no_context_error("CREATE_CATEGORY")

    parent_id_raw = arguments.get("parent_id")
    command = CreateCategoryCommand(
        name=str(name),
        parent_id=str(parent_id_raw) if parent_id_raw is not None else None,
        memo=arguments.get("memo"),
    )

    result = create_category(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        category = result.data
        return OperationResult.ok(
            data={
                "category_id": category.id.value,
                "name": category.name,
                "parent_id": category.parent_id.value if category.parent_id else None,
                "memo": category.memo,
            }
        ).to_dict()

    return result.to_dict()


def handle_move_code_to_category(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Move a code to a category via the move_code_to_category command handler."""
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("MOVE_CODE_TO_CATEGORY", "code_id")

    if ctx.code_repo is None:
        return no_context_error("MOVE_CODE_TO_CATEGORY")

    # category_id can be None (to uncategorize)
    category_id_raw = arguments.get("category_id")
    command = MoveCodeToCategoryCommand(
        code_id=str(code_id),
        category_id=str(category_id_raw) if category_id_raw is not None else None,
    )

    result = move_code_to_category(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        event = result.data
        return OperationResult.ok(
            data={
                "code_id": str(code_id),
                "old_category_id": (
                    event.old_category_id.value if event.old_category_id else None
                ),
                "new_category_id": (
                    event.new_category_id.value if event.new_category_id else None
                ),
            }
        ).to_dict()

    return result.to_dict()


def handle_merge_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Merge source code into target code via the merge_codes command handler."""
    source_code_id = arguments.get("source_code_id")
    if source_code_id is None:
        return missing_param_error("MERGE_CODES", "source_code_id")

    target_code_id = arguments.get("target_code_id")
    if target_code_id is None:
        return missing_param_error("MERGE_CODES", "target_code_id")

    if ctx.code_repo is None:
        return no_context_error("MERGE_CODES")

    command = MergeCodesCommand(
        source_code_id=str(source_code_id),
        target_code_id=str(target_code_id),
    )

    result = merge_codes(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        event = result.data
        return OperationResult.ok(
            data={
                "source_code_id": str(source_code_id),
                "target_code_id": str(target_code_id),
                "source_code_name": event.source_code_name,
                "target_code_name": event.target_code_name,
                "segments_moved": event.segments_moved,
            }
        ).to_dict()

    return result.to_dict()


def handle_delete_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Delete a code via the delete_code command handler."""
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("DELETE_CODE", "code_id")

    if ctx.code_repo is None:
        return no_context_error("DELETE_CODE")

    command = DeleteCodeCommand(
        code_id=str(code_id),
        delete_segments=bool(arguments.get("delete_segments", False)),
    )

    result = delete_code(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success and result.data:
        event = result.data
        return OperationResult.ok(
            data={
                "code_id": str(code_id),
                "name": event.name,
                "segments_removed": event.segments_removed,
                "deleted": True,
            }
        ).to_dict()

    return result.to_dict()


def handle_list_categories(
    ctx: HandlerContext,
    _arguments: dict[str, Any],
) -> dict[str, Any]:
    """Return all categories with hierarchy and code counts."""
    if ctx.category_repo is None:
        return no_context_error("LIST_CATEGORIES")

    categories = get_all_categories(ctx.category_repo)

    # Count codes per category
    code_counts: dict[str, int] = {}
    if ctx.code_repo is not None:
        from src.contexts.coding.core.commandHandlers import get_all_codes

        codes = get_all_codes(ctx.code_repo)
        for code in codes:
            if code.category_id:
                cat_id = code.category_id.value
                code_counts[cat_id] = code_counts.get(cat_id, 0) + 1

    return OperationResult.ok(
        data=[
            _serialize_category(c, code_count=code_counts.get(c.id.value, 0))
            for c in categories
        ]
    ).to_dict()


# Handler registry for category/code management tools
CATEGORY_HANDLERS = {
    "rename_code": handle_rename_code,
    "update_code_memo": handle_update_code_memo,
    "create_category": handle_create_category,
    "move_code_to_category": handle_move_code_to_category,
    "merge_codes": handle_merge_codes,
    "delete_code": handle_delete_code,
    "list_categories": handle_list_categories,
}
