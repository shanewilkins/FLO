from types import SimpleNamespace
from unittest.mock import Mock


import flo.services.telemetry as telemetry_mod


def _make_fake_trace(tracer_obj=None):
    class FakeTrace:
        def __init__(self):
            self._provider = None

        def set_tracer_provider(self, provider):
            self._provider = provider

        def get_tracer(self, name):
            return tracer_obj or f"tracer:{name}"

    return FakeTrace()


def test_init_telemetry_with_console_processor_and_provider_shutdown(monkeypatch):
    # Prepare fake OTEL environment
    fake_trace = _make_fake_trace(tracer_obj="fake-tracer")

    class FakeProvider:
        def __init__(self, resource=None):
            self.span_processors = []
            self.shutdown_called = False

        def add_span_processor(self, sp):
            self.span_processors.append(sp)

        def shutdown(self):
            self.shutdown_called = True

    class FakeBatchSpanProcessor:
        def __init__(self, exporter):
            self.exporter = exporter
            self.shutdown_called = False

        def shutdown(self):
            self.shutdown_called = True

    class FakeConsoleSpanExporter:
        def __init__(self):
            pass

    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(telemetry_mod, "trace", fake_trace)
    monkeypatch.setattr(telemetry_mod, "Resource", SimpleNamespace(create=lambda d: object()))
    monkeypatch.setattr(telemetry_mod, "SDKTracerProvider", FakeProvider)
    monkeypatch.setattr(telemetry_mod, "BatchSpanProcessor", FakeBatchSpanProcessor)
    monkeypatch.setattr(telemetry_mod, "ConsoleSpanExporter", FakeConsoleSpanExporter)

    # Ensure provider is reset
    monkeypatch.setattr(telemetry_mod, "_provider", None)

    t = telemetry_mod.init_telemetry("testsvc", console_export=True)
    assert t.tracer == "fake-tracer"

    # calling shutdown should call provider.shutdown()
    t.shutdown()
    # provider should be cleared
    assert getattr(telemetry_mod, "_provider") is None


def test_shutdown_falls_back_to_span_processors_when_provider_shutdown_raises(monkeypatch):
    # Create provider whose shutdown raises, but has span_processors
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

    # Call module-level shutdown which should attempt provider.shutdown and
    # then fall back to calling shutdown on span processors (swallowing errors).
    telemetry_mod.shutdown()

    # Good processor should have been called
    assert getattr(pg, "called", False) is True
    # provider cleared
    assert getattr(telemetry_mod, "_provider") is None


def test_get_tracer_returns_noop_when_otel_missing(monkeypatch):
    monkeypatch.setattr(telemetry_mod, "OTEL_AVAILABLE", False)
    monkeypatch.setattr(telemetry_mod, "trace", None)
    t = telemetry_mod.get_tracer("x")
    # Should be a NoOpTracer with a start_as_current_span contextmanager
    with t.start_as_current_span("name"):
        pass


def test_console_main_handles_clierror_and_telemetry_shutdown_is_suppressed(monkeypatch):
    # Import here to get the console_main function
    from flo.cli import console_main
    from flo.services.errors import CLIError

    # Fake services object
    services = SimpleNamespace()
    services.logger = None
    services.error_handler = Mock()
    # telemetry.shutdown will raise to ensure console_main swallows it
    services.telemetry = SimpleNamespace(shutdown=Mock(side_effect=RuntimeError("shutdown fail")))

    # Monkeypatch get_services to return our services (console_main imports this)
    import importlib as _il
    services_mod = _il.import_module("flo.services")
    monkeypatch.setattr(services_mod, "get_services", lambda verbose=False: services)

    # Monkeypatch parse_args (imported inside console_main)
    cli_args_mod = _il.import_module("flo.cli_args")
    def fake_parse_args(argv, s):
        return ("-", "run", {}, services, None)
    monkeypatch.setattr(cli_args_mod, "parse_args", fake_parse_args)

    # read_input / run_content / write_output come from flo.io and flo.core
    io_mod = _il.import_module("flo.io")
    core_mod = _il.import_module("flo.core")
    monkeypatch.setattr(io_mod, "read_input", lambda p: (0, "content", ""))

    # run_content will raise a CLIError on first subtest and later return ok
    def raise_cli(argv, command=None, options=None):
        raise CLIError("oh no", code=3)
    monkeypatch.setattr(core_mod, "run_content", raise_cli)

    # write_output shouldn't be called in this error path; stub it anyway
    monkeypatch.setattr(io_mod, "write_output", lambda out, path: (0, ""))

    rc = console_main(["dummy"])
    assert rc == 3
    services.error_handler.assert_called()

    # Now test normal flow where telemetry.shutdown raises but is swallowed
    monkeypatch.setattr(core_mod, "run_content", lambda content, command=None, options=None: (0, "out", ""))
    monkeypatch.setattr(io_mod, "write_output", lambda out, path: (0, ""))

    # telemetry.shutdown still raises; console_main should return rc without raising
    rc2 = console_main(["dummy"])
    assert rc2 == 0
