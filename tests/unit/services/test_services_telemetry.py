import importlib


def test_init_telemetry_no_otel(monkeypatch):
    # Ensure module behaves correctly when OpenTelemetry is unavailable
    mod = importlib.import_module("flo.services.telemetry")

    # Force the module into the "not available" state
    monkeypatch.setattr(mod, "OTEL_AVAILABLE", False)
    monkeypatch.setattr(mod, "trace", None)

    telem = mod.init_telemetry("flo-test")
    assert telem.tracer is None
    # shutdown should be callable and not raise
    telem.shutdown()

    tracer = mod.get_tracer("anything")
    # The no-op tracer exposes a contextmanager start_as_current_span
    with tracer.start_as_current_span("name") as span:
        assert span is not None


def test_shutdown_no_provider(monkeypatch):
    mod = importlib.import_module("flo.services.telemetry")
    # Ensure provider is None and shutting down is fine
    monkeypatch.setattr(mod, "_provider", None)
    # Should not raise
    mod.shutdown()
