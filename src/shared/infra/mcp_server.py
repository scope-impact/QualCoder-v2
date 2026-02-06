"""
QualCoder v2 Embedded MCP Server

Runs inside the QualCoder app, sharing AppContext and EventBus
for real-time AI agent interaction.

Usage in main.py:
    from src.shared.infra.mcp_server import MCPServerManager

    self._mcp_server = MCPServerManager(ctx=self._ctx)
    self._mcp_server.start()  # Starts on localhost:8765

Debug mode:
    self._mcp_server = MCPServerManager(ctx=self._ctx, debug=True)
    # Or set environment variable: MCP_DEBUG=1
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.shared.infra.app_context import AppContext

# Configure MCP logger
logger = logging.getLogger("qualcoder.mcp")


def _setup_mcp_logging(debug: bool = False) -> None:
    """Configure MCP server logging."""
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # Only add handler if none exist (avoid duplicates)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[MCP] %(asctime)s.%(msecs)03d %(levelname)s [%(request_id)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


class MCPLogAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request_id to log records."""

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["request_id"] = self.extra.get("request_id", "-")
        return msg, kwargs


class MCPServerManager:
    """Manages embedded MCP HTTP server lifecycle."""

    DEFAULT_PORT = 8765

    def __init__(
        self,
        ctx: AppContext,
        port: int = DEFAULT_PORT,
        debug: bool | None = None,
    ):
        self._ctx = ctx
        self._port = port
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._coding_tools: Any = None  # Cached CodingTools instance

        # Debug mode: explicit param > env var > default False
        if debug is None:
            debug = os.environ.get("MCP_DEBUG", "").lower() in ("1", "true", "yes")
        self._debug = debug
        _setup_mcp_logging(debug)
        self._log = MCPLogAdapter(logger, {"request_id": "init"})

        # Stats for debugging
        self._stats = {
            "requests": 0,
            "tool_calls": 0,
            "errors": 0,
            "start_time": None,
        }

    @property
    def url(self) -> str:
        return f"http://localhost:{self._port}"

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def stats(self) -> dict:
        """Return server statistics."""
        return {
            **self._stats,
            "uptime_seconds": (
                time.time() - self._stats["start_time"]
                if self._stats["start_time"]
                else 0
            ),
        }

    def start(self):
        """Start MCP server in background thread."""
        if self._running:
            self._log.warning("Server already running")
            return

        self._running = True
        self._stats["start_time"] = time.time()
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        self._log.info("Server starting on port %d (debug=%s)", self._port, self._debug)

    def stop(self):
        """Stop MCP server."""
        if not self._running:
            return

        self._log.info("Server stopping...")
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)
        self._log.info("Server stopped")

    def _run_server(self):
        """Run async server in background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:
            self._log.exception("Server error: %s", e)
            self._stats["errors"] += 1
        finally:
            self._loop.close()

    def _create_logging_middleware(self):
        """Create request/response logging middleware."""
        from aiohttp import web

        server = self  # Capture reference for closure

        @web.middleware
        async def logging_middleware(request, handler):
            # Generate unique request ID
            request_id = uuid.uuid4().hex[:8]
            request["request_id"] = request_id
            server._stats["requests"] += 1

            log = MCPLogAdapter(logger, {"request_id": request_id})
            start_time = time.perf_counter()

            if server._debug:
                log.debug("%s %s", request.method, request.path)

            try:
                response = await handler(request)
                elapsed = (time.perf_counter() - start_time) * 1000

                if server._debug:
                    log.debug(
                        "%s %s -> %d (%.1fms)",
                        request.method,
                        request.path,
                        response.status,
                        elapsed,
                    )
                return response
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                server._stats["errors"] += 1
                log.error(
                    "%s %s -> ERROR (%.1fms): %s",
                    request.method,
                    request.path,
                    elapsed,
                    e,
                )
                raise

        return logging_middleware

    async def _serve(self):
        """Main server coroutine."""
        try:
            from aiohttp import web
        except ImportError:
            self._log.error("aiohttp not installed. Run: uv add aiohttp")
            return

        app = web.Application(middlewares=[self._create_logging_middleware()])
        app.router.add_get("/", self._handle_info)
        app.router.add_get("/tools", self._handle_list_tools)
        app.router.add_post("/tools/{tool_name}", self._handle_call_tool)
        app.router.add_post("/mcp", self._handle_jsonrpc)
        # Debug endpoints
        app.router.add_get("/debug/status", self._handle_debug_status)
        app.router.add_get("/debug/stats", self._handle_debug_stats)
        app.router.add_post("/debug/publish_event", self._handle_debug_publish)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self._port)
        await site.start()

        self._log.info("Server ready at http://localhost:%d", self._port)

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

        request_id = request.get("request_id", "-")
        log = MCPLogAdapter(logger, {"request_id": request_id})

        tool_name = request.match_info.get("tool_name")
        try:
            body = await request.json()
            args = body.get("arguments", {})
        except Exception:
            args = {}

        result = self._execute_tool(tool_name, args, log)
        return web.json_response(result)

    async def _handle_jsonrpc(self, request: Any) -> Any:
        """Handle MCP JSON-RPC 2.0 requests."""
        from aiohttp import web

        request_id = request.get("request_id", "-")
        log = MCPLogAdapter(logger, {"request_id": request_id})

        try:
            body = await request.json()
        except Exception:
            log.warning("Invalid JSON in request body")
            return web.json_response({"error": "Invalid JSON"}, status=400)

        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        if self._debug:
            log.debug("JSON-RPC method=%s id=%s", method, req_id)

        # MCP Protocol: initialize
        if method == "initialize":
            log.info("Client initialized")
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                        "serverInfo": {
                            "name": "qualcoder-v2",
                            "version": "0.2.0",
                        },
                    },
                }
            )
        # MCP Protocol: initialized notification (no response needed)
        elif method == "notifications/initialized" or method == "ping":
            return web.json_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
        # MCP Protocol: tools/list
        elif method == "tools/list":
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": self._get_tool_schemas()},
                }
            )
        # MCP Protocol: tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result = self._execute_tool(tool_name, tool_args, log)
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
            log.warning("Unknown method: %s", method)
            return web.json_response(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                }
            )

    async def _handle_debug_status(self, _request: Any) -> Any:
        """Debug endpoint: server status and state."""
        from aiohttp import web

        return web.json_response(
            {
                "running": self._running,
                "port": self._port,
                "debug": self._debug,
                "project_open": self._ctx.coding_context is not None,
                "coding_tools_cached": self._coding_tools is not None,
                "url": self.url,
            }
        )

    async def _handle_debug_stats(self, _request: Any) -> Any:
        """Debug endpoint: server statistics."""
        from aiohttp import web

        return web.json_response(self.stats)

    async def _handle_debug_publish(self, request: Any) -> Any:
        """Debug endpoint to test event publishing."""
        from aiohttp import web

        request_id = request.get("request_id", "-")
        log = MCPLogAdapter(logger, {"request_id": request_id})

        try:
            from src.contexts.coding.core.entities import TextPosition
            from src.contexts.coding.core.events import SegmentCoded
            from src.shared.common.types import CodeId, SegmentId, SourceId

            try:
                body = await request.json()
                source_id = body.get("source_id", 114101)
                code_id = body.get("code_id", 284370)
            except Exception:
                source_id, code_id = 114101, 284370

            event = SegmentCoded.create(
                segment_id=SegmentId(value=999999),
                code_id=CodeId(value=code_id),
                code_name="test",
                source_id=SourceId(value=source_id),
                source_name="debug_source",
                position=TextPosition(start=0, end=100),
                selected_text="Debug test segment",
                memo=None,
            )

            log.info(
                "Publishing SegmentCoded event: source=%d code=%d", source_id, code_id
            )
            self._ctx.event_bus.publish(event)
            log.info("Event published successfully")

            return web.json_response({"published": True, "source_id": source_id})

        except Exception as e:
            log.exception("Failed to publish debug event: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    # ── Tool Execution ─────────────────────────────────────────

    def _get_tool_schemas(self) -> list[dict]:
        """Get all tool schemas."""
        from src.contexts.coding.interface.tool_definitions import ALL_TOOLS
        from src.contexts.projects.interface.mcp_tools import (
            get_project_context_tool,
            list_sources_tool,
            navigate_to_segment_tool,
            read_source_content_tool,
            suggest_source_metadata_tool,
        )

        project_tools = [
            get_project_context_tool,
            list_sources_tool,
            read_source_content_tool,
            navigate_to_segment_tool,
            suggest_source_metadata_tool,
        ]
        schemas = [t.to_schema() for t in project_tools]
        schemas.extend([t.to_schema() for t in ALL_TOOLS.values()])
        return schemas

    def _execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        log: MCPLogAdapter | None = None,
    ) -> dict:
        """Execute tool using shared AppContext with timing and logging."""
        from src.contexts.coding.interface.tool_definitions import ALL_TOOLS

        if log is None:
            log = self._log

        project_tools = {
            "get_project_context",
            "list_sources",
            "read_source_content",
            "navigate_to_segment",
            "suggest_source_metadata",
        }
        coding_tools = set(ALL_TOOLS.keys())

        self._stats["tool_calls"] += 1
        start_time = time.perf_counter()

        if self._debug:
            # Truncate large arguments for logging
            args_str = json.dumps(arguments)
            if len(args_str) > 200:
                args_str = args_str[:200] + "..."
            log.debug("Tool call: %s args=%s", tool_name, args_str)

        try:
            if tool_name in project_tools:
                from src.contexts.projects.interface.mcp_tools import ProjectTools

                tools = ProjectTools(ctx=self._ctx)
                result = tools.execute(tool_name, arguments)
                if hasattr(result, "value_or"):
                    result = {"success": True, "data": result.value_or(None)}
                else:
                    result = {"success": True, "data": result}

            elif tool_name in coding_tools:
                from src.contexts.coding.interface.mcp_tools import CodingTools

                if self._ctx.coding_context is None:
                    self._coding_tools = None  # Reset cache when no project
                    log.warning("Tool %s called with no project open", tool_name)
                    return {"success": False, "error": "No project open"}

                # Reuse cached CodingTools to preserve SuggestionCache
                if self._coding_tools is None:
                    coding_ctx = _CodingToolsContextWrapper(
                        coding_context=self._ctx.coding_context,
                        event_bus=self._ctx.event_bus,
                    )
                    self._coding_tools = CodingTools(ctx=coding_ctx)
                result = self._coding_tools.execute(tool_name, arguments)

            else:
                log.warning("Unknown tool requested: %s", tool_name)
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

            # Log successful completion with timing
            elapsed = (time.perf_counter() - start_time) * 1000
            success = result.get("success", True)
            if self._debug:
                log.debug(
                    "Tool %s completed: success=%s (%.1fms)",
                    tool_name,
                    success,
                    elapsed,
                )
            elif not success:
                log.warning(
                    "Tool %s failed (%.1fms): %s",
                    tool_name,
                    elapsed,
                    result.get("error", "unknown"),
                )

            return result

        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            self._stats["errors"] += 1
            log.exception(
                "Tool %s raised exception (%.1fms): %s", tool_name, elapsed, e
            )
            return {"success": False, "error": str(e)}


class _CodingToolsContextWrapper:
    """Wrapper providing CodingToolsContext interface from AppContext."""

    def __init__(self, coding_context, event_bus):
        self._coding_context = coding_context
        self._event_bus = event_bus

    @property
    def coding_context(self):
        return self._coding_context

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
