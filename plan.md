# Plan: Structured Logging + OpenTelemetry Metrics

## Overview

Two complementary initiatives:
1. **Structured Logging** — Add thorough `debug`, `info`, and `error` logs across the codebase using Python's `logging` module with a centralized configuration
2. **OTEL Metrics** — Instrument with OpenTelemetry counters, histograms, and gauges for observability

The codebase already has OTEL tracing (spans + SQLAlchemy instrumentation) in `src/shared/infra/telemetry.py`. This plan extends it with **metrics** and adds **comprehensive logging**.

---

## Part 1: Centralized Logging Setup

### Step 1.1 — Create `src/shared/infra/logging_config.py`

Centralized logging configuration module:

```python
"""Centralized logging configuration for QualCoder v2."""
import logging
import sys
from pathlib import Path

def configure_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    enable_console: bool = True,
) -> None:
    """Configure root logger with consistent formatting."""
    root = logging.getLogger("qualcoder")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if enable_console:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        root.addHandler(console)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
```

All module loggers will use `logging.getLogger("qualcoder.<context>.<layer>")` naming:
- `qualcoder.coding.core` — coding domain logic
- `qualcoder.coding.infra` — coding repositories
- `qualcoder.sources.presentation` — sources UI
- `qualcoder.shared.event_bus` — event bus
- `qualcoder.shared.signal_bridge` — signal bridges
- `qualcoder.mcp` — MCP server (already exists)

### Step 1.2 — Call `configure_logging()` in `src/main.py`

Add before `init_telemetry()`:
```python
from src.shared.infra.logging_config import configure_logging
configure_logging(level="DEBUG" if os.environ.get("QUALCODER_DEV") else "INFO")
```

### Step 1.3 — Add logging to each layer

#### A. Core Layer (Command Handlers) — 14 files in coding + others

Each command handler gets `logger = logging.getLogger("qualcoder.<context>.core")` with:
- **DEBUG**: Input parameters, state snapshot size, derived event type
- **INFO**: Successful operation with entity ID
- **ERROR**: Failure events with error code

Example for `create_code.py`:
```python
logger = logging.getLogger("qualcoder.coding.core")

def create_code(...) -> OperationResult:
    logger.debug("create_code called: name=%s, color=%s", command.name, command.color)
    ...
    if isinstance(result, FailureEvent):
        logger.error("create_code failed: %s", result.error_code)
        ...
    logger.info("Code created: id=%s, name=%s", code.id.value, code.name)
    ...
```

Files to instrument:
- `src/contexts/coding/core/commandHandlers/` — all 13 handler files
- `src/contexts/cases/core/commandHandlers/` — all handler files
- `src/contexts/sources/core/commandHandlers/` — all handler files
- `src/contexts/projects/core/commandHandlers/` — all handler files
- `src/contexts/folders/core/commandHandlers/` — all handler files

#### B. Infrastructure Layer (Repositories)

Each repository gets `logger = logging.getLogger("qualcoder.<context>.infra")` with:
- **DEBUG**: SQL operation type, entity ID, row counts
- **ERROR**: Database exceptions

Files to instrument:
- `src/contexts/coding/infra/repositories.py`
- `src/contexts/sources/infra/repositories.py`
- `src/contexts/cases/infra/repositories.py`
- `src/contexts/folders/infra/repositories.py`
- `src/contexts/projects/infra/project_repository.py`
- `src/contexts/settings/infra/` repositories

#### C. Shared Infrastructure

- **EventBus** (`event_bus.py`): DEBUG on publish (event type, handler count), ERROR on handler exceptions (replace `warnings.warn` with `logger.error`)
- **SignalBridge** (`signal_bridge/base.py`): DEBUG on dispatch, WARN on conversion errors (replace `warnings.warn`)
- **Lifecycle** (`lifecycle.py`): INFO on open/close, ERROR on failures
- **MCP Server** (`mcp_server.py`): Already has logging — enhance with DEBUG for tool schema loading
- **Sync Engine** (`sync/engine.py`): Already has logging — verify coverage
- **Cascade Registry** (`cascade_registry.py`): Already has logging — verify coverage

#### D. Presentation Layer

- **ViewModels**: DEBUG on user actions (load, create, delete), INFO on state changes
- **Screens**: Replace `print()` statements (~30 occurrences) with proper logger calls

Files with `print()` to replace:
- `src/contexts/sources/presentation/screens/file_manager.py` (6 prints)
- `src/contexts/cases/presentation/screens/case_manager.py` (7 prints)
- `src/contexts/sources/presentation/pages/file_manager_page.py` (10 prints — demo `__main__` block, OK to keep)
- `src/contexts/coding/presentation/screens/text_coding.py` (6 prints)

#### E. Interface Layer (MCP Handlers)

- DEBUG on tool input args
- INFO on tool result (success/fail)
- ERROR on exceptions

---

## Part 2: OpenTelemetry Metrics Instrumentation

### Step 2.1 — Extend `src/shared/infra/telemetry.py`

Add `MeterProvider` initialization alongside existing `TracerProvider`:

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)

def init_telemetry(...):
    # ... existing tracing setup ...

    # Metrics setup
    metric_readers = []
    if _is_dev_mode():
        # Export metrics to console every 30s in dev mode
        console_reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=30_000,
        )
        metric_readers.append(console_reader)

    if log_file:
        file_reader = PeriodicExportingMetricReader(
            FileMetricExporter(log_file.with_suffix(".metrics.jsonl")),
            export_interval_millis=30_000,
        )
        metric_readers.append(file_reader)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
    )
    metrics.set_meter_provider(meter_provider)
