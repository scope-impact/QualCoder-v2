"""
E2E test: MCP Server Real-time UI Updates

Verifies that MCP tool calls trigger domain events and UI signals
via the SignalBridge. Uses qasync unified event loop (same as production).
"""

import asyncio
import random
from pathlib import Path

import allure
import httpx
import pytest
import qasync

from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
from src.shared.infra.app_context import create_app_context
from src.shared.infra.mcp_server import MCPServerManager


@pytest.fixture
def mcp_test_env(qapp, tmp_path):
    """Create app context with MCP server on a qasync unified event loop."""
    port = random.randint(19000, 19999)

    ctx = create_app_context()
    ctx.start()

    # Create and open test project
    project_path = tmp_path / "test_mcp_project.qda"
    create_result = ctx.create_project(name="MCP Test Project", path=str(project_path))
    assert create_result.is_success, f"Failed to create project: {create_result.error}"

    result = ctx.open_project(str(project_path))
    assert result.is_success, f"Failed to open project: {result.error}"

    # Signal bridge for reactive UI
    CodingSignalBridge.clear_instance()
    signal_bridge = CodingSignalBridge.instance(ctx.event_bus)
    signal_bridge.start()

    # Flush any pending deferred deletions (deleteLater) from prior tests.
    # Unprocessed DeferredDelete events fire inside qasync.QEventLoop.run_until_complete()
    # and cause it to stop prematurely with "Event loop stopped before Future completed."
    from PySide6.QtCore import QEvent

    qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()

    # Unified event loop (same as production)
    loop = qasync.QEventLoop(qapp)
    asyncio.set_event_loop(loop)

    # Start MCP server as async task
    mcp = MCPServerManager(ctx=ctx, port=port)
    loop.run_until_complete(_wait_for_server(mcp, port))

    yield {
        "ctx": ctx,
        "mcp": mcp,
        "signal_bridge": signal_bridge,
        "mcp_url": f"http://localhost:{port}",
        "port": port,
        "loop": loop,
    }

    # Cleanup
    mcp.stop()
    # Let the serve_async task finish
    loop.run_until_complete(asyncio.sleep(0.2))
    loop.close()
    CodingSignalBridge.clear_instance()
    ctx.stop()


async def _wait_for_server(mcp: MCPServerManager, port: int):
    """Start MCP server task and wait until it accepts connections.

    Uses raw TCP socket probes instead of httpx for readiness checks.
    httpx depends on anyio, which is incompatible with qasync.QEventLoop
    (anyio's CancelScope raises RuntimeError when asyncio.current_task()
    fails under qasync, corrupting the event loop's running state).
    """
    import socket

    asyncio.get_event_loop().create_task(mcp.serve_async())
    for _ in range(50):
        try:
            with socket.create_connection(("localhost", port), timeout=0.5):
                return  # Server is accepting connections
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(0.1)
    raise RuntimeError(f"MCP server did not start on port {port}")


@pytest.mark.e2e
@allure.story("QC-050.08 Tool registration and response format")
def test_mcp_server_info_tools_and_context(mcp_test_env):
    """Test MCP server responds, lists tools, and returns project context."""
    loop = mcp_test_env["loop"]
    mcp_url = mcp_test_env["mcp_url"]

    async def _test():
        async with httpx.AsyncClient() as client:
            # Verify server info endpoint
            response = await client.get(f"{mcp_url}/")
            assert response.status_code == 200
            assert response.json()["name"] == "qualcoder-v2"

            # Verify tools listing
            response = await client.get(f"{mcp_url}/tools")
            assert response.status_code == 200
            tool_names = [t["name"] for t in response.json()["tools"]]
            assert "get_project_context" in tool_names
            assert "list_codes" in tool_names
            assert "batch_apply_codes" in tool_names

            # Verify get_project_context returns open project
            response = await client.post(
                f"{mcp_url}/tools/get_project_context",
                json={"arguments": {}},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["project_open"] is True

    loop.run_until_complete(_test())


@pytest.mark.e2e
@allure.story("QC-050.08 Tool registration and response format")
def test_mcp_segment_coded_emits_signal(mcp_test_env, qapp):
    """Test that batch_apply_codes triggers segment_coded signal."""
    loop = mcp_test_env["loop"]
    ctx = mcp_test_env["ctx"]
    signal_bridge = mcp_test_env["signal_bridge"]
    mcp_url = mcp_test_env["mcp_url"]

    coding_ctx = ctx.coding_context
    if coding_ctx is None:
        pytest.skip("No coding context")

    from src.contexts.coding.core.commandHandlers import create_code
    from src.contexts.coding.core.commands import CreateCodeCommand

    result = create_code(
        command=CreateCodeCommand(name="MCPTestCode", color="#00FF00"),
        code_repo=coding_ctx.code_repo,
        category_repo=coding_ctx.category_repo,
        segment_repo=coding_ctx.segment_repo,
        event_bus=ctx.event_bus,
    )
    assert result.is_success
    code_id = result.data.id.value

    qapp.processEvents()

    sources_ctx = ctx.sources_context
    if sources_ctx is None:
        pytest.skip("No sources context")

    from src.contexts.sources.core.entities import Source, SourceStatus, SourceType
    from src.shared.common.types import SourceId

    source = Source(
        id=SourceId(value="99"),
        name="mcp_test_source.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.READY,
        file_path=Path("/tmp/mcp_test.txt"),
        fulltext="This is test content for MCP coding test.",
    )
    sources_ctx.source_repo.save(source)

    received = []
    signal_bridge.segment_coded.connect(lambda p: received.append(p))

    async def _test():
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_url}/tools/batch_apply_codes",
                json={
                    "arguments": {
                        "operations": [
                            {
                                "code_id": code_id,
                                "source_id": 99,
                                "start_position": 0,
                                "end_position": 15,
                            }
                        ]
                    }
                },
            )
        assert response.status_code == 200
        result = response.json()
        assert result.get("is_success", result.get("success")), f"Failed: {result}"

        # Let signal bridge deliver queued signals
        for _ in range(20):
            qapp.processEvents()
            await asyncio.sleep(0.02)

    loop.run_until_complete(_test())

    assert len(received) > 0, "No segment_coded signal received!"
    payload = received[0]
    assert payload.code_id == code_id
    assert payload.source_id == "99"
    assert payload.start_pos == 0
    assert payload.end_pos == 15
