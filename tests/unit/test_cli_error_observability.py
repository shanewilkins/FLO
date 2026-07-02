from types import SimpleNamespace

from structlog.contextvars import get_contextvars

import flo.core.cli as cli_mod
from flo.services.errors import (
    CLIError,
    CompileError,
    ParseError,
    EXIT_INTERNAL_ERROR,
    EXIT_VALIDATION_ERROR,
)


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
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(CLIError("bad flags", code=3)),
    )

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
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

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


def test_execute_emits_verbose_diagnostic_on_fail_open_fallback(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (
            0,
            "<svg />",
            "fail-open postprocess: scc_condense failed: boom",
        ),
    )
    monkeypatch.setattr("flo.services.io.write_output", lambda out, path: (0, ""))

    rc = cli_mod._execute("input.flo", "run", {"verbose": True})

    assert rc == 0
    msg, event = captured[-1]
    assert msg.startswith("Warning: fail-open postprocess: scc_condense failed:")
    assert event["error_kind"] == "diagnostic"
    assert event["error_stage"] == "fail_open_fallback"
    assert event["exit_code"] == 0
    assert event["command"] == "run"
    assert event["path"] == "input.flo"


def test_execute_emits_write_output_error_fields_on_export_json(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (0, '{"process":{},"nodes":[],"edges":[]}', ""),
    )
    monkeypatch.setattr(
        "flo.services.io.write_output",
        lambda out, path: (5, "I/O error writing out.json: boom"),
    )

    rc = cli_mod._execute("input.flo", "run", {"export": "json", "output": "out.json"})

    assert rc == 5
    msg, event = captured[-1]
    assert msg == "I/O error writing out.json: boom"
    assert event["error_kind"] == "io"
    assert event["error_stage"] == "write_output"
    assert event["exit_code"] == 5
    assert event["command"] == "run"
    assert event["path"] == "input.flo"


def test_execute_maps_compile_error_stage_granularity(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            CompileError("compile failed", error_stage="compile")
        ),
    )

    rc = cli_mod._execute("input.flo", "run", {"export": "json"})

    assert rc == 3
    msg, event = captured[-1]
    assert msg == "compile failed"
    assert event["error_kind"] == "domain"
    assert event["error_stage"] == "compile"
    assert event["exit_code"] == 3


def test_execute_maps_parse_error_stage_granularity(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr("flo.services.io.read_input", lambda path: (0, "content", ""))
    monkeypatch.setattr(
        "flo.core.run_content",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ParseError("parse failed", error_stage="parse")
        ),
    )

    rc = cli_mod._execute("input.flo", "run", {"export": "json"})

    assert rc == 2
    msg, event = captured[-1]
    assert msg == "parse failed"
    assert event["error_kind"] == "domain"
    assert event["error_stage"] == "parse"
    assert event["exit_code"] == 2


def test_execute_emits_render_intent_validation_stage_from_real_pipeline(monkeypatch):
    captured: list[tuple[str, dict[str, object]]] = []

    def error_handler(msg: str) -> None:
        captured.append((msg, dict(get_contextvars())))

    services = SimpleNamespace(
        telemetry=SimpleNamespace(shutdown=lambda: None),
        error_handler=error_handler,
    )

    invalid_render_intent = "\n".join(
        [
            'spec_version: "0.1"',
            "",
            "process:",
            "  id: p",
            "  name: Process",
            "  metadata:",
            "    render:",
            "      defaults:",
            "        diagram: sppm",
            "      views:",
            '        "":',
            "          diagram: sppm",
            "",
            "steps:",
            "  - id: start",
            "    kind: start",
            "    name: Start",
            "  - id: end",
            "    kind: end",
            "    name: End",
            "",
            "transitions:",
            "  - source: start",
            "    target: end",
            "",
        ]
    )

    monkeypatch.setattr("flo.services.get_services", lambda verbose=False: services)
    monkeypatch.setattr(
        "flo.services.io.read_input",
        lambda path: (0, invalid_render_intent, ""),
    )

    rc = cli_mod._execute("input.flo", "validate", {})

    assert rc == EXIT_VALIDATION_ERROR
    msg, event = captured[-1]
    assert "view id must be non-empty string" in msg
    assert event["error_kind"] == "domain"
    assert event["error_stage"] == "validate_render_intent"
    assert event["exit_code"] == EXIT_VALIDATION_ERROR
    assert event["command"] == "validate"
    assert event["path"] == "input.flo"
