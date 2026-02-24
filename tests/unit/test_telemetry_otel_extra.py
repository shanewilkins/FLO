import types
from flo.services import telemetry as tel
from flo.services.telemetry import init_telemetry, get_tracer, shutdown


def make_dummy_trace():
    class DummyTracer:
        def __init__(self, name):
            self.name = name

        class Span:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        def start_as_current_span(self, name: str, **_):
            return DummyTracer.Span()

    def get_tracer(name: str):
        return DummyTracer(name)

    def set_tracer_provider(p):
        # record provider for assertions
        tel._provider = p

    return types.SimpleNamespace(get_tracer=get_tracer, set_tracer_provider=set_tracer_provider)


class DummyProvider:
    def __init__(self, resource=None):
        self.resource = resource
        self.span_processors = []

    def add_span_processor(self, sp):
        self.span_processors.append(sp)

    def shutdown(self):
        # set a flag to indicate shutdown was called
        self._shutdown_called = True


class DummySpanProcessor:
    def __init__(self):
        self._shutdown_called = False

    def shutdown(self):
        self._shutdown_called = True


def test_init_telemetry_with_otel(monkeypatch):
    # Simulate OTEL available with ConsoleSpanExporter and BatchSpanProcessor
    monkeypatch.setattr(tel, "OTEL_AVAILABLE", True)
    dummy_trace = make_dummy_trace()
    monkeypatch.setattr(tel, "trace", dummy_trace)

    monkeypatch.setattr(tel, "Resource", types.SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(tel, "SDKTracerProvider", DummyProvider)
    monkeypatch.setattr(tel, "ConsoleSpanExporter", lambda: object())
    monkeypatch.setattr(tel, "BatchSpanProcessor", lambda exporter: DummySpanProcessor())

    # ensure provider cleared
    monkeypatch.setattr(tel, "_provider", None)

    t = init_telemetry("flo-test", console_export=True)
    assert t.tracer is not None
    # tracer should support start_as_current_span
    tracer = get_tracer("x")
    with tracer.start_as_current_span("y"):
        pass

    # shutdown should be callable and not raise
    prov = tel._provider
    t.shutdown()
    assert getattr(prov, "_shutdown_called", False) is True


def test_shutdown_fallback_to_span_processors(monkeypatch):
    # Simulate OTEL available but provider without shutdown method
    monkeypatch.setattr(tel, "OTEL_AVAILABLE", True)
    dummy_trace = make_dummy_trace()
    monkeypatch.setattr(tel, "trace", dummy_trace)

    class ProviderNoShutdown:
        def __init__(self, resource=None):
            self._active_span_processors = [DummySpanProcessor()]

    monkeypatch.setattr(tel, "Resource", types.SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(tel, "SDKTracerProvider", ProviderNoShutdown)
    monkeypatch.setattr(tel, "ConsoleSpanExporter", None)
    monkeypatch.setattr(tel, "BatchSpanProcessor", None)

    # clear provider and init
    monkeypatch.setattr(tel, "_provider", None)
    t = init_telemetry("flo-test", console_export=False)
    assert t.tracer is not None
    # manually call module shutdown to exercise logic
    shutdown()
