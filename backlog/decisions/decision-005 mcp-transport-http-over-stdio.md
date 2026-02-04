---
id: decision-005
title: MCP Transport - HTTP over Stdio
status: Accepted
date: '2026-02-04'
deciders: []
labels:
  - mcp
  - architecture
  - ai-agents
---

## Context

QualCoder v2 exposes MCP (Model Context Protocol) tools for AI agent integration. The MCP specification supports multiple transport mechanisms:

1. **stdio** - Standard input/output (process-based)
2. **HTTP** - REST/JSON-RPC over HTTP
3. **SSE** - Server-Sent Events (deprecated)
4. **WebSocket** - Bidirectional WebSocket

We needed to choose a transport that allows AI agents (like Claude Code) to interact with a **running QualCoder instance** while sharing the same `AppContext`, `EventBus`, and enabling real-time UI updates.

## Decision

**Accepted: HTTP transport embedded in the QualCoder application.**

The MCP server runs as a background thread inside the QualCoder app on `localhost:8765`, sharing the same `AppContext` and `EventBus` with the Qt UI.

### Architecture

```
┌─────────────────────────────────────────────────┐
│              QualCoder App (Main Process)       │
│                                                 │
│  ┌──────────────┐    ┌──────────────────────┐  │
│  │  AppContext  │◄───│  MCPServerManager    │  │
│  │  (shared)    │    │  (HTTP on :8765)     │  │
│  └──────────────┘    │  [background thread] │  │
│         │            └──────────────────────┘  │
│         ▼                      ▲               │
│  ┌──────────────┐              │               │
│  │  EventBus    │──────────────┘               │
│  │ SignalBridge │  (publishes domain events)   │
│  └──────────────┘                              │
│         │                                      │
│         ▼                                      │
│  ┌──────────────┐                              │
│  │   Qt UI      │ (receives signals, updates)  │
│  └──────────────┘                              │
└─────────────────────────────────────────────────┘
              ▲
              │ HTTP (localhost:8765)
              │
       ┌──────┴──────┐
       │ Claude Code │
       │ (MCP Client)│
       └─────────────┘
```

## Options Considered

### Option 1: Stdio Transport (Rejected)

```
┌─────────────┐     stdio     ┌─────────────┐
│ Claude Code │◄─────────────►│ MCP Server  │
└─────────────┘               │ (separate)  │
                              └─────────────┘
                                    │
                              ┌─────┴─────┐
                              │ Shared DB │
                              └───────────┘
                                    │
                              ┌─────────────┐
                              │ QualCoder   │
                              │ (separate)  │
                              └─────────────┘
```

| Pros | Cons |
|------|------|
| Standard MCP transport | Separate process - no shared EventBus |
| Simple to implement | No real-time UI updates |
| Works with all MCP clients | Requires IPC for communication |
| | Database conflicts possible |

**Rejected because:** Cannot interact with running app. AI actions wouldn't trigger live UI updates.

### Option 2: HTTP Transport - Embedded (Accepted)

| Pros | Cons |
|------|------|
| Shares AppContext with UI | Requires HTTP server dependency (aiohttp) |
| Real-time UI updates via SignalBridge | Slightly more complex |
| EventBus integration | Port management needed |
| Thread-safe via QMetaObject | |

**Accepted because:** Enables the core use case - AI agents can code documents and researchers see changes in real-time.

### Option 3: WebSocket Transport (Future)

| Pros | Cons |
|------|------|
| Bidirectional communication | Not standard MCP transport |
| Push notifications to client | More implementation effort |
| Lower latency | |

**Deferred:** HTTP is sufficient for current needs. WebSocket could be added for bidirectional notifications.

## Consequences

### Positive

- **Real-time collaboration**: When AI applies codes, the UI updates immediately
- **Shared state**: AI reads the exact same project state the user sees
- **Thread-safe signals**: `SignalBridge` properly marshals events to Qt main thread
- **Simple configuration**: Single `.mcp.json` file for clients

### Negative

- **Port dependency**: Server uses fixed port (8765), may conflict
- **HTTP overhead**: Slightly higher latency than stdio
- **Requires running app**: MCP only available when QualCoder is open

### Mitigations

- Port can be configured via environment variable
- HTTP latency is negligible for tool calls (< 10ms local)
- Future: Add stdio mode for headless/batch operations

## Implementation

### Server Location

`src/shared/infra/mcp_server.py`

### Wiring in main.py

```python
from src.shared.infra.mcp_server import MCPServerManager

class QualCoderApp:
    def __init__(self):
        # ... existing init ...
        self._mcp_server = MCPServerManager(ctx=self._ctx)
        self._mcp_server.start()

    def run(self):
        # ... app.exec() ...
        self._mcp_server.stop()
```

### Client Configuration

`.mcp.json` in project root:

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

### Dependencies

```toml
[project.dependencies]
aiohttp = ">=3.9"  # MIT - HTTP server for MCP
```

## Thread Safety

The `SignalBridge` ensures thread-safe signal emission:

1. MCP tool executes in aiohttp thread
2. Publishes domain event to EventBus
3. SignalBridge catches event in background thread
4. Uses `QMetaObject.invokeMethod` with `QueuedConnection`
5. Signal emitted on Qt main thread
6. UI slot updates safely

See: `src/shared/infra/signal_bridge/base.py:314-336`

## References

- [MCP Transport Specification](https://modelcontextprotocol.io/docs/concepts/transports)
- [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
- [Qt Thread Safety](https://doc.qt.io/qt-6/threads-qobject.html)
