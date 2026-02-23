from flo.services.telemetry import init_telemetry, get_tracer


def test_init_telemetry_noop():
    t = init_telemetry(service_name="flo-test")
    assert hasattr(t, "shutdown")
    # shutdown should be callable and safe to call
    t.shutdown()


def test_get_tracer_noop_contextmanager():
    tracer = get_tracer("flo-test")
    # Should support context manager API start_as_current_span
    with tracer.start_as_current_span("test-span"):
        pass
