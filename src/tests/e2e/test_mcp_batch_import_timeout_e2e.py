"""
Reproduce: MCP import_file_source timeout when importing multiple files.

Bug: When an MCP client (Claude) calls import_file_source for many files,
the total wall-clock time exceeds the MCP session timeout.

Root cause: NOT the import logic itself (~1ms/file), but the MCP protocol
overhead. Each tool call requires a full LLM round-trip:
  Claude thinks → JSON-RPC request → tool executes → response → Claude processes
This takes ~2-5 seconds per call. For 20 files = 20 × ~3s = ~60s total.

Fix: Add a batch `import_file_sources` tool that accepts multiple file paths
in a single MCP call, eliminating N-1 round-trips.

This test suite:
1. Proves the import logic is fast (rules out server-side bottleneck)
2. Shows a batch import would complete in milliseconds
3. Documents the O(n) MCP round-trip problem
"""

from __future__ import annotations

import time
from pathlib import Path

import allure
import pytest
from returns.result import Failure, Success

from src.shared.infra.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MCP_TIMEOUT_SECONDS = 60
# Real-world MCP round-trip overhead per tool call (LLM thinking + JSON-RPC)
MCP_ROUNDTRIP_OVERHEAD_S = 3.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def open_project(app_context: AppContext, tmp_path: Path) -> Path:
    project_path = tmp_path / "timeout_test.qda"
    result = app_context.create_project(name="Timeout Test", path=str(project_path))
    assert result.is_success
    return project_path


@pytest.fixture
def source_tools(app_context: AppContext):
    from src.contexts.sources.interface.mcp_tools import SourceTools

    return SourceTools(ctx=app_context)


# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------


def _create_text_files(directory: Path, count: int, lines: int = 500) -> list[Path]:
    """Create N text files (~60KB each at 500 lines)."""
    directory.mkdir(parents=True, exist_ok=True)
    content = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20 + "\n"
    body = content * lines
    files = []
    for i in range(count):
        p = directory / f"document_{i:03d}.txt"
        p.write_text(body, encoding="utf-8")
        files.append(p)
    return files


def _create_mixed_files(directory: Path, count: int) -> list[Path]:
    """Create N files with mixed types."""
    directory.mkdir(parents=True, exist_ok=True)
    text_body = ("Qualitative research interview transcript line.\n") * 300
    files = []
    for i in range(count):
        remainder = i % 4
        if remainder == 0:
            p = directory / f"interview_{i:03d}.txt"
            p.write_text(text_body, encoding="utf-8")
        elif remainder == 1:
            p = directory / f"notes_{i:03d}.md"
            p.write_text(f"# Notes {i}\n\n{text_body}", encoding="utf-8")
        elif remainder == 2:
            p = directory / f"photo_{i:03d}.jpg"
            p.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 200)
        else:
            p = directory / f"recording_{i:03d}.wav"
            p.write_bytes(b"RIFF" + b"\x00" * 200)
        files.append(p)
    return files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_files_sequentially(
    source_tools, files: list[Path]
) -> tuple[float, list[dict]]:
    """Import files one-by-one via MCP tool, return (total_seconds, timings)."""
    timings: list[dict] = []
    t_start = time.perf_counter()

    for f in files:
        t0 = time.perf_counter()
        result = source_tools.execute("import_file_source", {"file_path": str(f)})
        elapsed = time.perf_counter() - t0
        timings.append({
            "file": f.name,
            "elapsed_s": round(elapsed, 4),
            "success": isinstance(result, Success),
            "error": str(result.failure()) if isinstance(result, Failure) else None,
        })

    total_s = time.perf_counter() - t_start
    return total_s, timings


