"""Telemetry helpers and a minimal `Telemetry` wrapper for FLO.

OpenTelemetry is optional; when not available a no-op `Telemetry` is
returned so callers can always call `shutdown()` safely.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Optional

try:
    # Optional OpenTelemetry SDK imports
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    OTEL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    trace = None  # type: ignore
    Resource = None  # type: ignore
    SDKTracerProvider = None  # type: ignore
    BatchSpanProcessor = None  # type: ignore
    ConsoleSpanExporter = None  # type: ignore
    OTEL_AVAILABLE = False


class _NoOpSpan:
    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None


class _NoOpTracer:
    @contextmanager
    def start_as_current_span(self, name: str, **_: Any):
        yield _NoOpSpan()


# module-level provider state
_provider: Optional[object] = None


@dataclass
class Telemetry:
    """Container for a tracer and a shutdown callable.

    `tracer` may be `None` when OpenTelemetry SDK isn't available.
    """

    tracer: Optional[object]
    shutdown: Callable[[], None]


def init_telemetry(service_name: str = "flo", *, console_export: bool = True) -> Telemetry:
    """Initialize a minimal OpenTelemetry tracer for the CLI.

    Returns a `Telemetry` object with a `tracer` and a `shutdown()` function
    that should be called at process exit to flush any remaining spans.
    When OpenTelemetry packages are not available this returns a no-op
    telemetry object where `tracer` is `None` and `shutdown()` is a noop.
    """
    global _provider
    if not OTEL_AVAILABLE:
        return Telemetry(tracer=None, shutdown=lambda: None)

    if _provider is None:
        resource = Resource.create({"service.name": service_name})
        provider = SDKTracerProvider(resource=resource)

        if console_export and ConsoleSpanExporter is not None and BatchSpanProcessor is not None:
            try:
                exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception:
                pass

        trace.set_tracer_provider(provider)
        _provider = provider

    tracer = trace.get_tracer(service_name) if trace is not None else None

    def _shutdown() -> None:
        global _provider
        if _provider is None:
            return
        try:
            # Prefer provider.shutdown() when available
            try:
                _provider.shutdown()
                return
            except Exception:
                pass

            # Best-effort: attempt to shut down attached span processors
            span_processors = getattr(_provider, "span_processors", None) or getattr(_provider, "_active_span_processors", None)
            if span_processors:
                for sp in list(span_processors):
                    try:
                        sp.shutdown()
                    except Exception:
                        pass
        finally:
            _provider = None

    return Telemetry(tracer=tracer, shutdown=_shutdown)


def get_tracer(name: str):
    """Return an OpenTelemetry tracer or a no-op tracer when OTEL missing."""
    if OTEL_AVAILABLE and trace is not None:
        return trace.get_tracer(name)
    return _NoOpTracer()


def shutdown() -> None:
    """Convenience helper to shut down the configured provider (if any)."""
    global _provider
    if _provider is None:
        return
    try:
        _provider.shutdown()
    except Exception:
        span_processors = getattr(_provider, "span_processors", None) or getattr(_provider, "_active_span_processors", None)
        if span_processors:
            for sp in list(span_processors):
                try:
                    sp.shutdown()
                except Exception:
                    pass
    finally:
        _provider = None
