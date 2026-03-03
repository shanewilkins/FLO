from __future__ import annotations

from types import SimpleNamespace

import flo.services.telemetry as telemetry_mod


def _fake_trace():
    return SimpleNamespace(
        set_tracer_provider=lambda provider: None,
        get_tracer=lambda name: f"tracer:{name}",
    )


def test_init_telemetry_console_exporter_exception_is_swallowed(monkeypatch):
    class FakeProvider:
        def __init__(self, resource=None):
            self.resource = resource
            self.added = []

        def add_span_processor(self, sp):
            self.added.append(sp)

    class BoomConsoleExporter:
        def __init__(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", _fake_trace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "BatchSpanProcessor", lambda exporter: object())
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", BoomConsoleExporter)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("svc", console_export=True)
    assert t.tracer == "tracer:svc"
    assert telemetry_mod._provider is not None


def test_init_telemetry_shutdown_closure_returns_when_provider_missing(monkeypatch):
    class FakeProvider:
        def __init__(self, resource=None):
            pass

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", _fake_trace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", None)
    monkeypatch.setattr(telemetry_mod, "BatchSpanProcessor", None)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("svc", console_export=False)
    monkeypatch.setattr(telemetry_mod, "_provider", None)
    t.shutdown()
    assert telemetry_mod._provider is None


def test_init_telemetry_shutdown_closure_falls_back_to_span_processors(monkeypatch):
    class ProcGood:
        def __init__(self):
            self.called = False

        def shutdown(self):
            self.called = True

    class ProcBad:
        def shutdown(self):
            raise RuntimeError("proc boom")

    class FakeProvider:
        def __init__(self, resource=None):
            self.shutdown = "not-callable"
            self.span_processors = [ProcGood(), ProcBad()]

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", _fake_trace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", None)
    monkeypatch.setattr(telemetry_mod, "BatchSpanProcessor", None)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("svc", console_export=False)
    provider = telemetry_mod._provider
    t.shutdown()

    assert provider is not None
    assert provider.span_processors[0].called is True
    assert telemetry_mod._provider is None


def test_module_shutdown_returns_after_provider_shutdown(monkeypatch):
    class Provider:
        def __init__(self):
            self.called = False

        def shutdown(self):
            self.called = True

    provider = Provider()
    monkeypatch.setattr(telemetry_mod, "_provider", provider)

    telemetry_mod.shutdown()

    assert provider.called is True
    assert telemetry_mod._provider is None
