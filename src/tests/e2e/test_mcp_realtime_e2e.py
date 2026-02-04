"""
E2E test: MCP Server Real-time UI Updates

Verifies that when MCP tools are called from a background thread,
the UI updates in real-time via SignalBridge.
"""

import random
import time
from pathlib import Path

import httpx
import pytest

from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
from src.shared.infra.app_context import create_app_context
from src.shared.infra.mcp_server import MCPServerManager


@pytest.fixture
def mcp_test_env(qapp, tmp_path):
    """Create app context with MCP server and test project."""
    # Use random port to avoid conflicts
    port = random.randint(19000, 19999)

    # Create app context
    ctx = create_app_context()
    ctx.start()

    # Create test project (creates the .qda directory and database)
    project_path = tmp_path / "test_mcp_project.qda"
    create_result = ctx.create_project(name="MCP Test Project", path=str(project_path))
    assert create_result.is_success, f"Failed to create project: {create_result.error}"

    # Open the project (this initializes bounded contexts)
    result = ctx.open_project(str(project_path))
    assert result.is_success, f"Failed to open project: {result.error}"

    # Clear any existing singleton and start signal bridge
    CodingSignalBridge.clear_instance()
    signal_bridge = CodingSignalBridge.instance(ctx.event_bus)
    signal_bridge.start()

    # Start MCP server
    mcp = MCPServerManager(ctx=ctx, port=port)
    mcp.start()
    time.sleep(0.3)  # Wait for server to start

    yield {
        "ctx": ctx,
        "mcp": mcp,
        "signal_bridge": signal_bridge,
        "mcp_url": f"http://localhost:{port}",
        "port": port,
    }

    # Cleanup
    mcp.stop()
    CodingSignalBridge.clear_instance()
    ctx.stop()


@pytest.mark.e2e
def test_mcp_server_responds(mcp_test_env):
    """Test MCP server info endpoint."""
    mcp_url = mcp_test_env["mcp_url"]

    response = httpx.get(f"{mcp_url}/", timeout=5.0)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "qualcoder-v2"


@pytest.mark.e2e
def test_mcp_lists_tools(mcp_test_env):
    """Test MCP server lists all tools."""
    mcp_url = mcp_test_env["mcp_url"]

    response = httpx.get(f"{mcp_url}/tools", timeout=5.0)
    assert response.status_code == 200
    tools = response.json()["tools"]

    tool_names = [t["name"] for t in tools]
    assert "get_project_context" in tool_names
    assert "list_codes" in tool_names
    assert "batch_apply_codes" in tool_names


@pytest.mark.e2e
def test_mcp_get_project_context(mcp_test_env):
    """Test get_project_context returns open project."""
    mcp_url = mcp_test_env["mcp_url"]

    response = httpx.post(
        f"{mcp_url}/tools/get_project_context",
        json={"arguments": {}},
        timeout=5.0,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["project_open"] is True


@pytest.mark.e2e
def test_mcp_segment_coded_emits_signal(mcp_test_env, qapp):
    """Test that batch_apply_codes triggers segment_coded signal."""
    ctx = mcp_test_env["ctx"]
    signal_bridge = mcp_test_env["signal_bridge"]
    mcp_url = mcp_test_env["mcp_url"]

    coding_ctx = ctx.coding_context
    if coding_ctx is None:
        pytest.skip("No coding context")

    # Create a code directly
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

    # Process events from code creation
    qapp.processEvents()

    # Create a source with text
    sources_ctx = ctx.sources_context
    if sources_ctx is None:
        pytest.skip("No sources context")

    from src.contexts.sources.core.entities import Source, SourceStatus, SourceType
    from src.shared.common.types import SourceId

    source = Source(
        id=SourceId(value=99),
        name="mcp_test_source.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.READY,
        file_path=Path("/tmp/mcp_test.txt"),
        fulltext="This is test content for MCP coding test.",
    )
    sources_ctx.source_repo.save(source)

    # Track segment_coded signals
    received = []

    def on_segment_coded(payload):
        received.append(payload)

    signal_bridge.segment_coded.connect(on_segment_coded)

    # Call batch_apply_codes via MCP
    response = httpx.post(
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
        timeout=5.0,
    )
    assert response.status_code == 200
    result = response.json()
    assert result.get("is_success", result.get("success")), f"Failed: {result}"

    # Process Qt events to allow cross-thread signals
    for _ in range(20):
        qapp.processEvents()
        time.sleep(0.02)

    # Verify signal was received
    assert len(received) > 0, "No segment_coded signal received!"
    payload = received[0]
    assert payload.code_id == code_id
    assert payload.source_id == 99
    assert payload.start_pos == 0
    assert payload.end_pos == 15
    print(
        f"✓ Received segment_coded signal: code={payload.code_id}, pos={payload.start_pos}-{payload.end_pos}"
    )
