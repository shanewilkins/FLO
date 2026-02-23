from flo import main as main_module
from flo.services import get_services
from flo.services.errors import (
    EXIT_RENDER_ERROR,
    EXIT_PARSE_ERROR,
    EXIT_COMPILE_ERROR,
    EXIT_VALIDATION_ERROR,
    EXIT_SUCCESS,
    ParseError,
    CompileError,
    ValidationError,
    RenderError,
)


def make_services():
    return get_services(verbose=False)


def test_main_success(monkeypatch):
    services = make_services()

    def fake_parse_args(argv, s):
        return ("path", "compile", {}, services, services.logger)

    monkeypatch.setattr(main_module, "parse_args", fake_parse_args)
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "content", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "scc_condense", lambda ir: ir)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: "dot")
    monkeypatch.setattr(main_module, "write_output", lambda out, path: (0, ""))

    rc = main_module.main(["path"])
    assert rc == EXIT_SUCCESS


def test_main_read_input_error(monkeypatch):
    services = make_services()

    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (EXIT_RENDER_ERROR, "", "io err"))

    rc = main_module.main(["p"])
    assert rc == EXIT_RENDER_ERROR


def test_main_parse_error(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: (_ for _ in ()).throw(ParseError("bad parse")))

    rc = main_module.main(["p"])
    assert rc == getattr(ParseError("x"), "code", EXIT_PARSE_ERROR)


def test_main_compile_error(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: (_ for _ in ()).throw(CompileError("bad compile")))

    rc = main_module.main(["p"])
    assert rc == getattr(CompileError("x"), "code", EXIT_COMPILE_ERROR)


def test_main_validation_error(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: (_ for _ in ()).throw(ValidationError("bad validate")))

    rc = main_module.main(["p"])
    assert rc == getattr(ValidationError("x"), "code", EXIT_VALIDATION_ERROR)


def test_main_render_error(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: (_ for _ in ()).throw(RenderError("bad render")))

    rc = main_module.main(["p"])
    assert rc == getattr(RenderError("x"), "code", EXIT_RENDER_ERROR)


def test_main_write_output_error(monkeypatch):
    services = make_services()
    monkeypatch.setattr(main_module, "parse_args", lambda a, s: ("p", "compile", {"output": "out"}, services, services.logger))
    monkeypatch.setattr(main_module, "read_input", lambda p: (0, "c", ""))
    monkeypatch.setattr(main_module, "parse_adapter", lambda c: object())
    monkeypatch.setattr(main_module, "compile_adapter", lambda a: object())
    monkeypatch.setattr(main_module, "validate_ir", lambda ir: None)
    monkeypatch.setattr(main_module, "scc_condense", lambda ir: ir)
    monkeypatch.setattr(main_module, "render_dot", lambda ir: "dot")
    monkeypatch.setattr(main_module, "write_output", lambda out, path: (EXIT_RENDER_ERROR, "write err"))

    rc = main_module.main(["p"])
    assert rc == EXIT_RENDER_ERROR
