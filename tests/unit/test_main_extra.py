from flo import main as main_module
from flo.services import get_services
from flo.services.errors import (
    EXIT_PARSE_ERROR,
    EXIT_COMPILE_ERROR,
    EXIT_VALIDATION_ERROR,
    EXIT_RENDER_ERROR,
    EXIT_SUCCESS,
)


def make_services():
    return get_services(verbose=False)


def test_main_path_none_uses_stdin(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: (None, "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c-from-stdin", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: "dot")
    monkeypatch.setattr(main_module, "write_output", lambda out, path: (0, ""))

    rc = main_module.main([])
    assert rc == EXIT_SUCCESS


def test_main_parse_generic_exception(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: (_ for _ in ()).throw(Exception("boom")))

    rc = main_module.main(["p"])
    assert rc == EXIT_PARSE_ERROR


def test_main_compile_generic_exception(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: (_ for _ in ()).throw(Exception("boom")))

    rc = main_module.main(["p"])
    assert rc == EXIT_COMPILE_ERROR


def test_main_validate_generic_exception(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: (_ for _ in ()).throw(Exception("boom")))

    rc = main_module.main(["p"])
    assert rc == EXIT_VALIDATION_ERROR


def test_main_render_generic_exception(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: (_ for _ in ()).throw(Exception("boom")))

    rc = main_module.main(["p"])
    assert rc == EXIT_RENDER_ERROR


def test_telemetry_shutdown_exceptions_are_ignored(monkeypatch):
    services = make_services()
    # create a telemetry-like object that raises on shutdown
    class BadTelemetry:
        def shutdown(self):
            raise RuntimeError("shutdown boom")

    services.telemetry = BadTelemetry()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: "dot")
    monkeypatch.setattr(main_module, "write_output", lambda out, path: (0, ""))

    rc = main_module.main(["p"])
    assert rc == EXIT_SUCCESS
