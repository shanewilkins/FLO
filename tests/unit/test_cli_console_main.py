from types import SimpleNamespace

import flo.core.cli as cli_mod
from flo.core._cli_contract import ParsedArgs
from flo.services.errors import CLIError
from flo.services.errors import EXIT_INTERNAL_ERROR, EXIT_USAGE


def test_console_main_uses_sys_argv_when_argv_is_none(monkeypatch):
    """Verify sys.argv is used as fallback when argv is None."""
    monkeypatch.setattr(cli_mod.sys, "argv", ["flo", "from_sys.flo"])
    monkeypatch.setattr(
        "flo.core._cli_contract.parse_cli_args",
        lambda argv: ParsedArgs(path="from_sys.flo", command="render", options={}),
    )
    monkeypatch.setattr(cli_mod, "_execute_request", lambda _request: 0)

    assert cli_mod.console_main(None) == 0


def test_console_main_maps_clierror_from_execute(monkeypatch):
    """Verify CLIError codes are preserved in exit status."""
    errors = []
    services = SimpleNamespace(error_handler=lambda msg: errors.append(msg))

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr(
        "flo.core._cli_contract.parse_cli_args",
        lambda argv: ParsedArgs(path="input.flo", command="render", options={}),
    )

    def raise_clierror(_request):
        raise CLIError("bad options", code=9)

    monkeypatch.setattr(cli_mod, "_execute_request", raise_clierror)

    rc = cli_mod.console_main(["input.flo"])
    assert rc == 9
    assert errors == ["bad options"]


def test_console_main_maps_unexpected_error_from_execute(monkeypatch):
    """Verify unexpected exceptions are mapped to EXIT_INTERNAL_ERROR."""
    errors = []
    services = SimpleNamespace(error_handler=lambda msg: errors.append(msg))

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr(
        "flo.core._cli_contract.parse_cli_args",
        lambda argv: ParsedArgs(path="input.flo", command="render", options={}),
    )
    monkeypatch.setattr(
        cli_mod,
        "_execute_request",
        lambda _request: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    rc = cli_mod.console_main(["input.flo"])
    assert rc == EXIT_INTERNAL_ERROR
    assert errors == ["Unexpected error: boom"]


def test_console_main_maps_parse_args_systemexit_to_usage(monkeypatch):
    """Verify SystemExit from parse_cli_args returns EXIT_USAGE."""
    services = SimpleNamespace(error_handler=lambda _msg: None)
    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)

    def fail_parse(_argv):
        raise SystemExit("bad args")

    monkeypatch.setattr("flo.core._cli_contract.parse_cli_args", fail_parse)

    rc = cli_mod.console_main(["--bad-flag"])
    assert rc == EXIT_USAGE


def test_main_delegates_to_console_main(monkeypatch):
    """Verify main() delegates to console_main()."""
    monkeypatch.setattr(cli_mod, "console_main", lambda argv=None: 17)
    assert cli_mod.main(["x.flo"]) == 17
