"""Structured logging and basic OpenTelemetry setup for FLO.

This module provides a simple `setup_logging` helper which configures
`structlog` for structured (JSON) logs and a minimal OpenTelemetry
TracerProvider with a `ConsoleSpanExporter` for local development.

Call `setup_logging("my-service")` early in your application's
startup to enable structured logs with `trace_id`/`span_id` injected
when spans are active.
"""
from __future__ import annotations

from typing import Optional

import structlog
from structlog.processors import TimeStamper

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


__all__ = ["setup_logging", "get_logger"]


def _inject_otel_trace(_logger, _method_name, event_dict):
    """Processor that adds current OTel trace/span ids to the log event dict.

    Trace and span ids are hex-formatted strings when a valid span is active.
    """
    span = trace.get_current_span()
    if span is None:
        return event_dict

    ctx = span.get_span_context()
    if not ctx.is_valid:
        return event_dict

    event_dict.setdefault("trace_id", format(ctx.trace_id, "032x"))
    event_dict.setdefault("span_id", format(ctx.span_id, "016x"))
    return event_dict


def setup_logging(service_name: str = "flo") -> None:
    """Configure structlog and a simple OpenTelemetry TracerProvider.

    - Installs a `ConsoleSpanExporter` so spans print to stdout (development).
    - Configures `structlog` to emit JSON logs including `trace_id` and `span_id`.

    This function is intentionally idempotent and safe to call multiple times.
    """
    # Configure OTel tracer provider with a Console exporter for local use.
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = TracerProvider(resource=Resource.create({"service.name": service_name or "flo"}))
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    # Configure structlog for JSON output and include OTel ids when available.
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            TimeStamper(fmt="iso"),
            _inject_otel_trace,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None):
    """Return a structlog logger with an optional name."""
    return structlog.get_logger(name)
