from types import SimpleNamespace

from flo.services.telemetry import (
    init_telemetry,
    get_tracer,
    shutdown,
    record_span_success,
)


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


def test_record_span_success_sets_status_attributes_and_event(monkeypatch):
    calls = {"status": [], "attrs": [], "events": []}

    class _Span:
        def set_status(self, status, description=""):
            calls["status"].append((status, description))

        def set_attribute(self, key, value):
            calls["attrs"].append((key, value))

        def add_event(self, name, attributes=None, **_):
            calls["events"].append((name, attributes))

    class _StatusCode:
        OK = "OK"

    monkeypatch.setitem(
        __import__("sys").modules,
        "opentelemetry.trace",
        SimpleNamespace(StatusCode=_StatusCode),
    )

    span = _Span()
    record_span_success(
        span,
        event_name="flo.test.completed",
        attributes={"flo.exit_code": 0, "flo.command": "run"},
    )

    assert calls["status"]
    assert ("flo.exit_code", 0) in calls["attrs"]
    assert calls["events"] == [
        ("flo.test.completed", {"flo.exit_code": 0, "flo.command": "run"})
    ]
