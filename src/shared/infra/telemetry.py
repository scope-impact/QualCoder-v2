"""
OpenTelemetry instrumentation for QualCoder v2.

Provides automatic tracing for SQLAlchemy queries and manual tracing for key operations.

Usage:
    # Initialize once at startup
    from src.shared.infra.telemetry import init_telemetry
    init_telemetry()

    # Instrument SQLAlchemy engine (auto-traces all queries)
    from src.shared.infra.telemetry import instrument_sqlalchemy
    instrument_sqlalchemy(engine)

    # Manual tracing with decorator
    @traced("operation_name")
    def my_function():
        ...
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

if TYPE_CHECKING:
    from opentelemetry.trace import Span
    from sqlalchemy import Engine

# Type vars for decorator
P = ParamSpec("P")
R = TypeVar("R")

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

_initialized = False
_sqlalchemy_instrumented = False


def init_telemetry(service_name: str = "qualcoder", enable_console: bool = True) -> None:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for traces
        enable_console: Whether to export spans to console
    """
    global _initialized
    if _initialized:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if enable_console:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    _initialized = True


def instrument_sqlalchemy(engine: Engine) -> None:
    """
    Enable automatic tracing for all SQLAlchemy queries.

    Call this after creating the SQLAlchemy engine. All queries will be
    automatically traced with timing, SQL statement, and parameters.

    Args:
        engine: SQLAlchemy engine to instrument
    """
    global _sqlalchemy_instrumented
    if _sqlalchemy_instrumented:
        return

    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine)
    _sqlalchemy_instrumented = True


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given component name."""
    return trace.get_tracer(name)


# Default tracer for coding context
tracer = get_tracer("qualcoder.coding")


# -----------------------------------------------------------------------------
# Decorators
# -----------------------------------------------------------------------------


def traced(
    span_name: str | None = None,
    attributes: dict[str, str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to trace a function with OpenTelemetry.

    Args:
        span_name: Custom span name (defaults to function name)
        attributes: Static attributes to add to the span

    Example:
        @traced("load_segments")
        def load_segments_for_source(self, source_id: int):
            ...

        @traced(attributes={"layer": "repository"})
        def get_all(self):
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = span_name or func.__qualname__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                return func(*args, **kwargs)

        return wrapper

    return decorator


def traced_method(
    span_name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for tracing methods, automatically extracts common attributes.

    Example:
        @traced_method()
        def get_segments_for_source(self, source_id: int):
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = span_name or func.__qualname__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with tracer.start_as_current_span(name) as span:
                # Add method arguments as attributes (skip self)
                if args and len(args) > 1:
                    span.set_attribute("arg_count", len(args) - 1)
                if kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (int, str, float, bool)):
                            span.set_attribute(f"arg.{key}", value)
                return func(*args, **kwargs)

        return wrapper

    return decorator


# -----------------------------------------------------------------------------
# Context Managers
# -----------------------------------------------------------------------------


class SpanContext:
    """
    Context manager for manual span creation with timing.

    Example:
        with SpanContext("build_categories") as span:
            span.set_attribute("code_count", len(codes))
            # ... work
    """

    def __init__(self, name: str, attributes: dict | None = None) -> None:
        self.name = name
        self.attributes = attributes or {}
        self._span: Span | None = None
        self._token = None

    def __enter__(self) -> Span:
        self._span = tracer.start_span(self.name)
        self._token = trace.use_span(self._span, end_on_exit=True).__enter__()
        for key, value in self.attributes.items():
            self._span.set_attribute(key, value)
        return self._span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None and self._span:
            self._span.record_exception(exc_val)
            self._span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))
        if self._token:
            trace.use_span(self._span, end_on_exit=True).__exit__(exc_type, exc_val, exc_tb)


# Alias for convenience
span = SpanContext


# -----------------------------------------------------------------------------
# Query Counter (for detecting N+1)
# -----------------------------------------------------------------------------


class QueryCounter:
    """
    Tracks database query counts within a span to detect N+1 issues.

    Example:
        with QueryCounter("load_highlights") as counter:
            segments = repo.get_by_source(source_id)
            counter.increment()
            for seg in segments:
                code = repo.get_code(seg.code_id)  # N+1!
                counter.increment()
        # Logs warning if query_count > threshold
    """

    def __init__(self, name: str, threshold: int = 5) -> None:
        self.name = name
        self.threshold = threshold
        self.count = 0
        self._span: Span | None = None

    def increment(self, n: int = 1) -> None:
        self.count += n

    def __enter__(self) -> "QueryCounter":
        self._span = tracer.start_span(f"{self.name}.queries")
        trace.use_span(self._span, end_on_exit=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._span:
            self._span.set_attribute("query_count", self.count)
            self._span.set_attribute("threshold", self.threshold)
            if self.count > self.threshold:
                self._span.set_attribute("n_plus_one_warning", True)
                self._span.add_event(
                    "N+1 Query Warning",
                    {"query_count": self.count, "threshold": self.threshold},
                )
            self._span.end()
