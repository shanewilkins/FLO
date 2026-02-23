import importlib
import sys
import types


def test_init_telemetry_with_fake_otel(monkeypatch):
    # Create fake opentelemetry package structure
    fake_trace = types.SimpleNamespace()

    class FakeTracer:
        pass

    def get_tracer(name):
        return FakeTracer()

    def set_tracer_provider(provider):
        fake_trace._provider = provider

    fake_trace.get_tracer = get_tracer
    fake_trace.set_tracer_provider = set_tracer_provider

    sdk_resources = types.SimpleNamespace()

    class Resource:
        @staticmethod
        def create(d):
            return d

    sdk_resources.Resource = Resource

    sdk_trace = types.SimpleNamespace()

    class TracerProvider:
        def __init__(self, resource=None):
            self._processors = []

        def add_span_processor(self, sp):
            self._processors.append(sp)

        def shutdown(self):
            # simulate clean shutdown
            for sp in list(self._processors):
                try:
                    sp.shutdown()
                except Exception:
                    pass

    sdk_trace.TracerProvider = TracerProvider

    sdk_trace.export = types.SimpleNamespace()

    class BatchSpanProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

        def shutdown(self):
            return None

    class ConsoleSpanExporter:
        pass

    sdk_trace.export.BatchSpanProcessor = BatchSpanProcessor
    sdk_trace.export.ConsoleSpanExporter = ConsoleSpanExporter

    # Install fake modules
    sys.modules["opentelemetry"] = types.ModuleType("opentelemetry")
    sys.modules["opentelemetry"].trace = fake_trace
    sys.modules["opentelemetry.sdk"] = types.ModuleType("opentelemetry.sdk")
    sys.modules["opentelemetry.sdk.resources"] = types.ModuleType("opentelemetry.sdk.resources")
    sys.modules["opentelemetry.sdk.resources"].Resource = Resource
    sys.modules["opentelemetry.sdk.trace"] = types.ModuleType("opentelemetry.sdk.trace")
    sys.modules["opentelemetry.sdk.trace"].TracerProvider = TracerProvider
    sys.modules["opentelemetry.sdk.trace.export"] = types.ModuleType("opentelemetry.sdk.trace.export")
    sys.modules["opentelemetry.sdk.trace.export"].BatchSpanProcessor = BatchSpanProcessor
    sys.modules["opentelemetry.sdk.trace.export"].ConsoleSpanExporter = ConsoleSpanExporter

    # Reload telemetry module to pick up fake opentelemetry
    import flo.services.telemetry as tel
    importlib.reload(tel)

    t = tel.init_telemetry(service_name="flo-test", console_export=True)
    assert hasattr(t, "shutdown")
    # tracer should be provided (FakeTracer)
    assert t.tracer is not None
    # call shutdown to exercise code paths
    t.shutdown()

    # cleanup: remove fake modules and reload telemetry to original state
    for m in [
        "opentelemetry",
        "opentelemetry.sdk",
        "opentelemetry.sdk.resources",
        "opentelemetry.sdk.trace",
        "opentelemetry.sdk.trace.export",
    ]:
        sys.modules.pop(m, None)
    importlib.reload(tel)
