"""Logging configuration helpers for the FLO CLI.

This module configures `structlog` for CLI use and injects OpenTelemetry
trace/span identifiers into each log event when OTEL is available. The
configuration is defensive and safe when OTEL isn't installed.
"""

import logging
from typing import Optional

import structlog


def _add_otel_trace_info(logger, method_name: str, event_dict: dict) -> dict:
    """Structlog processor that adds OpenTelemetry trace/span ids when present.

    Returns the (possibly) enriched `event_dict`.  This processor is defensive
    and is a no-op when OpenTelemetry is not installed or no active span is
    available.
    """
    try:
        from opentelemetry.trace import get_current_span

        span = get_current_span()
        if span is not None:
            sc = span.get_span_context()
            # trace_id/ span_id may be 0 when invalid; only add when present
            if getattr(sc, "trace_id", 0):
                # format as hex to match common log conventions
                event_dict.setdefault("trace_id", hex(sc.trace_id))
            if getattr(sc, "span_id", 0):
                event_dict.setdefault("span_id", hex(sc.span_id))
    except Exception:
        # OTEL not available or some error retrieving span -> no-op
        pass
    return event_dict


def _add_service_name(name: Optional[str]):
    def _processor(logger, method_name: str, event_dict: dict) -> dict:
        if name:
            event_dict.setdefault("service", name)
        return event_dict

    return _processor


def configure_logging(level: int = logging.INFO, service_name: Optional[str] = None) -> None:
    """Configure structlog + stdlib logging for CLI usage.

    Idempotent and safe to call multiple times; uses a simple, readable
    processor chain suitable for CLI output (logs go to stderr).

    Args:
        level: stdlib log level (e.g., `logging.INFO`).
        service_name: optional service name to include on every log event.
    """
    # Avoid reconfiguring if handlers already present
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(handler)
    root.setLevel(level)

    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.contextvars.merge_contextvars,
        _add_service_name(service_name),
        _add_otel_trace_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.KeyValueRenderer(key_order=["event", "message"]),
    ]

    structlog.configure(  # pyright: ignore[reportArgumentType]
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
