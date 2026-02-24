from types import SimpleNamespace

import flo.services.telemetry as telemetry_mod


def test_shutdown_no_provider_returns(monkeypatch):
    # Ensure no provider leads to a no-op shutdown
    monkeypatch.setattr(telemetry_mod, "_provider", None)
    telemetry_mod.shutdown()
    assert telemetry_mod._provider is None


def test_init_telemetry_prefers_provider_shutdown(monkeypatch):
    # Fake trace provider that exposes a shutdown method
    class FakeProvider:
        def __init__(self, resource=None):
            self.shutdown_called = False

        def shutdown(self):
            self.shutdown_called = True

    class FakeTrace:
        def get_tracer(self, name):
            return f"tracer:{name}"

        def set_tracer_provider(self, provider):
            pass

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", FakeTrace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    # ensure provider cleared
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("svc", console_export=False)
    # call the returned shutdown which should prefer provider.shutdown()
    t.shutdown()
    assert telemetry_mod._provider is None


def test_shutdown_fallback_to_span_processors(monkeypatch):
    # Provider whose shutdown raises, but has span_processors
    class BadProvider:
        def __init__(self):
            self.span_processors = []

        def shutdown(self):
            raise RuntimeError("boom")

    class ProcGood:
        def __init__(self):
            self.called = False

        def shutdown(self):
            self.called = True

    class ProcBad:
        def shutdown(self):
            raise RuntimeError("proc boom")

    p = BadProvider()
    pg = ProcGood()
    pb = ProcBad()
    p.span_processors.extend([pg, pb])

    monkeypatch.setattr(telemetry_mod, "_provider", p)

    telemetry_mod.shutdown()

    assert getattr(pg, "called", False) is True
    assert telemetry_mod._provider is None


def test_init_telemetry_adds_console_span_processor(monkeypatch):
    # Validate that init_telemetry adds a BatchSpanProcessor when console_export True
    class FakeProvider:
        def __init__(self, resource=None):
            self.span_processors = []

        def add_span_processor(self, sp):
            self.span_processors.append(sp)

    class FakeBatchSpanProcessor:
        def __init__(self, exporter):
            self.exporter = exporter

    class FakeConsoleSpanExporter:
        def __init__(self):
            pass

    class FakeTrace:
        def get_tracer(self, name):
            return f"tracer:{name}"

        def set_tracer_provider(self, provider):
            pass

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", FakeTrace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "BatchSpanProcessor", FakeBatchSpanProcessor)
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", FakeConsoleSpanExporter)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    telemetry_mod.init_telemetry("svc", console_export=True)
    prov = telemetry_mod._provider
    assert prov is not None
    # ensure at least one span processor was added
    assert getattr(prov, "span_processors", [])