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

### AI Code Suggestions (QC-028.07, QC-028.08)

All suggestions require researcher approval.

| Tool | Description | Required Params |
|------|-------------|-----------------|
| `analyze_content_for_codes` | Analyze uncoded content | `source_id` |
| `suggest_new_code` | Suggest a new code | `name`, `rationale` |
| `list_pending_suggestions` | List pending suggestions | - |
| `approve_suggestion` | Approve code suggestion | `suggestion_id` |
| `detect_duplicate_codes` | Find similar codes | - |
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
| `TOOL_NOT_FOUND` | Unknown tool |
