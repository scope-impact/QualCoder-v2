---
id: QC-050
title: Agent Code Management MCP Tools
status: To Do
assignee: []
created_date: '2026-03-13'
updated_date: '2026-03-13'
labels: [interface, coding, agent-tools, P1]
dependencies: [QC-028.03, QC-028.04, QC-028.02]
parent_task_id: ''
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
As an AI Agent, I want MCP tools for code management operations (rename, memo, category, merge, delete) so that I can perform a complete thematic analysis workflow without falling back to direct command handler calls.

**Context:** The thematic analysis replication E2E test (`test_thematic_analysis_replication_e2e.py`) demonstrates that an AI agent performing Braun & Clarke's Reflexive Thematic Analysis needs these operations:

- **Phase 2** (Initial Coding): `create_code` ✅, `batch_apply_codes` ✅
- **Phase 3** (Searching for Themes): `create_category` ❌, `move_code_to_category` ❌
- **Phase 4** (Reviewing Themes): `merge_codes` ❌ (direct merge, not suggest/approve)
- **Phase 5** (Defining Themes): `rename_code` ❌, `update_code_memo` ❌
- **Phase 6** (Verification): `list_codes` ✅, `get_code` ✅, `list_segments_for_source` ✅

The command handlers already exist and are tested. Only the MCP `interface/handlers/` wrappers are missing.

**Agent-First:** These tools complete the coding MCP surface so AI agents can perform end-to-end qualitative research workflows.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `rename_code` MCP tool: accepts `code_id` and `new_name`, delegates to `rename_code` command handler, returns updated code with old/new name
- [ ] #2 `update_code_memo` MCP tool: accepts `code_id` and `memo`, delegates to `update_code_memo` handler, returns success with old/new memo
- [ ] #3 `create_category` MCP tool: accepts `name`, optional `parent_id` and `memo`, delegates to `create_category` handler, returns category with ID
- [ ] #4 `move_code_to_category` MCP tool: accepts `code_id` and `category_id` (nullable for uncategorize), delegates to handler, returns success
- [ ] #5 `merge_codes` MCP tool: accepts `source_code_id` and `target_code_id`, delegates to `merge_codes` handler, returns merge result with reassigned segment count
- [ ] #6 `delete_code` MCP tool: accepts `code_id` and optional `delete_segments` flag, delegates to `delete_code` handler, returns success/failure
- [ ] #7 `list_categories` MCP tool: returns all categories with hierarchy (parent_id), code count per category
- [ ] #8 All tools follow the existing pattern: handler in `interface/handlers/`, schema in `interface/tool_definitions/`, registered in `ALL_HANDLERS` and `ALL_TOOLS`
- [ ] #9 All tools delegate to command handlers (never direct repo access) to ensure events are published and UI refreshes via SignalBridge
- [ ] #10 All tools return `OperationResult.to_dict()` for consistent JSON responses
- [ ] #11 E2E test `test_thematic_analysis_replication_e2e.py` updated to use MCP tools for ALL operations (no direct command handler calls)
- [ ] #12 E2E test passes with `QT_QPA_PLATFORM=offscreen make test-all`
<!-- AC:END -->

## Subtasks

| ID | Subtask | Status |
|----|---------|--------|
| QC-050.01 | Add `rename_code` MCP handler + schema | To Do |
| QC-050.02 | Add `update_code_memo` MCP handler + schema | To Do |
| QC-050.03 | Add `create_category` MCP handler + schema | To Do |
| QC-050.04 | Add `move_code_to_category` MCP handler + schema | To Do |
| QC-050.05 | Add `merge_codes` MCP handler + schema | To Do |
| QC-050.06 | Add `delete_code` MCP handler + schema | To Do |
| QC-050.07 | Add `list_categories` MCP handler + schema | To Do |
| QC-050.08 | Update thematic analysis E2E test to use all MCP tools | To Do |

## Implementation

### New handlers (add to existing files or create `category_handlers.py`)

```
src/contexts/coding/interface/handlers/core_handlers.py     # rename_code, update_code_memo, delete_code
src/contexts/coding/interface/handlers/category_handlers.py  # NEW: create_category, move_code_to_category, list_categories, merge_codes
src/contexts/coding/interface/tool_definitions/core_tools.py # Add schemas
src/contexts/coding/interface/tool_definitions/category_tools.py  # NEW: category schemas
```

### Handler pattern (follow existing convention)

```python
def handle_rename_code(ctx: HandlerContext, arguments: dict) -> dict:
    name = arguments.get("new_name")
    code_id = arguments.get("code_id")
    if not name or not code_id:
        return missing_param_error(...)

    command = RenameCodeCommand(code_id=str(code_id), new_name=str(name))
    result = rename_code(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success:
        return OperationResult.ok(data={...}).to_dict()
    return result.to_dict()
```

## Methodology Context

These tools map to qualitative research operations from Braun & Clarke's Reflexive Thematic Analysis:

| MCP Tool | TA Phase | Saldana Method |
|----------|----------|---------------|
| `rename_code` | Phase 5: Defining themes | Refining code labels |
| `update_code_memo` | Phase 5: Defining themes | Codebook definitions (Lincoln & Guba audit trail) |
| `create_category` | Phase 3: Searching for themes | Pattern Coding (Second Cycle) |
| `move_code_to_category` | Phase 3: Searching for themes | Focused Coding |
| `merge_codes` | Phase 4: Reviewing themes | Consolidating overlapping codes |
| `delete_code` | Phase 4: Reviewing themes | Removing irrelevant codes |
| `list_categories` | Phase 3-6: All review phases | Viewing thematic structure |
