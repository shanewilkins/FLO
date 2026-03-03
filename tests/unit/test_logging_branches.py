from __future__ import annotations

import logging
import sys
import types

from flo.services.logging import _add_otel_trace_info, _add_service_name, configure_logging


def test_add_service_name_processor_sets_and_preserves_service():
    processor = _add_service_name("flo")
    out = processor(None, "info", {"event": "x"})
    assert out["service"] == "flo"

    out2 = processor(None, "info", {"event": "x", "service": "custom"})
    assert out2["service"] == "custom"


def test_add_service_name_processor_no_name_is_noop():
    processor = _add_service_name(None)
    event = {"event": "x"}
    assert processor(None, "info", event) == event


def test_add_otel_trace_info_adds_ids_when_span_present(monkeypatch):
    class SpanContext:
        trace_id = 0xABC
        span_id = 0xDEF

    class Span:
        def get_span_context(self):
            return SpanContext()

    trace_mod = types.ModuleType("opentelemetry.trace")
    trace_mod.get_current_span = lambda: Span()
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", trace_mod)

    out = _add_otel_trace_info(None, "info", {"event": "x"})
    assert out["trace_id"] == hex(0xABC)
    assert out["span_id"] == hex(0xDEF)


def test_add_otel_trace_info_swallows_errors(monkeypatch):
    trace_mod = types.ModuleType("opentelemetry.trace")
    trace_mod.get_current_span = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", trace_mod)

    event = {"event": "x"}
    out = _add_otel_trace_info(None, "info", event)
    assert out == event


def test_configure_logging_returns_early_when_already_configured(monkeypatch):
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    try:
        root.handlers = [logging.StreamHandler()]
        called = {"value": False}

        def fake_configure(**kwargs):
            called["value"] = True

        monkeypatch.setattr("structlog.configure", fake_configure)
        configure_logging(level=logging.INFO)
        assert called["value"] is False
    finally:
        root.handlers = old_handlers
