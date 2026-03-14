"""
Reproduce: MCP import_file_source hangs on second call with DOCX files.

Bug report: First import_file_source succeeds, but the next call hangs
until the MCP client times out. Files are small DOCX (<100KB).

Investigation findings:
- The import logic itself is fast (~1ms for txt, ~50ms for docx)
- The entire call chain is synchronous on the qasync event loop main thread:
    MCP HTTP handler → _execute_tool() → import_file_source()
    → text extraction → DB save → event_bus.publish(SourceAdded)
    → signal bridge emit → UI slot (_load_data) → DB query
- After the first import, signal.emit(SourceAdded) triggers synchronous
  UI updates on the main thread. If the UI slot blocks or enters a
  nested event loop, the next HTTP request can't be processed.

Possible root causes:
1. Signal.emit() on main thread triggers heavy UI rebuild between requests
2. qasync event loop starvation: synchronous tool call blocks async HTTP
3. Qt signal delivery timing: signal emitted during sync code may
   defer delivery until next event loop tick, which never comes because
   the next HTTP request arrives first and blocks again
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


def _create_docx_files(directory: Path, count: int, paragraphs: int = 10) -> list[Path]:
    """Create N small DOCX files (<100KB each)."""
    from docx import Document

    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(count):
        doc = Document()
        for j in range(paragraphs):
            doc.add_paragraph(
                f"Interview transcript paragraph {j} of document {i}. "
                "The participant discussed their experience with the process "
                "and shared insights about the methodology used in the study."
            )
        p = directory / f"interview_{i:03d}.docx"
        doc.save(str(p))
        files.append(p)
    return files


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
        timings.append(
            {
                "file": f.name,
                "elapsed_s": round(elapsed, 4),
                "success": isinstance(result, Success),
                "error": str(result.failure()) if isinstance(result, Failure) else None,
            }
        )

    total_s = time.perf_counter() - t_start
    return total_s, timings


def _attach_timing_report(total_s: float, timings: list[dict]) -> None:
    """Attach timing report as Allure artifact."""
    file_count = len(timings)
    avg_s = total_s / file_count if timings else 0
    max_s = max(t["elapsed_s"] for t in timings) if timings else 0

    report_lines = [
        f"Total: {total_s:.3f}s for {file_count} files",
        f"Average: {avg_s * 1000:.1f}ms per file",
        f"Max: {max_s * 1000:.1f}ms single file",
        "",
        "Per-file breakdown:",
    ]
    for t in timings:
        status = "ok" if t["success"] else f"FAIL: {t['error']}"
        report_lines.append(f"  {t['file']}: {t['elapsed_s'] * 1000:.1f}ms ({status})")

    allure.attach(
        "\n".join(report_lines),
        name="timing_report",
        attachment_type=allure.attachment_type.TEXT,
    )


# ---------------------------------------------------------------------------
# Tests: Bug reproduction
# ---------------------------------------------------------------------------


@allure.story("QC-027.15 Agent Import File Source")
@allure.severity(allure.severity_level.CRITICAL)
class TestMcpImportDocxHangs:
    """Reproduce: first DOCX import succeeds, second call hangs."""

    @allure.title(
        "BUG REPRO: sequential DOCX imports via MCP — second call should not hang"
    )
    def test_sequential_docx_imports_do_not_hang(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        """Import 5 small DOCX files sequentially.
        Bug: the second call hangs after the first succeeds.
        This test will timeout if the bug is present."""
        files = _create_docx_files(tmp_path / "docx", count=5, paragraphs=10)

        total_s, timings = _import_files_sequentially(source_tools, files)

        with allure.step(f"5 DOCX files in {total_s:.2f}s"):
            _attach_timing_report(total_s, timings)
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # Each DOCX import should complete in under 5s
        for t in timings:
            assert t["elapsed_s"] < 5.0, (
                f"{t['file']} took {t['elapsed_s']:.1f}s — potential hang"
            )

    @allure.title(
        "BUG REPRO: DOCX import via MCP server and signal bridge (full production path)"
    )
    def test_docx_import_via_mcp_server_with_signal_bridge(
        self, app_context: AppContext, tmp_path: Path
    ):
        """Test the full MCP HTTP server path with DOCX files and signal bridge.
        Combines MCP server _execute_tool() entry point with ProjectSignalBridge
        connected — closest to real production setup where SourceAdded events
        trigger UI updates."""
        from src.shared.infra.mcp_server import MCPServerManager
        from src.shared.infra.signal_bridge.projects import ProjectSignalBridge

        # Setup project
        project_path = tmp_path / "mcp_bridge_test.qda"
        result = app_context.create_project(
            name="MCP Bridge Test", path=str(project_path)
        )
        assert result.is_success

        # Connect signal bridge (as main.py does)
        ProjectSignalBridge.clear_instance()
        bridge = ProjectSignalBridge.instance(app_context.event_bus)
        bridge.start()

        signal_count = {"source_added": 0}

        def _on_source_added(_payload):
            signal_count["source_added"] += 1

        bridge.source_added.connect(_on_source_added)

        try:
            server = MCPServerManager(ctx=app_context, debug=False)

            # Create DOCX files
            files = _create_docx_files(tmp_path / "mcp_docx", count=5, paragraphs=10)

            with allure.step("Import 5 DOCX files via MCP server _execute_tool()"):
                timings: list[dict] = []
                for f in files:
                    t0 = time.perf_counter()
                    result = server._execute_tool(
                        "import_file_source",
                        {"file_path": str(f)},
                    )
                    elapsed = time.perf_counter() - t0
                    success = result.get("success", False)
                    timings.append(
                        {
                            "file": f.name,
                            "elapsed_s": round(elapsed, 4),
                            "success": success,
                            "error": result.get("error") if not success else None,
                        }
                    )

                total_s = sum(t["elapsed_s"] for t in timings)

            with allure.step(f"5 DOCX via MCP server in {total_s:.2f}s"):
                _attach_timing_report(total_s, timings)
                for t in timings:
                    assert t["success"], f"Failed: {t['file']}: {t['error']}"
                    assert t["elapsed_s"] < 5.0, (
                        f"{t['file']} took {t['elapsed_s']:.1f}s — potential hang"
                    )

            with allure.step(
                f"Signal bridge emitted {signal_count['source_added']} source_added events"
            ):
                assert signal_count["source_added"] == 5, (
                    f"Expected 5 source_added signals, got {signal_count['source_added']}"
                )
        finally:
            ProjectSignalBridge.clear_instance()


# ---------------------------------------------------------------------------
# Tests: Batch import performance baseline
# ---------------------------------------------------------------------------


@allure.story("QC-027.15 Agent Import File Source")
@allure.severity(allure.severity_level.NORMAL)
class TestBatchImportBaseline:
    """Performance baseline for batch import optimization."""

    @allure.title("Batch import performance: text files fast, DOCX reasonable overhead")
    def test_text_and_docx_import_performance(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        with allure.step("Import 30 text files — should complete in <1s"):
            txt_files = _create_text_files(tmp_path / "fast", count=30, lines=500)
            txt_total_s, txt_timings = _import_files_sequentially(
                source_tools, txt_files
            )
            _attach_timing_report(txt_total_s, txt_timings)
            for t in txt_timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"
            assert txt_total_s < 1.0, (
                f"30 text file imports took {txt_total_s:.2f}s — expected <1s"
            )

        with allure.step("Import 10 DOCX files — should complete in <10s"):
            docx_files = _create_docx_files(
                tmp_path / "docx_perf", count=10, paragraphs=20
            )
            docx_total_s, docx_timings = _import_files_sequentially(
                source_tools, docx_files
            )
            _attach_timing_report(docx_total_s, docx_timings)
            for t in docx_timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"
            assert docx_total_s < 10.0, (
                f"10 DOCX imports took {docx_total_s:.2f}s — too slow"
            )

    @allure.title("O(n) uniqueness check: get_all() called per import")
    def test_uniqueness_check_overhead(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        files = _create_text_files(tmp_path / "scaling", count=50, lines=50)
        total_s, timings = _import_files_sequentially(source_tools, files)

        with allure.step(f"50 files in {total_s * 1000:.0f}ms"):
            _attach_timing_report(total_s, timings)
            for t in timings:
                assert t["success"], f"Failed: {t['file']}: {t['error']}"

        # Check if later imports are slower (O(n²) degradation)
        first_10_avg = sum(t["elapsed_s"] for t in timings[:10]) / 10
        last_10_avg = sum(t["elapsed_s"] for t in timings[-10:]) / 10
        slowdown = last_10_avg / first_10_avg if first_10_avg > 0 else 1.0

        with allure.step(f"Slowdown: {slowdown:.1f}x (first 10 vs last 10)"):
            allure.attach(
                f"first_10_avg_ms={first_10_avg * 1000:.1f}\n"
                f"last_10_avg_ms={last_10_avg * 1000:.1f}\n"
                f"slowdown_ratio={slowdown:.2f}x\n",
                name="scaling_analysis",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert total_s < 2.0, (
            f"50 file imports took {total_s:.2f}s — potential O(n²) issue"
        )
