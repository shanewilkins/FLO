from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Tuple, List

from flo.services.io import read_input, write_output
from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.compiler.analysis import scc_condense
from flo.render import render_dot
import time

from flo.services.telemetry import get_tracer


class Step(Protocol):
    """Protocol for pipeline steps."""

    def run(self, previous: Any, services: Any) -> Any:  # pragma: no cover - exercised by unit tests
        ...


@dataclass
class ReadStep:
    path: str | None = None

    def run(self, previous: Any, services: Any) -> Tuple[int, Any, Any]:
        if self.path:
            return read_input(self.path)
        return read_input("-")


@dataclass
class ParseStep:
    def run(self, previous: Tuple[int, str, Any], services: Any):
        rc, content, err = previous
        if rc != 0:
            return rc, None, err
        try:
            return 0, parse_adapter(content), None
        except Exception as e:
            try:
                services.error_handler(str(e))
            except Exception:
                pass
            from flo.services.errors import EXIT_PARSE_ERROR, ParseError

            if isinstance(e, ParseError):
                return getattr(e, "code", EXIT_PARSE_ERROR), None, str(e)
            return EXIT_PARSE_ERROR, None, str(e)


@dataclass
class CompileStep:
    def run(self, previous: Tuple[int, Any, Any], services: Any):
        rc, adapter_model, err = previous
        if rc != 0:
            return rc, None, err
        try:
            return 0, compile_adapter(adapter_model), None
        except Exception as e:
            try:
                services.error_handler(str(e))
            except Exception:
                pass
            from flo.services.errors import EXIT_COMPILE_ERROR, CompileError

            if isinstance(e, CompileError):
                return getattr(e, "code", EXIT_COMPILE_ERROR), None, str(e)
            return EXIT_COMPILE_ERROR, None, str(e)


@dataclass
class ValidateStep:
    def run(self, previous: Tuple[int, Any, Any], services: Any):
        rc, ir, err = previous
        if rc != 0:
            return rc, ir, err
        try:
            validate_ir(ir)
            return 0, ir, None
        except Exception as e:
            try:
                services.error_handler(str(e))
            except Exception:
                pass
            from flo.services.errors import EXIT_VALIDATION_ERROR, ValidationError

            if isinstance(e, ValidationError):
                return getattr(e, "code", EXIT_VALIDATION_ERROR), None, str(e)
            return EXIT_VALIDATION_ERROR, None, str(e)


@dataclass
class PostprocessStep:
    def run(self, previous: Tuple[int, Any, Any], services: Any):
        rc, ir, err = previous
        if rc != 0:
            return rc, ir, err
        try:
            return 0, scc_condense(ir), None
        except Exception:
            # Fall back to original IR if postprocessing fails.
            return 0, ir, None


@dataclass
class RenderStep:
    def run(self, previous: Tuple[int, Any, Any], services: Any):
        rc, ir, err = previous
        if rc != 0:
            return rc, None, err
        try:
            dot = render_dot(ir)
            return 0, dot, None
        except Exception as e:
            try:
                services.error_handler(str(e))
            except Exception:
                pass
            from flo.services.errors import EXIT_RENDER_ERROR, RenderError

            if isinstance(e, RenderError):
                return getattr(e, "code", EXIT_RENDER_ERROR), None, str(e)
            return EXIT_RENDER_ERROR, None, str(e)


@dataclass
class OutputStep:
    options: dict | None = None

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        rc, out, err = previous
        if rc != 0:
            return rc, out, err
        write_rc, write_err = write_output(out, self.options.get("output") if self.options else None)
        if write_rc != 0:
            return write_rc, None, write_err
        return 0, None, None


class PipelineRunner:
    """Run a sequence of Steps, carrying state between them.

    Each step receives the previous step's result as its `previous`
    argument. The runner treats a step result as a 3-tuple: `(rc, payload, err)`.
    The final rc is returned as an int.
    """

    def __init__(self, steps: List[Step]):
        self.steps = steps

    def run(self, services: Any) -> int:
        state: Tuple[int, Any, Any] = (0, None, None)
        tracer = get_tracer("flo.pipeline")
        for step in self.steps:
            span_name = f"pipeline.step.{step.__class__.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                start = time.perf_counter()
                state = step.run(state, services)
                # Normalize results to expected 3-tuple
                if not (isinstance(state, tuple) and len(state) == 3):
                    if isinstance(state, int):
                        rc = int(state)
                    else:
                        rc = int(getattr(state, "rc", 1))
                        # fallback if shape unexpected
                        state = (rc, None, None)
                rc = int(state[0] or 0)
                duration_ms = int((time.perf_counter() - start) * 1000)
                setter = getattr(span, "set_attribute", None)
                if callable(setter):
                    setter("pipeline.step.name", step.__class__.__name__)
                    setter("pipeline.step.rc", rc)
                    setter("pipeline.step.duration_ms", duration_ms)
                    setter("pipeline.step.status", "ok" if rc == 0 else "error")
                if rc != 0:
                    # stop on first non-zero rc
                    return rc
        rc = int(state[0] or 0)
        return rc
