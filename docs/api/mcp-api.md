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
| `add_source` | Add a text source to the project | QC-027 AC #11 |
| `auto_code_pattern` | Auto-code by text pattern | QC-032 |
| `auto_code_speaker` | Auto-code by speaker | QC-032 |

---

## Architecture

See [ARCHITECTURE.md](../ARCHITECTURE.md) for how MCP integrates with the application.

See [Decision 005](../backlog/decisions/decision-005%20mcp-transport-http-over-stdio.md) for the HTTP vs stdio transport decision.
