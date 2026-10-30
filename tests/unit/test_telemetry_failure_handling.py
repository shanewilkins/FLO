from __future__ import annotations

from types import SimpleNamespace

import pytest

import flo.app.telemetry as telemetry_mod


def _fake_trace():
    return SimpleNamespace(
        set_tracer_provider=lambda provider: None,
        get_tracer=lambda name: f"tracer:{name}",
    )


def test_init_telemetry_console_exporter_exception_is_swallowed(monkeypatch, caplog):
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
    monkeypatch.setattr(telemetry_mod, "SimpleSpanProcessor", lambda exporter: object())
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", BoomConsoleExporter)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    with caplog.at_level("DEBUG", logger=telemetry_mod.__name__):
        t = telemetry_mod.init_telemetry("svc", console_export=True)
    assert t.tracer == "tracer:svc"
    assert telemetry_mod._provider is not None
    assert "Failed to configure the console span exporter" in caplog.messages
    assert caplog.records[-1].levelname == "DEBUG"
    assert caplog.records[-1].exc_info is not None


@pytest.mark.parametrize("missing_symbol", ["Resource", "SDKTracerProvider"])
def test_inconsistent_sdk_state_raises_explicitly(monkeypatch, missing_symbol):
    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "_provider", None)
    monkeypatch.setattr(telemetry_mod, missing_symbol, None)

    with pytest.raises(RuntimeError, match="marked available but incomplete"):
        telemetry_mod.init_telemetry("svc")


@pytest.mark.parametrize(
    ("operation_name", "failing_method", "message"),
    [
        ("record_span_error", "set_status", "Failed to mark the span as failed"),
        (
            "record_span_error",
            "record_exception",
            "Failed to record the span exception",
        ),
        ("record_span_error", "add_event", "Failed to add the span error event"),
        ("record_span_success", "set_status", "Failed to mark the span as successful"),
        ("record_span_success", "set_attribute", "Failed to set a span attribute"),
        ("record_span_success", "add_event", "Failed to add the span success event"),
    ],
)
def test_span_annotation_failures_are_debug_logged_without_raising(
    caplog, operation_name, failing_method, message
):
    def fail(*_args, **_kwargs):
        raise RuntimeError("telemetry test failure")

    span = SimpleNamespace(**{failing_method: fail})
    operation = getattr(telemetry_mod, operation_name)

    with caplog.at_level("DEBUG", logger=telemetry_mod.__name__):
        if operation_name == "record_span_success":
            operation(span, attributes={"key": "value"})
        else:
            operation(span, "failed")

    assert caplog.messages == [message]
    assert caplog.records[0].levelname == "DEBUG"
    assert caplog.records[0].exc_info is not None


def test_init_telemetry_shutdown_closure_returns_when_provider_missing(monkeypatch):
    class FakeProvider:
        def __init__(self, resource=None):
            pass

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", _fake_trace())
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: d))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", None)
    monkeypatch.setattr(telemetry_mod, "SimpleSpanProcessor", None)
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
    monkeypatch.setattr(telemetry_mod, "SimpleSpanProcessor", None)
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("svc", console_export=False)
    provider = telemetry_mod._provider
    t.shutdown()

    assert provider is not None
    span_processors = getattr(provider, "span_processors", None)
    assert span_processors is not None
    assert span_processors[0].called is True
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
