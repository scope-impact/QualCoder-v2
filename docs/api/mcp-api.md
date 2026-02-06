# MCP API Reference

Technical reference for QualCoder's MCP (Model Context Protocol) server.

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

#### open_project

Open an existing QualCoder project file (.qda). Closes any currently open project first.

```json
{
  "name": "open_project",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Absolute path to the .qda project file."
      }
    },
    "required": ["path"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "project_name": "My Research",
  "project_path": "/path/to/project.qda",
  "source_count": 5
}
```

#### close_project

Close the currently open project. Idempotent — safe to call when no project is open.

```json
{
  "name": "close_project",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Response (project was open):**
```json
{
  "success": true,
  "closed": true,
  "project_name": "My Research"
}
```

**Response (no project open):**
```json
{
  "success": true,
  "closed": false,
  "message": "No project was open"
}
```

#### add_text_source

Add a new text source to the current project with agent-provided content (no file import needed).

```json
{
  "name": "add_text_source",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Name for the new source (must be unique within project)."
      },
      "content": {
        "type": "string",
        "description": "The full text content of the source."
      },
      "memo": {
        "type": "string",
        "description": "Optional memo/notes about the source."
      },
      "origin": {
        "type": "string",
        "description": "Optional origin description (e.g., 'interview transcript', 'field notes')."
      }
    },
    "required": ["name", "content"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "source_id": 7,
  "name": "interview_01.txt",
  "type": "text",
  "status": "imported",
  "file_size": 1234
}
```

| Error | Cause |
|-------|-------|
| `SOURCE_NOT_ADDED/DUPLICATE_NAME` | A source with that name already exists |
| `Missing required parameter: name` | Empty or missing name |
| `Missing required parameter: content` | Empty or missing content |

#### remove_source

Remove a source from the project. Supports preview mode (default) and confirmed deletion.

**Trust Level:** T3 (Suggest) — Deletion is destructive and removes coded segments.

```json
{
  "name": "remove_source",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {
        "type": "integer",
        "description": "ID of the source to remove."
      },
      "confirm": {
        "type": "boolean",
        "description": "Set to true to actually delete. Default false returns a preview.",
        "default": false
      }
    },
    "required": ["source_id"]
  }
}
```

**Response (preview, confirm=false):**
```json
{
  "preview": true,
  "source_id": 7,
  "source_name": "interview_01.txt",
  "source_type": "text",
  "coded_segments_count": 3,
  "requires_approval": true,
  "message": "This will delete source 'interview_01.txt' and 3 coded segment(s)"
}
```

**Response (confirmed deletion, confirm=true):**
```json
{
  "success": true,
  "removed": true,
  "source_id": 7,
  "source_name": "interview_01.txt",
  "segments_removed": 3
}
```

### Folder Tools

#### list_folders

List all source folders in the current project.

```json
{
  "name": "list_folders",
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
  "total_count": 2,
  "folders": [
    {"id": 1, "name": "Interviews", "parent_id": null, "source_count": 3},
    {"id": 2, "name": "Field Notes", "parent_id": null, "source_count": 1}
  ]
}
```

#### create_folder

Create a new folder for organizing sources.

```json
{
  "name": "create_folder",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Folder name (must be unique within parent)."
      },
      "parent_id": {
        "type": "integer",
        "description": "Parent folder ID for nesting. Omit for root-level folder."
      }
    },
    "required": ["name"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "folder_id": 3,
  "name": "Interviews",
  "parent_id": null
}
```

#### rename_folder

Rename an existing folder.

```json
{
  "name": "rename_folder",
  "inputSchema": {
    "type": "object",
    "properties": {
      "folder_id": {
        "type": "integer",
        "description": "ID of the folder to rename."
      },
      "new_name": {
        "type": "string",
        "description": "New folder name."
      }
    },
    "required": ["folder_id", "new_name"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "folder_id": 3,
  "name": "Transcripts"
}
```

#### delete_folder

Delete an empty folder. Fails if the folder contains sources.

```json
{
  "name": "delete_folder",
  "inputSchema": {
    "type": "object",
    "properties": {
      "folder_id": {
        "type": "integer",
        "description": "ID of the folder to delete."
      }
    },
    "required": ["folder_id"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "folder_id": 3,
  "name": "Interviews"
}
```

#### move_source_to_folder

Move a source into a folder. Use folder_id=0 or null to move to root.

```json
{
  "name": "move_source_to_folder",
  "inputSchema": {
    "type": "object",
    "properties": {
      "source_id": {
        "type": "integer",
        "description": "ID of the source to move."
      },
      "folder_id": {
        "type": "integer",
        "description": "Target folder ID. Use null or 0 for root."
      }
    },
    "required": ["source_id"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "source_id": 7,
  "old_folder_id": null,
  "new_folder_id": 3
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

## HTTP Examples

### Direct Tool Call

```bash
curl -X POST http://localhost:8765/tools/list_codes \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'
```

### JSON-RPC: List Tools

```bash
curl -X POST http://localhost:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### JSON-RPC: Call Tool

```bash
curl -X POST http://localhost:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "batch_apply_codes",
      "arguments": {
        "operations": [{
          "code_id": 1,
          "source_id": 1,
          "start_position": 0,
          "end_position": 100
        }]
      }
    }
  }'
```

---

## Error Responses

```json
{
  "success": false,
  "error": "No project open",
  "error_code": "NO_PROJECT"
}
```

| Error Code | Meaning |
|------------|---------|
| `NO_PROJECT` | No project is open in QualCoder |
| `CODE_NOT_FOUND` | Code ID doesn't exist |
| `SOURCE_NOT_FOUND` | Source ID doesn't exist |
| `INVALID_POSITION` | Start/end position out of range |
| `TOOL_NOT_FOUND` | Unknown tool name |
| `SOURCE_NOT_ADDED/DUPLICATE_NAME` | Source with that name already exists |
| `FOLDER_NOT_CREATED/DUPLICATE_NAME` | Folder with that name already exists |
| `FOLDER_NOT_DELETED/HAS_SOURCES` | Cannot delete folder that contains sources |

---

## Agent Integration

### Discovery

Check for `.mcp.json` in project root:

```python
import json
from pathlib import Path

def discover_mcp(project_root: str) -> str | None:
    config = Path(project_root) / ".mcp.json"
    if config.exists():
        data = json.loads(config.read_text())
        return data.get("mcpServers", {}).get("qualcoder", {}).get("url")
    return None
```

### Health Check

```python
import httpx

def is_qualcoder_running(url: str = "http://localhost:8765") -> bool:
    try:
        return httpx.get(f"{url}/", timeout=2).status_code == 200
    except httpx.RequestError:
        return False
```

### Recommended Workflow

```python
async def agent_workflow():
    mcp_url = discover_mcp(".") or "http://localhost:8765/mcp"

    if not is_qualcoder_running():
        return "Start QualCoder first"

    # Check project is open
    ctx = await call_tool(mcp_url, "get_project_context", {})
    if not ctx["data"]["project_open"]:
        return "Open a project in QualCoder"

    # Work with the project
    codes = await call_tool(mcp_url, "list_codes", {})
    # ... apply codes, analyze, etc.
```

---

## Planned Tools

The following tools are planned but not yet implemented. Progress is tracked via Agent AC on feature tasks:

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
