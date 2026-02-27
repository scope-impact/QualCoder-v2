"""
Application-wide OpenTelemetry metric instruments for QualCoder v2.

Provides shared counters, histograms, and a ``@metered_command`` decorator
that can be applied to any command handler function.

Usage:
    from src.shared.infra.metrics import metered_command

    @metered_command("create_code")
    def create_code(command, code_repo, event_bus) -> OperationResult:
        ...
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from src.shared.infra.telemetry import get_meter

P = ParamSpec("P")
R = TypeVar("R")

_meter = get_meter("qualcoder")

# ---------------------------------------------------------------------------
# Command handler metrics
# ---------------------------------------------------------------------------

command_total = _meter.create_counter(
    "qualcoder.commands.total",
    description="Total command handler invocations",
)

command_duration = _meter.create_histogram(
    "qualcoder.commands.duration_ms",
    unit="ms",
    description="Command handler execution duration",
)

command_failures = _meter.create_counter(
    "qualcoder.commands.failures",
    description="Failed command handler invocations",
)

# ---------------------------------------------------------------------------
# Event bus metrics
# ---------------------------------------------------------------------------

events_published = _meter.create_counter(
    "qualcoder.events.published",
    description="Total domain events published",
)

event_handler_duration = _meter.create_histogram(
    "qualcoder.events.handler_duration_ms",
    unit="ms",
    description="Time to execute all handlers for a single event",
)

event_handler_errors = _meter.create_counter(
    "qualcoder.events.handler_errors",
    description="Errors raised in event handlers",
)

# ---------------------------------------------------------------------------
# Signal bridge metrics
# ---------------------------------------------------------------------------

signals_emitted = _meter.create_counter(
    "qualcoder.signals.emitted",
    description="Qt signals emitted from event bus",
)

signal_dispatch_errors = _meter.create_counter(
    "qualcoder.signals.dispatch_errors",
    description="Errors during signal dispatch",
)

# ---------------------------------------------------------------------------
# Repository / DB metrics
# ---------------------------------------------------------------------------

db_operations = _meter.create_counter(
    "qualcoder.db.operations",
    description="Database operations executed",
)

db_operation_duration = _meter.create_histogram(
    "qualcoder.db.operation_duration_ms",
    unit="ms",
    description="Database operation duration",
)

# ---------------------------------------------------------------------------
# MCP server metrics
# ---------------------------------------------------------------------------

mcp_requests = _meter.create_counter(
    "qualcoder.mcp.requests",
    description="Total MCP HTTP requests",
)

mcp_tool_calls = _meter.create_counter(
    "qualcoder.mcp.tool_calls",
    description="Total MCP tool calls",
)

mcp_tool_duration = _meter.create_histogram(
    "qualcoder.mcp.tool_duration_ms",
    unit="ms",
    description="MCP tool execution duration",
)

mcp_errors = _meter.create_counter(
    "qualcoder.mcp.errors",
    description="MCP tool execution errors",
)

# ---------------------------------------------------------------------------
# Application lifecycle metrics
# ---------------------------------------------------------------------------

project_open = _meter.create_up_down_counter(
    "qualcoder.project.open",
    description="Number of currently open projects (1 or 0)",
)


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def metered_command(command_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that records command metrics (count, duration, failures).

    Example::

        @metered_command("create_code")
        def create_code(command, code_repo, event_bus) -> OperationResult:
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                attrs = {"command": command_name}
                if hasattr(result, "is_success") and not result.is_success:
                    command_failures.add(1, attrs)
                command_total.add(1, attrs)
                return result
            except Exception:
                command_failures.add(1, {"command": command_name})
                command_total.add(1, {"command": command_name})
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                command_duration.record(elapsed_ms, {"command": command_name})

        return wrapper

    return decorator
