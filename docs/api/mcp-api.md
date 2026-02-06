# MCP API Reference

Technical reference for QualCoder's MCP (Model Context Protocol) server.

> **Tip:** Call `tools/list` at runtime to get full JSON schemas with descriptions for every tool.

## Server Details

| Property | Value |
|----------|-------|
| URL | `http://localhost:8765` |
| Transport | HTTP (JSON-RPC 2.0) |
| Binding | localhost only |
| Started by | QualCoder app (embedded) |

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server info |
| `/tools` | GET | List available tools |
| `/tools/{name}` | POST | Call a specific tool |
| `/mcp` | POST | MCP JSON-RPC endpoint |

---

## Available Tools

### Project Tools

| Tool | Required Params | Optional Params | Description |
|------|----------------|-----------------|-------------|
| `get_project_context` | — | — | Get current project state, sources, and cases |
| `open_project` | `path` (str) | — | Open a .qda project file |
| `close_project` | — | — | Close current project (idempotent) |

### Source Tools

| Tool | Required Params | Optional Params | Description |
|------|----------------|-----------------|-------------|
| `list_sources` | — | `source_type` | List all sources, optionally filtered by type |
| `read_source_content` | `source_id` | `start_pos`, `end_pos`, `max_length` | Read document text with pagination |
| `add_text_source` | `name`, `content` | `memo`, `origin` | Add text source with inline content |
| `import_file_source` | `file_path` | `name`, `memo`, `origin`, `dry_run` | Import file by path (auto-detects type) |
| `remove_source` | `source_id` | `confirm` (default: false) | Preview or delete a source (T3) |
| `suggest_source_metadata` | `source_id` | `language`, `topics`, `organization_suggestion` | Suggest metadata (pending human approval) |
| `navigate_to_segment` | `source_id`, `start_pos`, `end_pos` | `highlight` | Navigate UI to a position |

### Folder Tools

| Tool | Required Params | Optional Params | Description |
|------|----------------|-----------------|-------------|
| `list_folders` | — | — | List all source folders |
| `create_folder` | `name` | `parent_id` | Create a new folder |
| `rename_folder` | `folder_id`, `new_name` | — | Rename a folder |
| `delete_folder` | `folder_id` | — | Delete an empty folder |
| `move_source_to_folder` | `source_id` | `folder_id` (0/null = root) | Move source to a folder |

### Coding Tools

| Tool | Required Params | Optional Params | Description |
|------|----------------|-----------------|-------------|
| `list_codes` | — | — | Get all codes in the codebook |
| `get_code` | `code_id` | — | Get details for a specific code |
| `batch_apply_codes` | `operations` (array) | — | Apply multiple codes in one call |
| `list_segments_for_source` | `source_id` | — | Get coded segments for a source |

---

## Error Codes

All errors return `{"success": false, "error": "...", "error_code": "..."}`.

| Error Code | Meaning |
|------------|---------|
| `NO_PROJECT` | No project is open |
| `CODE_NOT_FOUND` | Code ID doesn't exist |
| `SOURCE_NOT_FOUND` | Source ID doesn't exist |
| `INVALID_POSITION` | Start/end position out of range |
| `TOOL_NOT_FOUND` | Unknown tool name |
| `SOURCE_NOT_ADDED/DUPLICATE_NAME` | Source name already exists |
| `SOURCE_NOT_IMPORTED/FILE_NOT_FOUND` | File not found at path |
| `SOURCE_NOT_IMPORTED/UNSUPPORTED_TYPE` | Unsupported file extension |
| `SOURCE_NOT_IMPORTED/DUPLICATE_NAME` | Source name already exists |
| `SOURCE_NOT_IMPORTED/RELATIVE_PATH` | Path must be absolute |
| `FOLDER_NOT_CREATED/DUPLICATE_NAME` | Folder name already exists |
| `FOLDER_NOT_DELETED/HAS_SOURCES` | Folder contains sources |

---

## HTTP Examples

### Direct Tool Call

```bash
curl -X POST http://localhost:8765/tools/list_codes \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'
```

### JSON-RPC

```bash
# List all tools (returns full schemas)
curl -X POST http://localhost:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# Call a tool
curl -X POST http://localhost:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_codes", "arguments": {}}}'
```

---

## Agent Integration

Check for `.mcp.json` in the project root to discover the server URL. Call `GET /` to verify the server is running before making tool calls.

---

## Planned Tools

| Tool | Description | Tracked In |
|------|-------------|------------|
| `create_code` | Create a new code with name and color | QC-028 AC #10 |
| `update_code` | Update code name, color, or memo | QC-028 |
| `delete_code` | Delete a code | QC-028 |
| `merge_codes` | Merge two codes into one | QC-028 |
| `remove_coding` | Remove coding from a segment | QC-029 AC #10 |
| `auto_code_pattern` | Auto-code by text pattern | QC-032 |
| `auto_code_speaker` | Auto-code by speaker | QC-032 |

---

## Architecture

See [ARCHITECTURE.md](../ARCHITECTURE.md) for how MCP integrates with the application.

See [Decision 005](../backlog/decisions/decision-005%20mcp-transport-http-over-stdio.md) for the HTTP vs stdio transport decision.