```

Add `FileMetricExporter` class (similar pattern to existing `FileSpanExporter`).

Add helper function:
```python
def get_meter(name: str) -> metrics.Meter:
    """Get a meter for the given component name."""
    return metrics.get_meter(name)
```

### Step 2.2 — Command Handler Metrics

New file: `src/shared/infra/metrics.py` (shared metric instruments)

```python
"""Application-wide OTEL metric instruments."""
from opentelemetry import metrics

meter = metrics.get_meter("qualcoder")

# Command execution metrics
command_counter = meter.create_counter(
    "qualcoder.commands.total",
    description="Total command handler invocations",
)

command_duration = meter.create_histogram(
    "qualcoder.commands.duration_ms",
    unit="ms",
    description="Command handler execution duration",
)

command_failures = meter.create_counter(
    "qualcoder.commands.failures",
    description="Failed command handler invocations",
)
```

Add a `@metered_command` decorator:
```python
def metered_command(command_name: str):
    """Decorator to add metrics to command handlers."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                attrs = {"command": command_name}
                if hasattr(result, "is_success"):
                    attrs["success"] = str(result.is_success)
                    if not result.is_success:
                        command_failures.add(1, attrs)
                command_counter.add(1, attrs)
                return result
            except Exception:
                command_failures.add(1, {"command": command_name})
                command_counter.add(1, {"command": command_name, "success": "False"})
                raise
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                command_duration.record(elapsed, {"command": command_name})
        return wrapper
    return decorator
```

Apply to all command handler functions.

### Step 2.3 — Event Bus Metrics

In `event_bus.py`, add:

```python
from src.shared.infra.metrics import (
    events_published,
    event_handler_duration,
    event_handler_errors,
)
```

Metric instruments:
- `qualcoder.events.published` — Counter (attrs: event_type)
- `qualcoder.events.handler_duration_ms` — Histogram (attrs: event_type)
- `qualcoder.events.handler_errors` — Counter (attrs: event_type)

### Step 2.4 — Repository Metrics

Metric instruments:
- `qualcoder.db.operations` — Counter (attrs: operation=[get, save, delete, list], context, entity)
- `qualcoder.db.operation_duration_ms` — Histogram (attrs: same)

Add a `@metered_repo` decorator or instrument in the repository base pattern.

### Step 2.5 — MCP Server Metrics

Metric instruments (alongside existing `_stats` dict):
- `qualcoder.mcp.requests` — Counter (attrs: method, path)
- `qualcoder.mcp.tool_calls` — Counter (attrs: tool_name, success)
- `qualcoder.mcp.tool_duration_ms` — Histogram (attrs: tool_name)
- `qualcoder.mcp.errors` — Counter (attrs: tool_name)

### Step 2.6 — Signal Bridge Metrics

Metric instruments:
- `qualcoder.signals.emitted` — Counter (attrs: context, event_type)
- `qualcoder.signals.queue_depth` — Histogram (attrs: context)
- `qualcoder.signals.dispatch_errors` — Counter (attrs: context, event_type)

### Step 2.7 — Application Lifecycle Gauges

- `qualcoder.project.open` — UpDownCounter (1 on open, -1 on close)
- `qualcoder.contexts.active` — Gauge (number of active bounded contexts)
- `qualcoder.sync.pending_changes` — Gauge (pending sync changes)

---

## Part 3: Dependencies

### Add to `pyproject.toml`:
```toml
"opentelemetry-exporter-otlp-proto-grpc>=1.39.1",  # For production OTLP export
```

No other new dependencies needed — `opentelemetry-sdk` already includes `MeterProvider` and console exporters.

---

## Implementation Order

| Step | What | Files | Est. Lines |
|------|------|-------|-----------|
| 1 | `logging_config.py` + wire in `main.py` | 2 new/modified | ~40 |
| 2 | Extend `telemetry.py` with MeterProvider + FileMetricExporter | 1 modified | ~80 |
| 3 | Create `metrics.py` with shared instruments + decorators | 1 new | ~100 |
| 4 | Add logging to EventBus + metrics | 1 modified | ~30 |
| 5 | Add logging to SignalBridge base + metrics | 1 modified | ~25 |
| 6 | Add logging to Lifecycle | 1 modified | ~15 |
| 7 | Add logging + metrics to all command handlers (coding) | 13 modified | ~80 |
| 8 | Add logging + metrics to all command handlers (other contexts) | ~15 modified | ~80 |
| 9 | Add logging to repositories | ~8 modified | ~60 |
| 10 | Replace `print()` with logger in presentation layer | ~3 modified | ~30 |
| 11 | Add logging + metrics to MCP server | 1 modified | ~30 |
| 12 | Add OTEL metrics to `pyproject.toml` | 1 modified | ~2 |
| 13 | Run tests, fix any issues | — | — |
| 14 | Commit and push | — | — |

Total: ~35 files, ~570 lines of logging/metrics additions.

---

## Conventions

- Logger naming: `logging.getLogger("qualcoder.<context>.<layer>")`
- Metric naming: `qualcoder.<subsystem>.<metric_name>`
- Metric attributes: `command`, `event_type`, `context`, `entity`, `operation`, `success`
- No logging in hot loops (iteration over items) — only at operation boundaries
- No sensitive data in logs (no file contents, user text, SQL parameters with PII)
- Logging levels: DEBUG for developer trace, INFO for operations, WARNING for recoverable issues, ERROR for failures
