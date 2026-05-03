from types import SimpleNamespace

import flo.core.cli as cli_mod
from flo.services.errors import CLIError, EXIT_INTERNAL_ERROR


def test_execute_shuts_down_telemetry_on_read_error(monkeypatch):
    calls: list[str] = []

    telemetry = SimpleNamespace(shutdown=lambda: calls.append("shutdown"))
    services = SimpleNamespace(
        telemetry=telemetry,
        error_handler=lambda msg: calls.append(f"err:{msg}"),
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (5, "", "read failed"))

    rc = cli_mod._execute("/missing.flo", "run", {})

    assert rc == 5
    assert calls == ["err:read failed", "shutdown"]


def test_execute_maps_unexpected_exception_to_internal(monkeypatch):
    calls: list[str] = []

    telemetry = SimpleNamespace(shutdown=lambda: calls.append("shutdown"))
    services = SimpleNamespace(
        telemetry=telemetry,
        error_handler=lambda msg: calls.append(f"err:{msg}"),
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))

    def boom(content, command="run", options=None):
        raise RuntimeError("kaboom")

    monkeypatch.setattr("flo.core.run_content", boom)

    rc = cli_mod._execute("input.flo", "run", {})

    assert rc == EXIT_INTERNAL_ERROR
    assert calls == ["err:Unexpected error: kaboom", "shutdown"]


def test_execute_maps_domain_exception_code(monkeypatch):
    calls: list[str] = []

    telemetry = SimpleNamespace(shutdown=lambda: calls.append("shutdown"))
    services = SimpleNamespace(
        telemetry=telemetry,
        error_handler=lambda msg: calls.append(f"err:{msg}"),
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))

    def fail_domain(content, command="run", options=None):
        raise CLIError("invalid option", code=3)

    monkeypatch.setattr("flo.core.run_content", fail_domain)

    rc = cli_mod._execute("input.flo", "run", {})

    assert rc == 3
    assert calls == ["err:invalid option", "shutdown"]


def test_execute_shuts_down_telemetry_on_write_error(monkeypatch):
    calls: list[str] = []

    telemetry = SimpleNamespace(shutdown=lambda: calls.append("shutdown"))
    services = SimpleNamespace(
        telemetry=telemetry,
        error_handler=lambda msg: calls.append(f"err:{msg}"),
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr("flo.core.run_content", lambda content, command="run", options=None: (0, "dot", ""))
    monkeypatch.setattr("flo.services.io.write_output", lambda out, path: (5, "write failed"))

    rc = cli_mod._execute("input.flo", "run", {"output": "out.dot"})

    assert rc == 5
    assert calls == ["err:write failed", "shutdown"]
