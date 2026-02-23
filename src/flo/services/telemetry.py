from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

try:
    # OpenTelemetry SDK imports (optional but present in dev deps)
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    OTEL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    OTEL_AVAILABLE = False


@dataclass
class Telemetry:
    tracer: Optional[object]
    shutdown: Callable[[], None]


def init_telemetry(service_name: str = "flo", *, console_export: bool = True) -> Telemetry:
    """Initialize a minimal OpenTelemetry tracer for the CLI.

    This sets up a `TracerProvider` with a `ConsoleSpanExporter` by default
    so spans are visible on the console during development. Returns a
    `Telemetry` object with a `tracer` and a `shutdown()` function that
    should be called at process exit to flush any remaining spans.

    The implementation is deliberately small and safe to call even when
    OpenTelemetry packages are not available (it will return a no-op
    telemetry object).
    """
    if not OTEL_AVAILABLE:
        def _noop_shutdown() -> None:
            return None

        return Telemetry(tracer=None, shutdown=_noop_shutdown)

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if console_export:
        exporter = ConsoleSpanExporter()
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name)

    def _shutdown() -> None:
        try:
            provider.shutdown()
        except Exception:
            # Best-effort shutdown; do not raise during CLI exit
            pass

    return Telemetry(tracer=tracer, shutdown=_shutdown)
