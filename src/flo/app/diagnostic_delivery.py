"""One application boundary for human/JSON diagnostic delivery and tracing."""

from __future__ import annotations

import contextlib
import json
from dataclasses import asdict
from typing import Any

from structlog.contextvars import bind_contextvars, unbind_contextvars

from flo.diagnostics import (
    Diagnostic,
    DiagnosticReport,
    adapt_diagnostic,
    diagnostic_report,
)


def _emit_error(
    services: Any,
    message: str,
    *,
    diagnostics_format: str = "text",
    report: DiagnosticReport | None = None,
    **event_fields: object,
) -> None:
    """Emit a user-facing error message plus structured context fields.

    The message contract remains unchanged (stderr), while event fields are
    attached through structlog contextvars for observability backends.
    """
    if diagnostics_format == "json":
        if report is None:
            record = Diagnostic(
                code=None,
                severity="error" if event_fields.get("exit_code") else "warning",
                message=message,
                stage=str(event_fields.get("error_stage") or "run_content"),
                source=(
                    "<stdin>"
                    if event_fields.get("path") in (None, "", "-")
                    else str(event_fields["path"])
                ),
            )
            report = diagnostic_report((record,))
        message = json.dumps(report.as_dict(), sort_keys=True)
    bound_keys = tuple(key for key, value in event_fields.items() if value is not None)
    try:
        bind_contextvars(**{key: event_fields[key] for key in bound_keys})
    except Exception:
        bound_keys = ()

    try:
        services.error_handler(message)
    finally:
        if bound_keys:
            with contextlib.suppress(Exception):
                unbind_contextvars(*bound_keys)


def _safe_set_span_attr(span: Any, key: str, value: object) -> None:
    setter = getattr(span, "set_attribute", None)
    if callable(setter):
        with contextlib.suppress(Exception):
            setter(key, value)


def _safe_add_span_event(
    span: Any, event_name: str, attributes: dict[str, object]
) -> None:
    add_event = getattr(span, "add_event", None)
    if callable(add_event):
        with contextlib.suppress(Exception):
            add_event(event_name, attributes)


def _handle_run_content_exception(
    *,
    root_span: Any,
    exc: Exception,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
    diagnostic_format: str = "text",
    diagnostics_format: str = "text",
) -> int:
    from flo.app.telemetry import record_span_error
    from flo.errors import map_exception_to_rc

    mapped_rc, msg, internal, error_stage = map_exception_to_rc(exc)
    diagnostic = getattr(exc, "diagnostic", None)
    if diagnostic_format == "json" and diagnostic is not None:
        msg = json.dumps(asdict(diagnostic), sort_keys=True)
    report = None
    if diagnostic is not None:
        report = diagnostic_report(
            (adapt_diagnostic(diagnostic, stage=error_stage or "run_content"),)
        )
    stage = error_stage or "run_content"
    _safe_set_span_attr(root_span, "flo.exit_code", mapped_rc)
    _safe_set_span_attr(root_span, "flo.error.stage", stage)
    record_span_error(root_span, msg or "")
    display_msg = f"Unexpected error: {msg or 'internal error'}" if internal else msg
    _emit_error(
        services,
        display_msg,
        diagnostics_format=diagnostics_format,
        report=report,
        error_kind="internal" if internal else "domain",
        error_stage=stage,
        exit_code=mapped_rc,
        internal=internal,
        command=command,
        command_id=command_id,
        path=effective_path,
    )
    return mapped_rc


def _handle_nonzero_run_content_result(
    *,
    root_span: Any,
    rc: int,
    err: str | None,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> int:
    from flo.app.telemetry import record_span_error

    _safe_set_span_attr(root_span, "flo.exit_code", rc)
    record_span_error(root_span, err or f"command failed with exit code {rc}")
    if err:
        _emit_error(
            services,
            err,
            error_kind="domain",
            error_stage="run_content",
            exit_code=rc,
            internal=False,
            command=command,
            command_id=command_id,
            path=effective_path,
        )
    return rc


def _deliver_diagnostics(
    *,
    root_span: Any,
    report: DiagnosticReport,
    options: dict,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
) -> None:
    message = report.text(include_info=bool(options.get("verbose")), prefixes=True)
    if report.warning_count:
        _safe_set_span_attr(root_span, "flo.degraded", True)
        _safe_set_span_attr(root_span, "flo.degraded_reason", message)
        _safe_add_span_event(
            root_span, "flo.degraded", {"flo.warning_count": report.warning_count}
        )
    if message or options.get("diagnostics_format") == "json":
        stage = report.diagnostics[0].stage if report.diagnostics else "complete"
        _emit_error(
            services,
            message,
            diagnostics_format=options.get("diagnostics_format", "text"),
            report=report,
            error_kind="diagnostic",
            error_stage=stage,
            exit_code=0,
            internal=False,
            command=command,
            command_id=command_id,
            path=effective_path,
        )


def _write_output_or_emit_failure(
    *,
    root_span: Any,
    out: str | None,
    options: dict,
    services: Any,
    command: str,
    command_id: str,
    effective_path: str,
    prior_report: DiagnosticReport | None = None,
) -> int | None:
    from flo.app.io import write_output
    from flo.app.telemetry import record_span_error

    if not out:
        return None
    _safe_set_span_attr(root_span, "flo.output.bytes", len(out))
    _safe_set_span_attr(root_span, "flo.output.to_file", bool(options.get("output")))
    write_rc, write_err = write_output(out, options.get("output"))
    if write_rc == 0:
        return None
    _safe_set_span_attr(root_span, "flo.exit_code", write_rc)
    record_span_error(root_span, write_err or "")
    _emit_error(
        services,
        write_err,
        diagnostics_format=options.get("diagnostics_format", "text"),
        report=diagnostic_report(
            (
                *(prior_report or DiagnosticReport()).diagnostics,
                Diagnostic(
                    code=None,
                    severity="error",
                    message=write_err,
                    stage="write_output",
                    source="<stdin>" if effective_path == "-" else effective_path,
                ),
            )
        ),
        error_kind="io",
        error_stage="write_output",
        exit_code=write_rc,
        internal=False,
        command=command,
        command_id=command_id,
        path=effective_path,
    )
    return write_rc
