from types import SimpleNamespace

from structlog.contextvars import get_contextvars

import flo.core.cli as cli_mod
from flo.services.errors import CLIError, EXIT_INTERNAL_ERROR


def test_execute_emits_domain_error_event_fields(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr("flo.core.run_content", lambda *_args, **_kwargs: (_ for _ in ()).throw(CLIError("bad flags", code=3)))

    rc = cli_mod._execute("input.flo", "run", {})

    assert rc == 3
    msg, event = captured[-1]
    assert msg == "bad flags"
    assert event["error_kind"] == "domain"
    assert event["error_stage"] == "run_content"
    assert event["exit_code"] == 3
    assert event["internal"] is False
    assert event["command"] == "run"
    assert event["path"] == "input.flo"
    assert "error_kind" not in get_contextvars()


def test_execute_emits_internal_error_event_fields(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr("flo.core.run_content", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    rc = cli_mod._execute("input.flo", "run", {})

    assert rc == EXIT_INTERNAL_ERROR
    msg, event = captured[-1]
    assert msg == "Unexpected error: boom"
    assert event["error_kind"] == "internal"
    assert event["error_stage"] == "run_content"
    assert event["exit_code"] == EXIT_INTERNAL_ERROR
    assert event["internal"] is True
    assert event["command"] == "run"
    assert event["path"] == "input.flo"
    assert "error_kind" not in get_contextvars()
