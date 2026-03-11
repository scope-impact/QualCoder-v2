"""
Thread-safe repository access - E2E tests.

Validates that the SingletonThreadPool + connection_factory enables safe
multi-threaded database access so the MCP server can run _execute_tool()
via asyncio.to_thread() without SQLite thread-safety violations.
"""

from __future__ import annotations

import threading
from pathlib import Path

import allure
import pytest

from src.shared.infra.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-INF Thread-Safe Repositories"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_project(app_context: AppContext, tmp_path: Path, name: str) -> Path:
    project_path = tmp_path / f"{name}.qda"
    result = app_context.create_project(name=name, path=str(project_path))
    assert result.is_success, f"Failed to create project: {result.error}"
    # create_project doesn't initialize contexts; open it to wire repos
    result = app_context.open_project(path=str(project_path))
    assert result.is_success, f"Failed to open project: {result.error}"
    return project_path


# ---------------------------------------------------------------------------
# Test 1: Engine uses SingletonThreadPool and connection_factory works
# ---------------------------------------------------------------------------


@allure.story("QC-INF.01 SingletonThreadPool Connection Factory")
class TestConnectionFactory:
    @allure.title("Engine uses SingletonThreadPool and factory returns same conn on same thread")
    def test_engine_pool_and_factory_same_thread(
        self, app_context: AppContext, tmp_path: Path
    ):
        from sqlalchemy.pool import SingletonThreadPool

        _open_project(app_context, tmp_path, "pool_type")
        engine = app_context.lifecycle.engine
        assert engine is not None
        assert isinstance(engine.pool, SingletonThreadPool)

        factory = app_context.lifecycle.connection_factory
        assert factory is not None
        assert callable(factory)

        conn1 = factory()
        conn2 = factory()
        assert conn1 is conn2, "Same thread should get same cached connection"

    @allure.title("Factory returns different conn on different thread with busy_timeout")
    def test_factory_different_thread_with_busy_timeout(
        self, app_context: AppContext, tmp_path: Path
    ):
        from sqlalchemy import text

        _open_project(app_context, tmp_path, "factory_diff")
        factory = app_context.lifecycle.connection_factory

        main_conn = factory()
        worker_conn = None
        busy_timeout = None
        errors: list[Exception] = []

        def _worker():
            nonlocal worker_conn, busy_timeout
            try:
                worker_conn = factory()
                row = worker_conn.execute(text("PRAGMA busy_timeout")).fetchone()
                busy_timeout = row[0] if row else None
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=5)

        assert not errors, f"Worker thread failed: {errors}"
        assert worker_conn is not None
        assert worker_conn is not main_conn
        assert busy_timeout == 5000, f"Expected busy_timeout=5000, got {busy_timeout}"


# ---------------------------------------------------------------------------
# Test 2: Repo reads/writes from worker thread
# ---------------------------------------------------------------------------


@allure.story("QC-INF.02 Repo Worker Thread Access")
class TestRepoWorkerThreadAccess:
    @allure.title("Worker and main threads can read each other's writes")
    def test_cross_thread_reads_and_writes(
        self, app_context: AppContext, tmp_path: Path
    ):
        _open_project(app_context, tmp_path, "repo_rw")
        code_repo = app_context.coding_context.code_repo

        from src.contexts.coding.core.entities import Code, Color
        from src.shared.common.types import CodeId

        # Main writes, worker reads
        code_repo.save(
            Code(id=CodeId(1), name="main-code", color=Color.from_hex("#FF0000"))
        )
        app_context.session.commit()

        read_results: dict = {}
        errors: list[Exception] = []

        def _reader():
            try:
                codes = code_repo.get_all()
                read_results["count"] = len(codes)
                read_results["names"] = [c.name for c in codes]
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=_reader)
        t.start()
        t.join(timeout=5)

        assert not errors, f"Worker read failed: {errors}"
        assert read_results["count"] >= 1
        assert "main-code" in read_results["names"]

        # Worker writes, main reads
        def _writer():
            try:
                code_repo.save(
                    Code(
                        id=CodeId(99),
                        name="worker-code",
                        color=Color.from_hex("#00FF00"),
                    )
                )
                app_context.session.commit()
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=_writer)
        t.start()
        t.join(timeout=5)

        assert not errors, f"Worker write failed: {errors}"
        codes = code_repo.get_all()
        assert any(c.name == "worker-code" for c in codes)


