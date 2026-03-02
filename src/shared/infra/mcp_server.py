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
import queue
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QMetaObject, QObject, Qt, Slot

from src.shared.infra.signal_bridge.thread_utils import is_main_thread

if TYPE_CHECKING:
    from src.shared.infra.app_context import AppContext

# Configure MCP logger
logger = logging.getLogger("qualcoder.mcp")


def _setup_mcp_logging(debug: bool = False) -> None:
    """Configure MCP server logging level.

    Output is handled by the root ``qualcoder`` logger (set up by
    ``configure_logging``), so we only adjust the level here — no extra
    handler needed.
    """
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)


class MCPLogAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request_id to log records."""

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["request_id"] = self.extra.get("request_id", "-")
        return msg, kwargs


@dataclass
class _ToolRequest:
    """A request to execute tool logic on the main thread."""

    fn: Callable[[], dict]
    result: dict | None = None
    exception: Exception | None = None
    done_event: threading.Event = field(default_factory=threading.Event)


class _MainThreadExecutor(QObject):
    """Marshals callable execution to the Qt main thread.

    Uses a thread-safe queue + QMetaObject.invokeMethod(QueuedConnection) to
    schedule work on the main event loop, then blocks the caller until the
    work completes via threading.Event.
    """

    _TIMEOUT_SECONDS = 30.0

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._queue: queue.Queue[_ToolRequest] = queue.Queue()
        self._log = logging.getLogger("qualcoder.mcp.executor")

    def execute(self, fn: Callable[[], dict]) -> dict:
        """Execute *fn* on the Qt main thread, blocking the caller until done.

        If already on the main thread (e.g. in tests), runs directly.
        """
        if is_main_thread():
            self._log.debug("Already on main thread, executing directly")
            return fn()

        request = _ToolRequest(fn=fn)
        self._queue.put(request)
        queue_size = self._queue.qsize()
        self._log.debug(
            "Queued request for main thread (thread=%s, queue_size=%d)",
            threading.current_thread().name,
            queue_size,
        )
        QMetaObject.invokeMethod(self, "_process", Qt.ConnectionType.QueuedConnection)
        if not request.done_event.wait(timeout=self._TIMEOUT_SECONDS):
            self._log.error(
                "Main-thread execution timed out after %.1fs (thread=%s)",
                self._TIMEOUT_SECONDS,
                threading.current_thread().name,
            )
            raise TimeoutError(
                f"Main-thread execution timed out after {self._TIMEOUT_SECONDS}s"
            )
        if request.exception is not None:
            self._log.error(
                "Main-thread execution raised: %s", request.exception, exc_info=True
            )
            raise request.exception
        self._log.debug("Main-thread execution completed successfully")
        assert request.result is not None  # noqa: S101
        return request.result

    @Slot()
    def _process(self) -> None:
        """Drain the queue on the main thread and execute each request."""
        processed = 0
        while True:
            try:
                request = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                request.result = request.fn()
                processed += 1
            except Exception as exc:
                self._log.error(
                    "Exception during main-thread execution: %s", exc, exc_info=True
                )
                request.exception = exc
            finally:
                request.done_event.set()
        if processed:
            self._log.debug("Processed %d queued request(s) on main thread", processed)


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
        self._executor: _MainThreadExecutor | None = None

        # Debug mode: explicit param > MCP_DEBUG > QUALCODER_DEV > default False
        if debug is None:
            debug = os.environ.get(
                "MCP_DEBUG", os.environ.get("QUALCODER_DEV", "")
            ).lower() in ("1", "true", "yes")
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
        # Create executor on main thread so its QObject affinity is correct
        self._executor = _MainThreadExecutor()
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        self._log.info("Server starting on port %d (debug=%s)", self._port, self._debug)

    def stop(self):
        """Stop MCP server."""
        if not self._running:
            return

        self._log.info("Server stopping...")
        self._running = False
        self._executor = None
        # Don't force-stop the loop; _serve() checks _running every 100ms
        # and exits gracefully, allowing run_until_complete to finish cleanly.
        if self._thread:
            self._thread.join(timeout=2.0)
        self._log.info("Server stopped")

    def _run_server(self):
        """Run async server in background thread."""
        self._log.debug(
            "MCP server thread started (thread=%s)", threading.current_thread().name
        )
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:
            self._log.exception("Server error: %s", e)
            self._stats["errors"] += 1
        finally:
            self._loop.close()
            self._log.debug("MCP server event loop closed")

    def _create_logging_middleware(self):
        """Create request/response logging middleware."""
        from aiohttp import web

        @web.middleware
        async def logging_middleware(request, handler):
            from src.shared.infra.metrics import mcp_requests

            request_id = uuid.uuid4().hex[:8]
            request["request_id"] = request_id
            self._stats["requests"] += 1
            mcp_requests.add(1, {"method": request.method, "path": request.path})

            log = MCPLogAdapter(logger, {"request_id": request_id})
            start_time = time.perf_counter()

            if self._debug:
                log.debug("%s %s", request.method, request.path)

            try:
                response = await handler(request)
                elapsed = (time.perf_counter() - start_time) * 1000

                if self._debug:
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
                self._stats["errors"] += 1
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

        app = web.Application(
            middlewares=[self._create_logging_middleware()],
            handler_args={"tcp_keepalive": False},
        )
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

        result = await self._run_tool_on_main_thread(tool_name, args, log)
        return web.json_response(result, dumps=lambda o: json.dumps(o, default=str))

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

        def _jsonrpc_ok(result: Any) -> Any:
            return web.json_response({"jsonrpc": "2.0", "id": req_id, "result": result})

        if method == "initialize":
            log.info("Client initialized")
            return _jsonrpc_ok(
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "qualcoder-v2", "version": "0.2.0"},
                }
            )

        if method in ("notifications/initialized", "ping"):
            return _jsonrpc_ok({})

        if method == "tools/list":
            return _jsonrpc_ok({"tools": self._get_tool_schemas()})

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            result = await self._run_tool_on_main_thread(tool_name, tool_args, log)
            return _jsonrpc_ok(
                {"content": [{"type": "text", "text": json.dumps(result, default=str)}]}
            )

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
                segment_id=SegmentId(value="999999"),
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

            def _publish() -> dict:
                self._ctx.event_bus.publish(event)
                return {"published": True, "source_id": source_id}

            result = await self._run_on_main_thread(_publish)
            log.info("Event published successfully")

            return web.json_response(result)

        except Exception as e:
            log.exception("Failed to publish debug event: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    # ── Main-Thread Marshalling ─────────────────────────────────

    async def _run_tool_on_main_thread(
        self,
        tool_name: str,
        args: dict,
        log: MCPLogAdapter,
    ) -> dict:
        """Marshal tool execution to the Qt main thread without blocking asyncio.

        Uses ``run_in_executor`` so the blocking ``_MainThreadExecutor.execute()``
        call happens on a pool thread, keeping the asyncio event loop responsive.
        """
        executor = self._executor
        if executor is None:
            # Fallback: no executor (tests, or server not fully started)
            log.debug("No executor — running tool %s directly (fallback)", tool_name)
            return self._execute_tool(tool_name, args, log)

        log.debug("Marshalling tool %s to main thread via run_in_executor", tool_name)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # default ThreadPoolExecutor
            lambda: executor.execute(lambda: self._execute_tool(tool_name, args, log)),
        )

    async def _run_on_main_thread(self, fn: Callable[[], dict]) -> dict:
        """Marshal an arbitrary callable to the main thread."""
        executor = self._executor
        if executor is None:
            self._log.debug("No executor — running callable directly (fallback)")
            return fn()

        self._log.debug("Marshalling callable to main thread via run_in_executor")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: executor.execute(fn),
        )

    # ── Tool Execution ─────────────────────────────────────────

    def _get_tool_schemas(self) -> list[dict]:
        """Get all tool schemas from all context tool classes."""
        from src.contexts.coding.interface.tool_definitions import ALL_TOOLS
        from src.contexts.folders.interface.mcp_tools import ALL_FOLDER_TOOLS
        from src.contexts.projects.interface.mcp_tools import ALL_PROJECT_TOOLS
        from src.contexts.projects.interface.vcs_mcp_tools import (
            initialize_version_control_tool,
            list_snapshots_tool,
            restore_snapshot_tool,
            view_diff_tool,
        )
        from src.contexts.sources.interface.mcp_tools import ALL_SOURCE_TOOLS

        vcs_tools_list = [
            list_snapshots_tool,
            view_diff_tool,
            restore_snapshot_tool,
            initialize_version_control_tool,
        ]

        schemas = []
        for tools_dict in [
            ALL_PROJECT_TOOLS,
            ALL_SOURCE_TOOLS,
            ALL_FOLDER_TOOLS,
            ALL_TOOLS,
        ]:
            schemas.extend(t.to_schema() for t in tools_dict.values())

        # VCS tools
        schemas.extend(t.to_schema() for t in vcs_tools_list)

        # Cloud sync tools
        try:
            from src.contexts.settings.interface.cloud_sync_mcp_tools import (
                configure_cloud_sync_tool,
                get_sync_settings_tool,
            )
            from src.contexts.settings.interface.cloud_sync_mcp_tools import (
                get_sync_status_tool as cloud_sync_status_tool,
            )

            for tool in [
                cloud_sync_status_tool,
                configure_cloud_sync_tool,
                get_sync_settings_tool,
            ]:
                schemas.append(tool.to_schema())
        except ImportError:
            pass  # Cloud sync tools not available

        return schemas

    def _get_all_result_tool_names(self) -> set[str]:
        """Get tool names that return returns.Result (project, source, folder tools)."""
        from src.contexts.folders.interface.mcp_tools import ALL_FOLDER_TOOLS
        from src.contexts.projects.interface.mcp_tools import ALL_PROJECT_TOOLS
        from src.contexts.sources.interface.mcp_tools import ALL_SOURCE_TOOLS

        return (
            set(ALL_PROJECT_TOOLS.keys())
            | set(ALL_SOURCE_TOOLS.keys())
            | set(ALL_FOLDER_TOOLS.keys())
        )

    def _get_cloud_sync_tool_names(self) -> set[str]:
        """Get cloud sync tool names."""
        return {"get_sync_status", "configure_cloud_sync", "get_sync_settings"}

    def _get_vcs_tool_names(self) -> set[str]:
        """Get version control tool names."""
        return {
            "list_snapshots",
            "view_diff",
            "restore_snapshot",
            "initialize_version_control",
        }

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

        result_tool_names = self._get_all_result_tool_names()
        coding_tools = set(ALL_TOOLS.keys())
        cloud_sync_tools = self._get_cloud_sync_tool_names()
        vcs_tools = self._get_vcs_tool_names()

        from src.shared.infra.metrics import (
            mcp_errors,
            mcp_tool_calls,
            mcp_tool_duration,
        )

        self._stats["tool_calls"] += 1
        mcp_tool_calls.add(1, {"tool_name": tool_name})
        start_time = time.perf_counter()

        if self._debug:
            args_str = json.dumps(arguments)
            if len(args_str) > 200:
                args_str = args_str[:200] + "..."
            log.debug("Tool call: %s args=%s", tool_name, args_str)

        try:
            if tool_name in result_tool_names:
                result = self._execute_result_tool(tool_name, arguments)

            elif tool_name in coding_tools:
                from src.contexts.coding.interface.mcp_tools import CodingTools

                if self._ctx.coding_context is None:
                    self._coding_tools = None
                    log.warning("Tool %s called with no project open", tool_name)
                    return {"success": False, "error": "No project open"}

                if self._coding_tools is None:
                    coding_ctx = _CodingToolsContextWrapper(ctx=self._ctx)
                    self._coding_tools = CodingTools(ctx=coding_ctx)
                result = self._coding_tools.execute(tool_name, arguments)

            elif tool_name in cloud_sync_tools:
                from src.contexts.settings.interface.cloud_sync_mcp_tools import (
                    CloudSyncMCPTools,
                )

                tools = CloudSyncMCPTools(
                    settings_repo=self._ctx.settings_repo,
                    event_bus=self._ctx.event_bus,
                )
                return tools.handle_tool_call(tool_name, arguments)

            elif tool_name in vcs_tools:
                from src.contexts.projects.interface.vcs_mcp_tools import (
                    VersionControlMCPTools,
                )

                projects_ctx = self._ctx.projects_context
                if projects_ctx is None:
                    log.warning("Tool %s called with no project open", tool_name)
                    return {"success": False, "error": "No project open"}

                vcs = VersionControlMCPTools(
                    diffable=projects_ctx.diffable_adapter,
                    git=projects_ctx.git_adapter,
                    event_bus=self._ctx.event_bus,
                    state=self._ctx.state,
                )
                result = vcs.execute(tool_name, arguments)

            else:
                log.warning("Unknown tool requested: %s", tool_name)
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

            elapsed = (time.perf_counter() - start_time) * 1000
            mcp_tool_duration.record(elapsed, {"tool_name": tool_name})
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
            mcp_tool_duration.record(elapsed, {"tool_name": tool_name})
            self._stats["errors"] += 1
            mcp_errors.add(1, {"tool_name": tool_name})
            log.exception(
                "Tool %s raised exception (%.1fms): %s", tool_name, elapsed, e
            )
            return {"success": False, "error": str(e)}

    def _execute_result_tool(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool that returns returns.Result, converting to dict."""
        from returns.result import Failure

        from src.contexts.folders.interface.mcp_tools import (
            ALL_FOLDER_TOOLS,
            FolderTools,
        )
        from src.contexts.projects.interface.mcp_tools import (
            ALL_PROJECT_TOOLS,
            ProjectTools,
        )
        from src.contexts.sources.interface.mcp_tools import (
            ALL_SOURCE_TOOLS,
            SourceTools,
        )

        if tool_name in ALL_PROJECT_TOOLS:
            result = ProjectTools(ctx=self._ctx).execute(tool_name, arguments)
        elif tool_name in ALL_SOURCE_TOOLS:
            result = SourceTools(ctx=self._ctx).execute(tool_name, arguments)
        elif tool_name in ALL_FOLDER_TOOLS:
            result = FolderTools(ctx=self._ctx).execute(tool_name, arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        if isinstance(result, Failure):
            failure_val = result.failure()
            # Support structured error dicts (OperationResult format)
            if isinstance(failure_val, dict):
                return failure_val
            return {"success": False, "error": failure_val}
        return {"success": True, "data": result.unwrap()}


class _CodingToolsContextWrapper:
    """Wrapper providing CodingToolsContext interface from AppContext.

    Delegates to the live AppContext so that project close/reopen cycles
    always provide fresh contexts with active database connections.
    """

    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    @property
    def coding_context(self):
        return self._ctx.coding_context

    @property
    def sources_context(self):
        return self._ctx.sources_context

    @property
    def code_repo(self):
        cc = self._ctx.coding_context
        return cc.code_repo if cc else None

    @property
    def category_repo(self):
        cc = self._ctx.coding_context
        return cc.category_repo if cc else None

    @property
    def segment_repo(self):
        cc = self._ctx.coding_context
        return cc.segment_repo if cc else None

    @property
    def event_bus(self):
        return self._ctx.event_bus
