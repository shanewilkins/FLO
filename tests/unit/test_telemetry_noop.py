from flo.services.telemetry import init_telemetry, get_tracer, shutdown


def test_telemetry_noop_and_tracer():
    t = init_telemetry("flo-test")
    assert hasattr(t, "shutdown")
    # shutdown callable should be safe to call
    t.shutdown()

    tracer = get_tracer("foo")
    # should return an object supporting context manager interface
    with tracer.start_as_current_span("x"):
        pass

    # shutdown when no provider should be safe
    shutdown()
