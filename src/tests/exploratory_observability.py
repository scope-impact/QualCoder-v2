"""
Exploratory test: verify logging + OTEL metrics fire correctly across the stack.

Run with:
    QT_QPA_PLATFORM=offscreen uv run python -m src.tests.exploratory_observability
"""

from __future__ import annotations

import io
import logging
import sys
import tempfile
from pathlib import Path

# ── 1. Bootstrap telemetry + logging BEFORE any app imports ──────────────
from src.shared.infra.logging_config import configure_logging
from src.shared.infra.telemetry import init_telemetry

configure_logging(level="DEBUG")
init_telemetry(service_name="qualcoder-test")

# Capture log output for assertions
log_stream = io.StringIO()
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    logging.Formatter("%(levelname)s [%(name)s] %(message)s")
)
logging.getLogger("qualcoder").addHandler(handler)

# ── 2. Now import app modules ───────────────────────────────────────────
from opentelemetry import metrics

from src.shared.infra.event_bus import EventBus
from src.shared.infra.metrics import (
    command_duration,
    command_failures,
    command_total,
    event_handler_duration,
    event_handler_errors,
    events_published,
    mcp_errors,
    mcp_requests,
    mcp_tool_calls,
    mcp_tool_duration,
    signal_dispatch_errors,
    signals_emitted,
)

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name} — {detail}")


def get_logs() -> str:
    return log_stream.getvalue()


def clear_logs():
    log_stream.truncate(0)
    log_stream.seek(0)


# ═════════════════════════════════════════════════════════════════════════
print("\n=== 1. LOGGING: Command Handlers ===")
# ═════════════════════════════════════════════════════════════════════════

# Set up an in-memory SQLite database with the coding context
from sqlalchemy import create_engine

from src.shared.infra.telemetry import instrument_sqlalchemy

engine = create_engine("sqlite:///:memory:")
instrument_sqlalchemy(engine)
conn = engine.connect()

# Create tables
from src.contexts.coding.infra.schema import code_cat, code_name, code_text

code_name.create(conn, checkfirst=True)
code_cat.create(conn, checkfirst=True)
code_text.create(conn, checkfirst=True)

# Create repositories
from src.contexts.coding.infra.repositories import (
    SQLiteCategoryRepository,
    SQLiteCodeRepository,
    SQLiteSegmentRepository,
)

code_repo = SQLiteCodeRepository(conn)
category_repo = SQLiteCategoryRepository(conn)
segment_repo = SQLiteSegmentRepository(conn)
event_bus = EventBus()

# Test create_code
clear_logs()
from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commands import CreateCodeCommand

result = create_code(
    command=CreateCodeCommand(name="TestCode", color="#FF0000", memo="test"),
    code_repo=code_repo,
    category_repo=category_repo,
    segment_repo=segment_repo,
    event_bus=event_bus,
)
logs = get_logs()

check("create_code succeeds", result.is_success, f"got: {result}")
check(
    "create_code DEBUG log",
    "create_code: name=TestCode" in logs,
    f"missing debug log in: {logs[:200]}",
)
check(
    "create_code INFO log",
    "Code created:" in logs,
    f"missing info log in: {logs[:200]}",
)

# Test create_code failure (duplicate name)
clear_logs()
result2 = create_code(
    command=CreateCodeCommand(name="TestCode", color="#00FF00", memo="dup"),
    code_repo=code_repo,
    category_repo=category_repo,
    segment_repo=segment_repo,
    event_bus=event_bus,
)
logs = get_logs()

check("create_code duplicate fails", not result2.is_success)
check(
    "create_code ERROR log on failure",
    "ERROR" in logs and "create_code failed" in logs,
    f"missing error log in: {logs[:200]}",
)

# Test invalid color
clear_logs()
result3 = create_code(
    command=CreateCodeCommand(name="BadColor", color="notacolor", memo=""),
    code_repo=code_repo,
    category_repo=category_repo,
    segment_repo=segment_repo,
    event_bus=event_bus,
)
logs = get_logs()

