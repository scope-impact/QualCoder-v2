# MCP Setup Guide

Connect AI assistants like Claude Code to QualCoder for AI-assisted qualitative analysis.

## What is MCP?

MCP (Model Context Protocol) allows AI assistants to interact with QualCoder in real-time. When connected, AI can:

- Read your documents and codes
- Apply codes to text segments
- Navigate to specific locations
- Suggest codes and patterns

All AI actions appear immediately in the UI, so you always see what's happening.

## Quick Setup

### Step 1: Start QualCoder

```bash
uv run python -m src.main
```

The MCP server starts automatically on `localhost:8765`.

### Step 2: Open a Project

Open or create a project in QualCoder. AI tools only work when a project is open.

### Step 3: Connect Your AI Assistant

**Claude Code** auto-connects via the `.mcp.json` file in the project.

To verify: type `/mcp` in Claude Code - you should see `qualcoder` listed.

## Manual Configuration

If your AI client doesn't auto-detect the configuration, add this to your MCP settings:

```json
{
  "mcpServers": {
    "qualcoder": {
      "type": "http",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "qualcoder": {
      "type": "http",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

## Available AI Tools

Once connected, AI assistants can use these tools:

| Tool | What it does |
|------|--------------|
| `get_project_context` | See what project is open, list sources and cases |
| `list_sources` | Get all documents in the project |
| `read_source_content` | Read document text |
| `list_codes` | See all codes in your codebook |
| `batch_apply_codes` | Apply codes to text (you'll see it immediately) |
| `navigate_to_segment` | Jump to a specific location in the UI |

## Real-Time Updates

When AI applies a code:

1. You see the highlight appear immediately
2. The codes panel updates
3. You can undo or modify the AI's work

This "human-in-the-loop" design means you stay in control.

## Troubleshooting

### "Connection refused"

- Make sure QualCoder is running
- Check port 8765 is not blocked: `lsof -i :8765`

### "No project open"

- Open a project in QualCoder before using AI tools

### AI tools not appearing

- Restart Claude Code after starting QualCoder
- Check `/mcp` shows the qualcoder server

## Security

- The MCP server only accepts local connections (`localhost`)
- No data is sent externally through MCP
- AI actions are visible in the UI for your review

## See Also

- [AI Features](./ai-features.md) - Built-in AI assistance
- [MCP API Reference](../api/mcp-api.md) - Technical API details
