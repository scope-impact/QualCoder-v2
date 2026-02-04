"""
QualCoder v2 Embedded MCP Server

Runs inside the QualCoder app, sharing AppContext and EventBus
for real-time AI agent interaction.

Usage in main.py:
    from src.shared.infra.mcp_server import MCPServerManager

    self._mcp_server = MCPServerManager(ctx=self._ctx)
    self._mcp_server.start()  # Starts on localhost:8765
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.shared.infra.app_context import AppContext


class MCPServerManager:
    """Manages embedded MCP HTTP server lifecycle."""

    DEFAULT_PORT = 8765

    def __init__(self, ctx: AppContext, port: int = DEFAULT_PORT):
        self._ctx = ctx
        self._port = port
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False

    @property
    def url(self) -> str:
        return f"http://localhost:{self._port}"

    def start(self):
        """Start MCP server in background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop MCP server."""
        if not self._running:
            return

        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run_server(self):
        """Run async server in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:
            print(f"[MCP] Server error: {e}")
        finally:
            self._loop.close()

    async def _serve(self):
        """Main server coroutine."""
        try:
            from aiohttp import web
        except ImportError:
            print("[MCP] Install aiohttp: uv add aiohttp")
            return

        app = web.Application()
        app.router.add_get("/", self._handle_info)
        app.router.add_get("/tools", self._handle_list_tools)
        app.router.add_post("/tools/{tool_name}", self._handle_call_tool)
        app.router.add_post("/mcp", self._handle_jsonrpc)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self._port)
        await site.start()

        print(f"[MCP] Server running on http://localhost:{self._port}")

        while self._running:
            await asyncio.sleep(0.1)

        await runner.cleanup()

    # ── HTTP Handlers ──────────────────────────────────────────

    async def _handle_info(self, _request: Any) -> Any:
        from aiohttp import web

        return web.json_response(
            {
                "name": "qualcoder-v2",
                "version": "0.2.0",
                "mcp_endpoint": "POST /mcp",
                "tools_endpoint": "GET /tools",
            }
        )

    async def _handle_list_tools(self, _request: Any) -> Any:
        from aiohttp import web

        return web.json_response({"tools": self._get_tool_schemas()})

    async def _handle_call_tool(self, request: Any) -> Any:
        from aiohttp import web

        tool_name = request.match_info.get("tool_name")
        try:
            body = await request.json()
            args = body.get("arguments", {})
        except Exception:
            args = {}

        result = self._execute_tool(tool_name, args)
        return web.json_response(result)

    async def _handle_jsonrpc(self, request: Any) -> Any:
        """Handle MCP JSON-RPC 2.0 requests."""
        from aiohttp import web

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        if method == "tools/list":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": self._get_tool_schemas()},
                }
            )
        elif method == "tools/call":
            result = self._execute_tool(params.get("name"), params.get("arguments", {}))
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}]
                    },
                }
            )
        else:
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                }
            )

    # ── Tool Execution ─────────────────────────────────────────

    def _get_tool_schemas(self) -> list[dict]:
        """Get all tool schemas."""
        from src.contexts.coding.interface.mcp_tools import (
            batch_apply_codes_tool,
            get_code_tool,
            list_codes_tool,
            list_segments_tool,
        )
        from src.contexts.projects.interface.mcp_tools import (
            get_project_context_tool,
            list_sources_tool,
            navigate_to_segment_tool,
            read_source_content_tool,
            suggest_source_metadata_tool,
        )

        tools = [
            get_project_context_tool,
            list_sources_tool,
            read_source_content_tool,
            navigate_to_segment_tool,
            suggest_source_metadata_tool,
            list_codes_tool,
            get_code_tool,
            batch_apply_codes_tool,
            list_segments_tool,
        ]
        return [t.to_schema() for t in tools]

    def _execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute tool using shared AppContext."""
        project_tools = {
            "get_project_context",
            "list_sources",
            "read_source_content",
            "navigate_to_segment",
            "suggest_source_metadata",
        }
        coding_tools = {
            "list_codes",
            "get_code",
            "batch_apply_codes",
            "list_segments_for_source",
        }

        try:
            if tool_name in project_tools:
                from src.contexts.projects.interface.mcp_tools import ProjectTools

                tools = ProjectTools(ctx=self._ctx)
                result = tools.execute(tool_name, arguments)
                if hasattr(result, "value_or"):
                    return {"success": True, "data": result.value_or(None)}
                return {"success": True, "data": result}

            elif tool_name in coding_tools:
                from src.contexts.coding.interface.mcp_tools import CodingTools

                if self._ctx.coding_context is None:
                    return {"success": False, "error": "No project open"}

                # Create wrapper that provides repos + event_bus
                coding_ctx = _CodingToolsContextWrapper(
                    coding_context=self._ctx.coding_context,
                    event_bus=self._ctx.event_bus,
                )
                tools = CodingTools(ctx=coding_ctx)
                return tools.execute(tool_name, arguments)

            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class _CodingToolsContextWrapper:
    """Wrapper providing CodingToolsContext interface from AppContext."""

    def __init__(self, coding_context, event_bus):
        self._coding_context = coding_context
        self._event_bus = event_bus

    @property
    def code_repo(self):
        return self._coding_context.code_repo

    @property
    def category_repo(self):
        return self._coding_context.category_repo

    @property
    def segment_repo(self):
        return self._coding_context.segment_repo

    @property
    def event_bus(self):
        return self._event_bus