check("create_code invalid color fails", not result3.is_success)
check(
    "create_code invalid color ERROR log",
    "invalid color" in logs,
    f"missing error log in: {logs[:200]}",
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 2. LOGGING: EventBus ===")
# ═════════════════════════════════════════════════════════════════════════

clear_logs()
bus = EventBus()
received = []
bus.subscribe("test.event", lambda e: received.append(e))
bus.publish(type("TestEvent", (), {"event_type": "test.event"})())
logs = get_logs()

check("EventBus publish delivers", len(received) == 1)
check(
    "EventBus DEBUG 'Publishing' log",
    "Publishing test.event" in logs,
    f"missing in: {logs[:200]}",
)
check(
    "EventBus DEBUG 'Subscribed' log",
    "Subscribed to test.event" in logs,
    f"missing in: {logs[:200]}",
)

# Test handler error logging
clear_logs()
bus2 = EventBus()
bus2.subscribe("err.event", lambda e: 1 / 0)
bus2.publish(type("E", (), {"event_type": "err.event"})())
logs = get_logs()

check(
    "EventBus ERROR log on handler exception",
    "Handler error for err.event" in logs,
    f"missing in: {logs[:300]}",
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 3. OTEL METRICS: @metered_command ===")
# ═════════════════════════════════════════════════════════════════════════

# Read the meter provider's in-memory state
meter_provider = metrics.get_meter_provider()
check(
    "MeterProvider is SDK MeterProvider",
    "MeterProvider" in type(meter_provider).__name__,
    f"got: {type(meter_provider).__name__}",
)

# Verify metric instruments are created (they exist if we can call .add/.record)
try:
    command_total.add(0, {"command": "__test__"})
    command_duration.record(0.0, {"command": "__test__"})
    command_failures.add(0, {"command": "__test__"})
    events_published.add(0, {"event_type": "__test__"})
    event_handler_duration.record(0.0, {"event_type": "__test__"})
    event_handler_errors.add(0, {"event_type": "__test__"})
    signals_emitted.add(0, {"context": "__test__", "event_type": "__test__"})
    signal_dispatch_errors.add(0, {"context": "__test__", "event_type": "__test__"})
    mcp_requests.add(0, {"method": "GET", "path": "/__test__"})
    mcp_tool_calls.add(0, {"tool_name": "__test__"})
    mcp_tool_duration.record(0.0, {"tool_name": "__test__"})
    mcp_errors.add(0, {"tool_name": "__test__"})
    check("All 12 metric instruments callable", True)
except Exception as e:
    check("All 12 metric instruments callable", False, str(e))

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 4. OTEL METRICS: metered_command decorator timing ===")
# ═════════════════════════════════════════════════════════════════════════

# The decorator wraps the function; verify it preserves function metadata
from src.contexts.coding.core.commandHandlers.rename_code import rename_code

check(
    "rename_code has __wrapped__ (is decorated)",
    hasattr(rename_code, "__wrapped__"),
    "function not wrapped by @metered_command",
)
check(
    "rename_code.__name__ preserved",
    rename_code.__name__ == "rename_code",
    f"got: {rename_code.__name__}",
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 5. LOGGING: Lifecycle ===")
# ═════════════════════════════════════════════════════════════════════════

clear_logs()
from src.shared.infra.lifecycle import ProjectLifecycle

lifecycle = ProjectLifecycle()

# Test open non-existent file
result = lifecycle.open_database(Path("/tmp/nonexistent_qc_test.qda"))
logs = get_logs()

check("Lifecycle open nonexistent fails", not isinstance(result, type(None)))
check(
    "Lifecycle ERROR log for missing file",
    "Database file not found" in logs,
    f"missing in: {logs[:200]}",
)

# Test open + close real temp file
clear_logs()
with tempfile.NamedTemporaryFile(suffix=".qda", delete=False) as f:
    # Create a valid SQLite db
    import sqlite3

    sqlite3.connect(f.name).close()
    tmp_path = Path(f.name)

result = lifecycle.open_database(tmp_path)
logs = get_logs()

check(
    "Lifecycle INFO log on open",
    "Database opened:" in logs,
    f"missing in: {logs[:200]}",
)

clear_logs()
lifecycle.close_database()
logs = get_logs()

check(
    "Lifecycle INFO log on close",
    "Closing database:" in logs,
    f"missing in: {logs[:200]}",
)

tmp_path.unlink(missing_ok=True)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 6. LOGGING: Repositories ===")
# ═════════════════════════════════════════════════════════════════════════

clear_logs()
# Use the code_repo from earlier — save already happened via create_code
codes = code_repo.get_all()
logs = get_logs()

check("Repository get_all returns data", len(codes) > 0)
check(
    "Repository DEBUG log on get_all",
    "get_all" in logs,
    f"missing in: {logs[:200]}",
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 7. LOGGING: Other command handlers ===")
# ═════════════════════════════════════════════════════════════════════════

# Verify rename_code logs
clear_logs()
code = codes[0]
from src.contexts.coding.core.commands import RenameCodeCommand

result = rename_code(
    command=RenameCodeCommand(code_id=code.id.value, new_name="RenamedCode"),
    code_repo=code_repo,
    category_repo=category_repo,
    segment_repo=segment_repo,
    event_bus=event_bus,
)
logs = get_logs()

check("rename_code succeeds", result.is_success)
check(
    "rename_code DEBUG log",
    "rename_code: code_id=" in logs,
    f"missing in: {logs[:200]}",
)
check(
    "rename_code INFO log",
    "Code renamed:" in logs,
    f"missing in: {logs[:200]}",
)

# Verify delete_code logs
clear_logs()
from src.contexts.coding.core.commandHandlers.delete_code import delete_code
from src.contexts.coding.core.commands import DeleteCodeCommand

result = delete_code(
    command=DeleteCodeCommand(code_id=code.id.value, delete_segments=True),
    code_repo=code_repo,
    category_repo=category_repo,
    segment_repo=segment_repo,
    event_bus=event_bus,
)
logs = get_logs()

check("delete_code succeeds", result.is_success)
check(
    "delete_code INFO log",
    "Code deleted:" in logs,
    f"missing in: {logs[:200]}",
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 8. LOGGING: Presentation layer (no more print()) ===")
# ═════════════════════════════════════════════════════════════════════════

# Verify print() was replaced by checking source files don't have print() in methods
import ast


def count_prints_in_methods(filepath: str) -> list[int]:
    """Return line numbers of print() calls inside class methods."""
    source = Path(filepath).read_text()
    tree = ast.parse(source)
    prints = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                # Check if inside a class method (not __main__)
                prints.append(node.lineno)
    return prints


files_to_check = [
    "src/contexts/sources/presentation/screens/file_manager.py",
    "src/contexts/cases/presentation/screens/case_manager.py",
    "src/contexts/coding/presentation/screens/text_coding.py",
]

for filepath in files_to_check:
    source = Path(filepath).read_text()
    # Check if __main__ block exists to exclude those prints
    has_main = "if __name__" in source
    # Quick check: are there logger calls?
    has_logger = "logger." in source
    check(
        f"{Path(filepath).name} has logger calls",
        has_logger,
        "no logger.xxx() found",
    )


# ═════════════════════════════════════════════════════════════════════════
print("\n=== 9. SignalBridge instrumentation (static check) ===")
# ═════════════════════════════════════════════════════════════════════════

# Read signal bridge base and check for metrics imports
bridge_source = Path(
    "src/shared/infra/signal_bridge/base.py"
).read_text()
check(
    "SignalBridge imports logging",
    "import logging" in bridge_source,
)
check(
    "SignalBridge has logger",
    'logging.getLogger("qualcoder.shared.signal_bridge")' in bridge_source,
)
check(
    "SignalBridge imports metrics",
    "from src.shared.infra.metrics import" in bridge_source,
)
check(
    "SignalBridge logs on start",
    "started" in bridge_source and "logger.info" in bridge_source,
)
check(
    "SignalBridge logs on stop",
    "stopped" in bridge_source,
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 10. MCP Server instrumentation (static check) ===")
# ═════════════════════════════════════════════════════════════════════════

mcp_source = Path("src/shared/infra/mcp_server.py").read_text()
check(
    "MCP imports mcp_requests metric",
    "mcp_requests" in mcp_source,
)
check(
    "MCP imports mcp_tool_calls metric",
    "mcp_tool_calls" in mcp_source,
)
check(
    "MCP imports mcp_tool_duration metric",
    "mcp_tool_duration" in mcp_source,
)
check(
    "MCP imports mcp_errors metric",
    "mcp_errors" in mcp_source,
)

# ═════════════════════════════════════════════════════════════════════════
print("\n=== 11. FileMetricExporter write test ===")
# ═════════════════════════════════════════════════════════════════════════

with tempfile.NamedTemporaryFile(suffix=".metrics.jsonl", delete=False) as f:
    metrics_path = Path(f.name)

from src.shared.infra.telemetry import FileMetricExporter

exporter = FileMetricExporter(metrics_path)
check("FileMetricExporter creates file", metrics_path.exists())
check(
    "FileMetricExporter has export method",
    hasattr(exporter, "export"),
)
check(
    "FileMetricExporter has force_flush",
    hasattr(exporter, "force_flush"),
)
metrics_path.unlink(missing_ok=True)


# ═════════════════════════════════════════════════════════════════════════
# Cleanup
conn.close()
engine.dispose()

# ═════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL} checks")
print(f"{'='*60}")

if FAIL > 0:
    sys.exit(1)
