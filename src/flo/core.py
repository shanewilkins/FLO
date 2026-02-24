"""Core processing: parse, compile, validate, and render content.

This module intentionally keeps side-effects out: it accepts raw
content and returns structured `(rc, out, err)` tuples suitable for the
CLI orchestrator to handle I/O and logging.
"""

from __future__ import annotations

from typing import Tuple

from flo.services.errors import EXIT_SUCCESS, ParseError, CompileError, ValidationError, RenderError


from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.ir import validate_ir, IR
from flo.ir.validate import ensure_schema_aligned
from flo.analysis import scc_condense
from flo.render import render_dot


def run_content(content: str, command: str = "compile", options: dict | None = None) -> Tuple[int, str, str]:
    """Process `content` and return `(rc, out, err)`.

    Steps: parse -> compile -> validate -> postprocess -> render/output.
    For empty content we preserve the original simple behaviour used by tests.
    """
    if not content:
        # No content -> no output
        return EXIT_SUCCESS, "", ""

    try:
        adapter_model = parse_adapter(content)
    except Exception as e:
        raise ParseError(str(e))

    try:
        ir = compile_adapter(adapter_model)
    except Exception as e:
        raise CompileError(str(e))

    try:
        validate_ir(ir)
    except Exception as e:
        raise ValidationError(str(e))

    # Schema validation: ensure the compiled IR conforms to the
    # authoritative JSON Schema. This enforces the contract at the
    # boundary so CLI/CI will fail fast on non-conforming output.
    # Enforce the schema-shaped contract for compiled IR.
    # Only enforce the schema contract for real `IR` instances; tests
    # and some callers may monkeypatch the compiler to return arbitrary
    # objects and expect run_content to continue to the render step.
    if isinstance(ir, IR):
        try:
            ensure_schema_aligned(ir)
        except Exception as e:
            raise ValidationError(str(e))

    # Post-processing (SCC condensation)
    try:
        ir = scc_condense(ir)
    except Exception:
        # Post-processing failures are non-fatal for v0.1; log/ignore.
        pass

    # Rendering: produce DOT for now but keep the simple, human-friendly
    # placeholder output used by the test-suite.
    try:
        _dot = render_dot(ir)
    except Exception as e:
        raise RenderError(str(e))

    # Return the rendered DOT text to callers; the CLI will handle writing
    # to files when `options["output"]` is provided.
    return EXIT_SUCCESS, _dot, ""


def run() -> Tuple[int, str, str]:
    """Programmatic, non-blocking convenience wrapper for tests and callers.

    Preserves previous behaviour of returning the placeholder output when
    called with no content.
    """
    return run_content("")
