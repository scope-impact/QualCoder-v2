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

## Tool Schemas

### Project Tools

#### get_project_context

Get current project state.

```json
{
  "name": "get_project_context",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project_open": true,
    "project_name": "My Research",
    "project_path": "/path/to/project.qda",
    "source_count": 5,
    "sources": [{"id": 1, "name": "interview1.txt", "type": "text"}],
    "case_count": 3,
    "cases": [{"id": 1, "name": "Participant A"}]
  }
}
```

#### list_sources

List all sources with metadata.

```json
{
  "name": "list_sources",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_type": {
        "type": "string",
        "description": "Filter: 'text', 'audio', 'video', 'image', 'pdf'"
      }
    },
    "required": []
  }
}
```

#### read_source_content

Read document text with pagination.

```json
{
  "name": "read_source_content",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {"type": "integer", "description": "Source ID"},
      "start_pos": {"type": "integer", "default": 0},
      "end_pos": {"type": "integer"},
      "max_length": {"type": "integer", "default": 50000}
    },
    "required": ["source_id"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "source_id": 1,
    "source_name": "interview1.txt",
    "content": "The interview transcript...",
    "start_pos": 0,
    "end_pos": 5000,
    "total_length": 15000,
    "has_more": true
  }
}
```

#### navigate_to_segment

Navigate UI to a specific position.

```json
{
  "name": "navigate_to_segment",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {"type": "integer"},
      "start_pos": {"type": "integer"},
      "end_pos": {"type": "integer"},
      "highlight": {"type": "boolean", "default": true}
    },
    "required": ["source_id", "start_pos", "end_pos"]
  }
}
```

#### suggest_source_metadata

Suggest metadata for a source (pending human approval).

```json
{
  "name": "suggest_source_metadata",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {"type": "integer"},
      "language": {"type": "string", "description": "e.g., 'en', 'es'"},
      "topics": {"type": "array", "items": {"type": "string"}},
      "organization_suggestion": {"type": "string"}
    },
    "required": ["source_id"]
  }
}
```

---

### Coding Tools

#### list_codes

Get all codes in the codebook.

```json
{
  "name": "list_codes",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "Anxiety", "color": "#FF6B6B", "segment_count": 12},
    {"id": 2, "name": "Coping", "color": "#4ECDC4", "segment_count": 8}
  ]
}
```

#### get_code

Get details for a specific code.

```json
{
  "name": "get_code",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code_id": {"type": "integer"}
    },
    "required": ["code_id"]
  }
}
```

#### batch_apply_codes

Apply multiple codes efficiently (AI-optimized).

```json
{
  "name": "batch_apply_codes",
  "inputSchema": {
    "type": "object",
    "properties": {
      "operations": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "code_id": {"type": "integer"},
            "source_id": {"type": "integer"},
            "start_position": {"type": "integer"},
            "end_position": {"type": "integer"},
            "memo": {"type": "string"},
            "importance": {"type": "integer", "minimum": 0, "maximum": 3}
          },
          "required": ["code_id", "source_id", "start_position", "end_position"]
        }
      }
    },
    "required": ["operations"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 3,
    "succeeded": 3,
    "failed": 0,
    "all_succeeded": true,
    "results": [
      {"index": 0, "success": true, "segment_id": 42},
      {"index": 1, "success": true, "segment_id": 43},
      {"index": 2, "success": true, "segment_id": 44}
    ]
  }
}
```

#### list_segments_for_source

Get coded segments for a source.

```json
{
  "name": "list_segments_for_source",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {"type": "integer"}
    },
    "required": ["source_id"]
  }
}
```

---

### Version Control Tools

#### list_snapshots

List version control snapshots (commit history).

```json
{
  "name": "list_snapshots",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "description": "Max snapshots to return. Default 20.",
        "default": 20
      }
    },
    "required": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 3,
    "snapshots": [
      {
        "sha": "abc123456789",
        "message": "coding: 3 events",
        "author": "QualCoder",
        "date": "2024-01-15T10:30:00Z"
      },
      {
        "sha": "def987654321",
        "message": "sources: imported 2 files",
        "author": "QualCoder",
        "date": "2024-01-15T09:15:00Z"
      }
    ]
  }
}
```

#### view_diff

View differences between two snapshots.

```json
{
  "name": "view_diff",
  "inputSchema": {
    "type": "object",
    "properties": {
      "from_ref": {
        "type": "string",
        "description": "Starting commit reference (SHA or HEAD~N)"
      },
      "to_ref": {
        "type": "string",
        "description": "Ending commit reference (SHA or HEAD~N)"
      }
    },
    "required": ["from_ref", "to_ref"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "from_ref": "abc123",
    "to_ref": "def456",
    "diff": "diff --git a/code.csv b/code.csv\n+new line\n-old line"
  }
}
```

#### restore_snapshot

**⚠️ DESTRUCTIVE**: Restore database to a previous snapshot.

```json
{
  "name": "restore_snapshot",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ref": {
        "type": "string",
        "description": "Commit reference to restore (SHA or HEAD~N)"
      }
    },
    "required": ["ref"]
  },
  "annotations": {"destructive": true}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Restored to snapshot abc123",
    "restored_ref": "abc123"
  }
}
```

#### initialize_version_control

Initialize version control for the project.

```json
{
  "name": "initialize_version_control",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Version control initialized",
    "initial_sha": "abc123456789"
  }
}
```

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
