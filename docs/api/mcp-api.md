# MCP API Reference

QualCoder MCP server at `http://localhost:8765`.

## Tools

### Core

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `list_codes` | Get all codes | - |
| `get_code` | Get code details | `code_id` |
| `create_code` | Create a new code | `name`, `color` |
| `list_segments_for_source` | Get segments for source | `source_id` |
| `delete_segment` | Delete a coded segment | `segment_id` |
| `batch_apply_codes` | Apply multiple codes | `operations[]` |

### Project Lifecycle (QC-026.05, QC-026.07)

| Tool | Description | Required Params | Optional Params |
|------|-------------|-----------------|-----------------|
| `get_project_context` | Get current project name, path, sources, cases, and screen | - | - |
| `open_project` | Request project open (returns UI guidance) | `path` | - |
| `close_project` | Request project close (returns UI guidance) | - | - |

> **Note:** `open_project` and `close_project` return guidance text directing the user to open/close from the QualCoder UI (File menu). This ensures proper database initialization and cleanup.

### Source Management (QC-027.08–QC-027.15)

| Tool | Description | Required Params | Optional Params |
|------|-------------|-----------------|-----------------|
| `list_sources` | List all sources in the project | - | `source_type` (filter: `text`, `audio`, `video`, `image`, `pdf`) |
| `read_source_content` | Read text content of a source | `source_id` | `start_pos` (default 0), `end_pos`, `max_length` (default 50000) |
| `navigate_to_segment` | Open source at a position and scroll | `source_id`, `start_pos`, `end_pos` | `highlight` (default true) |
| `suggest_source_metadata` | Suggest language, topics, org hints | `source_id` | `language`, `topics[]`, `organization_suggestion` |
| `add_text_source` | Add a new text source | `name`, `content` | `memo`, `origin` |
| `remove_source` | Delete source and its segments | `source_id` | `confirm` (default false — preview only) |
| `import_file_source` | Import file by absolute path | `file_path` | `name`, `memo`, `origin`, `dry_run` (default false) |

**Pagination:** `read_source_content` returns `has_more: true` when the content exceeds `max_length`. Pass the returned `end_pos` as the next `start_pos` to continue reading.

**Safe deletion:** `remove_source` defaults to preview mode (`confirm=false`), returning source name, type, and coded segment count. Set `confirm=true` to perform the actual deletion.

### Folder Management (QC-027.13)

| Tool | Description | Required Params | Optional Params |
|------|-------------|-----------------|-----------------|
| `list_folders` | List all folders with hierarchy | - | - |
| `create_folder` | Create a new folder | `name` | `parent_id` (omit for root) |
| `rename_folder` | Rename an existing folder | `folder_id`, `new_name` | - |
| `delete_folder` | Delete an empty folder | `folder_id` | - |
| `move_source_to_folder` | Move a source into a folder | `source_id` | `folder_id` (null or 0 for root) |

**Naming rules:** Folder names must be unique within their parent, 1–255 characters, no slashes.

**Nesting:** Pass `parent_id` to `create_folder` to nest folders. Omit for root-level.

### AI Code Suggestions (QC-028.07, QC-028.08)

All suggestions require researcher approval.

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `analyze_content_for_codes` | Analyze uncoded content | `source_id` |
| `suggest_new_code` | Suggest a new code | `name`, `rationale` |
| `list_pending_suggestions` | List pending suggestions | - |
| `approve_suggestion` | Approve code suggestion | `suggestion_id` |
| `detect_duplicate_codes` | Find similar codes (token-level + memo-aware) | - |
| `suggest_merge_codes` | Suggest merging codes | `source_code_id`, `target_code_id`, `rationale` |
| `approve_merge` | Approve merge | `merge_suggestion_id` |

### AI Text Coding (QC-029.07, QC-029.08)

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `suggest_code_application` | Suggest applying code to text | `source_id`, `code_id`, `start_pos`, `end_pos` |
| `list_pending_coding_suggestions` | List pending | `source_id` (optional) |
| `approve_coding_suggestion` | Approve suggestion | `suggestion_id` |
| `reject_coding_suggestion` | Reject with feedback | `suggestion_id` |
| `analyze_uncoded_text` | Find uncoded ranges | `source_id` |
| `suggest_codes_for_range` | Suggest codes for text | `source_id`, `start_pos`, `end_pos` |
| `auto_suggest_codes` | Auto-suggest for source | `source_id` |
| `get_suggestion_batch_status` | Check batch status | `batch_id` |
| `respond_to_code_suggestion` | Accept/reject batch suggestions | `suggestion_batch_id`, `response` |
| `approve_batch_coding` | Approve entire batch | `batch_id` |

### Batch Operations

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `find_similar_content` | Find similar text | `search_text` |
| `suggest_batch_coding` | Suggest code for multiple segments | `code_id`, `segments[]`, `rationale` |

---

## Usage

```bash
# List tools
curl http://localhost:8765/tools

# Call a tool
curl -X POST http://localhost:8765/tools/list_codes \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'
```

## Response Format

```json
{"success": true, "data": {...}}
{"success": false, "error": "...", "error_code": "..."}
```

## Error Codes

| Code | Meaning |
|------|---------|
| `NO_PROJECT` | No project open |
| `CODE_NOT_FOUND` | Invalid code_id |
| `SOURCE_NOT_FOUND` | Invalid source_id |
| `FOLDER_NOT_FOUND` | Invalid folder_id |
| `FOLDER_NOT_CREATED` | Folder creation failed (duplicate name or invalid parent) |
| `FOLDER_NOT_EMPTY` | Cannot delete folder that contains sources |
| `FOLDER_RENAME_FAILED` | Rename failed (duplicate name in parent) |
| `SOURCE_IMPORT_FAILED` | File import failed (unsupported type or file not found) |
| `SOURCE_DUPLICATE_NAME` | Source name already exists in project |
| `TOOL_NOT_FOUND` | Unknown tool |
