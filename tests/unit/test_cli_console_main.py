from types import SimpleNamespace

import flo.core.cli as cli_mod
from flo.services.errors import CLIError
from flo.services.errors import EXIT_INTERNAL_ERROR, EXIT_USAGE


def test_console_main_uses_sys_argv_when_argv_is_none(monkeypatch):
    captured = {}
    services = SimpleNamespace(error_handler=lambda _msg: None)

    monkeypatch.setattr(cli_mod.sys, "argv", ["flo", "from_sys.flo"]) 

    def fake_get_services(verbose=False):
        return services

    def fake_parse_args(argv, svc):
        captured["argv"] = list(argv)
        return ("from_sys.flo", "run", {"export": "dot"}, svc, None)

    monkeypatch.setattr("flo.services.get_services", fake_get_services)
    monkeypatch.setattr("flo.core.cli_args.parse_args", fake_parse_args)
    monkeypatch.setattr(cli_mod, "_execute", lambda path, command, options: 0)

    assert cli_mod.console_main(None) == 0
    assert captured["argv"] == ["from_sys.flo"]


def test_console_main_maps_clierror_from_execute(monkeypatch):
    errors = []
    services = SimpleNamespace(error_handler=lambda msg: errors.append(msg))

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr(
        "flo.core.cli_args.parse_args",
        lambda argv, svc: ("input.flo", "run", {}, svc, None),
    )

    def raise_clierror(path, command, options):
        raise CLIError("bad options", code=9)

    monkeypatch.setattr(cli_mod, "_execute", raise_clierror)

    rc = cli_mod.console_main(["input.flo"])
    assert rc == 9
    assert errors == ["bad options"]


def test_console_main_maps_unexpected_error_from_execute(monkeypatch):
    errors = []
    services = SimpleNamespace(error_handler=lambda msg: errors.append(msg))

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr(
        "flo.core.cli_args.parse_args",
        lambda argv, svc: ("input.flo", "run", {}, svc, None),
    )
    monkeypatch.setattr(cli_mod, "_execute", lambda path, command, options: (_ for _ in ()).throw(RuntimeError("boom")))

    rc = cli_mod.console_main(["input.flo"])
    assert rc == EXIT_INTERNAL_ERROR
    assert errors == ["Unexpected error: boom"]


def test_console_main_maps_parse_args_systemexit_to_usage(monkeypatch):
    services = SimpleNamespace(error_handler=lambda _msg: None)
    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)

    def fail_parse(_argv, _svc):
        raise SystemExit("bad args")

    monkeypatch.setattr("flo.core.cli_args.parse_args", fail_parse)

    rc = cli_mod.console_main(["--bad-flag"])
    assert rc == EXIT_USAGE


def test_main_delegates_to_console_main(monkeypatch):
    monkeypatch.setattr(cli_mod, "console_main", lambda argv=None: 17)
    assert cli_mod.main(["x.flo"]) == 17