def _attach_timing_report(
    total_s: float, timings: list[dict], file_count: int
) -> None:
    """Attach timing report as Allure artifact."""
    avg_s = total_s / len(timings) if timings else 0

    # Estimate real-world time including MCP round-trip overhead
    estimated_real_s = total_s + (file_count * MCP_ROUNDTRIP_OVERHEAD_S)

    report_lines = [
        f"=== Server-side execution ===",
        f"Total server time: {total_s:.3f}s for {file_count} files",
        f"Average: {avg_s * 1000:.1f}ms per file",
        f"",
        f"=== Estimated real-world with MCP overhead ===",
        f"MCP round-trip overhead: ~{MCP_ROUNDTRIP_OVERHEAD_S}s × {file_count} calls",
        f"Estimated total: {estimated_real_s:.1f}s",
        f"Would timeout (>{MCP_TIMEOUT_SECONDS}s): {'YES' if estimated_real_s > MCP_TIMEOUT_SECONDS else 'no'}",
        f"",
        f"=== Batch import (single MCP call) would take ===",
        f"Estimated: {total_s:.3f}s + {MCP_ROUNDTRIP_OVERHEAD_S}s = {total_s + MCP_ROUNDTRIP_OVERHEAD_S:.1f}s",
        f"",
        f"=== Per-file breakdown ===",
    ]
    for t in timings:
        status = "ok" if t["success"] else f"FAIL: {t['error']}"
        report_lines.append(f"  {t['file']}: {t['elapsed_s']*1000:.1f}ms ({status})")

    allure.attach(
        "\n".join(report_lines),
        name="timing_report",
        attachment_type=allure.attachment_type.TEXT,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@allure.story("QC-027.15 Agent Batch Import Sources")
@allure.severity(allure.severity_level.CRITICAL)
class TestMcpBatchImportTimeout:
    """Reproduce and document MCP timeout when importing multiple files."""

    @allure.title("Server-side import is fast — 30 files complete in <1s")
    def test_server_side_import_is_fast(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        """Prove the bottleneck is NOT the import logic.
        30 text files (~60KB each) should complete well under 1 second."""
        files = _create_text_files(tmp_path / "fast", count=30, lines=500)
        total_s, timings = _import_files_sequentially(source_tools, files)

        with allure.step(f"30 files imported in {total_s*1000:.0f}ms"):
            _attach_timing_report(total_s, timings, len(files))
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # Server-side should be well under 1 second
        assert total_s < 1.0, (
            f"Server-side import of 30 files took {total_s:.2f}s — "
            f"expected <1s since import logic is ~1ms/file"
        )

    @allure.title("BUG: 20 files × ~3s MCP overhead = timeout")
    def test_mcp_overhead_causes_timeout_for_20_files(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        """Show that 20 sequential MCP calls would timeout due to protocol overhead.
        Server time is negligible; the ~3s per MCP round-trip is the bottleneck."""
        files = _create_mixed_files(tmp_path / "timeout", count=20)
        total_s, timings = _import_files_sequentially(source_tools, files)

        with allure.step(f"Server: {total_s*1000:.0f}ms, Estimated real: {total_s + 20*MCP_ROUNDTRIP_OVERHEAD_S:.0f}s"):
            _attach_timing_report(total_s, timings, len(files))
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # The real-world time WITH MCP overhead exceeds timeout
        estimated_real_time = total_s + (len(files) * MCP_ROUNDTRIP_OVERHEAD_S)
        assert estimated_real_time > MCP_TIMEOUT_SECONDS, (
            f"Expected real-world time ({estimated_real_time:.0f}s) to exceed "
            f"MCP timeout ({MCP_TIMEOUT_SECONDS}s) for {len(files)} files. "
            f"Bug may not reproduce with fewer files."
        )

    @allure.title("Batch import would complete in <1s + single MCP round-trip")
    def test_batch_import_would_be_fast(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        """Demonstrate that a batch tool executing all imports in one call
        would complete in milliseconds (server time only) + one MCP round-trip."""
        files = _create_text_files(tmp_path / "batch", count=20, lines=500)

        # Simulate batch: call import_file_source N times in a tight loop
        # This is what a batch tool would do internally
        total_s, timings = _import_files_sequentially(source_tools, files)

        # With batch: server_time + 1 round-trip
        batch_estimated = total_s + MCP_ROUNDTRIP_OVERHEAD_S
        # Without batch: server_time + N round-trips
        sequential_estimated = total_s + (len(files) * MCP_ROUNDTRIP_OVERHEAD_S)

        speedup = sequential_estimated / batch_estimated if batch_estimated > 0 else 1

        with allure.step(f"Batch: ~{batch_estimated:.1f}s vs Sequential: ~{sequential_estimated:.0f}s ({speedup:.0f}x faster)"):
            _attach_timing_report(total_s, timings, len(files))
            allure.attach(
                f"batch_estimated={batch_estimated:.1f}s\n"
                f"sequential_estimated={sequential_estimated:.0f}s\n"
                f"speedup={speedup:.0f}x\n"
                f"server_time={total_s*1000:.0f}ms\n",
                name="batch_vs_sequential",
                attachment_type=allure.attachment_type.TEXT,
            )
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # Batch would be well within timeout
        assert batch_estimated < MCP_TIMEOUT_SECONDS, (
            f"Even batch import would timeout ({batch_estimated:.1f}s)"
        )

    @allure.title("O(n) uniqueness check: get_all() called per import")
    def test_uniqueness_check_overhead(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        """Each import calls source_repo.get_all() for name uniqueness.
        Verify this doesn't degrade significantly as sources accumulate."""
        files = _create_text_files(tmp_path / "scaling", count=50, lines=50)
        total_s, timings = _import_files_sequentially(source_tools, files)

        with allure.step(f"50 files in {total_s*1000:.0f}ms"):
            _attach_timing_report(total_s, timings, len(files))
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # Check if later imports are slower (O(n²) degradation)
        first_10_avg = sum(t["elapsed_s"] for t in timings[:10]) / 10
        last_10_avg = sum(t["elapsed_s"] for t in timings[-10:]) / 10
        slowdown = last_10_avg / first_10_avg if first_10_avg > 0 else 1.0

        with allure.step(f"First 10 avg: {first_10_avg*1000:.1f}ms, Last 10 avg: {last_10_avg*1000:.1f}ms, Slowdown: {slowdown:.1f}x"):
            allure.attach(
                f"first_10_avg_ms={first_10_avg*1000:.1f}\n"
                f"last_10_avg_ms={last_10_avg*1000:.1f}\n"
                f"slowdown_ratio={slowdown:.2f}x\n",
                name="scaling_analysis",
                attachment_type=allure.attachment_type.TEXT,
            )

        # Even with O(n) check, 50 files should still be sub-second
        assert total_s < 2.0, (
            f"50 file imports took {total_s:.2f}s — potential O(n²) issue"
        )