# ---------------------------------------------------------------------------
# Test 3: Concurrent reads + writes (simulates MCP + UI)
# ---------------------------------------------------------------------------


@allure.story("QC-INF.03 Concurrent Repo Access Stress Test")
class TestConcurrentRepoAccess:
    @allure.title("MCP worker thread and UI main thread can access repos concurrently")
    def test_concurrent_read_write(self, app_context: AppContext, tmp_path: Path):
        _open_project(app_context, tmp_path, "concurrent")
        code_repo = app_context.coding_context.code_repo

        from src.contexts.coding.core.entities import Code, Color
        from src.shared.common.types import CodeId

        errors: list[tuple[str, Exception]] = []
        barrier = threading.Barrier(2, timeout=5)

        def _mcp_worker():
            """Simulate MCP tool calls from asyncio.to_thread."""
            try:
                barrier.wait()
                for i in range(20):
                    code_repo.save(
                        Code(
                            id=CodeId(1000 + i),
                            name=f"mcp-{i}",
                            color=Color.from_hex("#AA0000"),
                        )
                    )
                    app_context.session.commit()
                    code_repo.get_all()
            except Exception as e:
                errors.append(("worker", e))

        t = threading.Thread(target=_mcp_worker)
        t.start()

        # Main thread does concurrent reads (simulates UI/ViewModel)
        try:
            barrier.wait()
            for _ in range(20):
                code_repo.get_all()
        except Exception as e:
            errors.append(("main", e))

        t.join(timeout=10)

        with allure.step(f"Concurrent access completed with {len(errors)} errors"):
            assert not errors, f"Concurrent access failed: {errors}"

        codes = code_repo.get_all()
        mcp_codes = [c for c in codes if c.name.startswith("mcp-")]
        assert len(mcp_codes) == 20, f"Expected 20 mcp codes, got {len(mcp_codes)}"


# ---------------------------------------------------------------------------
# Test 4: asyncio.to_thread with real MCP path
# ---------------------------------------------------------------------------


@allure.story("QC-INF.04 MCP asyncio.to_thread Integration")
class TestMcpAsyncToThread:
    @allure.title("_execute_tool runs safely via asyncio.to_thread for reads and writes")
    def test_execute_tool_reads_and_writes_in_thread(self, app_context: AppContext, tmp_path: Path):
        import asyncio

        _open_project(app_context, tmp_path, "async_thread")

        from src.shared.infra.mcp_server import MCPServerManager

        server = MCPServerManager(ctx=app_context)

        async def _run():
            # Concurrent reads
            r1, r2 = await asyncio.gather(
                asyncio.to_thread(server._execute_tool, "list_codes", {}, None),
                asyncio.to_thread(server._execute_tool, "list_codes", {}, None),
            )
            assert r1["success"], f"Tool call 1 failed: {r1}"
            assert r2["success"], f"Tool call 2 failed: {r2}"

            # Sequential write then read
            result = await asyncio.to_thread(
                server._execute_tool,
                "create_code",
                {"name": "thread-code", "color": "#123456"},
                None,
            )
            assert result.get("success"), f"create_code failed: {result}"

            result = await asyncio.to_thread(
                server._execute_tool, "list_codes", {}, None
            )
            return result

        result = asyncio.run(_run())
        assert result["success"]
        codes = result.get("data", [])
        assert any(c.get("name") == "thread-code" for c in codes), (
            f"thread-code not found in {codes}"
        )


# ---------------------------------------------------------------------------
# Test 5: Cleanup on project close (engine.dispose handles pool cleanup)
# ---------------------------------------------------------------------------


@allure.story("QC-INF.05 Pool Cleanup on Project Close")
class TestPoolCleanup:
    @allure.title("Project close disposes engine and clears connection_factory")
    def test_close_cleans_up(self, app_context: AppContext, tmp_path: Path):
        _open_project(app_context, tmp_path, "cleanup")

        # Verify factory exists while project is open
        assert app_context.lifecycle.connection_factory is not None

        # Create a worker connection to exercise the pool
        def _worker():
            factory = app_context.lifecycle.connection_factory
            factory()  # creates a pooled connection for this thread

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=5)

        # Close project — engine.dispose() should clean up all pooled connections
        app_context.close_project()

        assert app_context.lifecycle.connection_factory is None
        assert app_context.lifecycle.engine is None
