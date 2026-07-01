"""Pipeline runner and step implementations for FLO orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Tuple, List

from flo.services.io import read_input, write_output
from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.compiler.analysis import scc_condense
from flo.render import render_artifact
from flo.services.errors import (
    EXIT_PARSE_ERROR,
    EXIT_COMPILE_ERROR,
    EXIT_VALIDATION_ERROR,
    EXIT_RENDER_ERROR,
    DomainError,
)
import time

from flo.services.telemetry import get_tracer, record_span_error


_FAIL_OPEN_SCC_PREFIX = "fail-open postprocess: scc_condense failed"


def _step_error(e: Exception, services: Any, default_rc: int) -> tuple[int, None, str]:
    """Notify the error handler and map an exception to an (rc, None, message) tuple."""
    try:
        services.error_handler(str(e))
    except Exception:
        pass
    rc = e.exit_code if isinstance(e, DomainError) else default_rc
    return rc, None, str(e)


class Step(Protocol):
    """Protocol for pipeline steps."""

    def run(
        self, previous: Any, services: Any
    ) -> Any:  # pragma: no cover - exercised by unit tests
        """Execute the step and return a pipeline state tuple or compatible rc object."""
        ...


@dataclass
class ReadStep:
    """Read input from a path or stdin."""

    path: str | None = None

    def run(self, previous: Any, services: Any) -> Tuple[int, Any, Any]:
        """Execute read step and return `(rc, payload, err)` tuple."""
        if self.path:
            return read_input(self.path)
        return read_input("-")


@dataclass
class ParseStep:
    """Parse raw content into adapter model payload."""

    source_path: str | None = None

    def run(self, previous: Tuple[int, str, Any], services: Any):
        """Execute parse step and propagate parse-specific exit codes."""
        rc, content, err = previous
        if rc != 0:
            return rc, None, err
        try:
            return 0, parse_adapter(content, source_path=self.source_path), None
        except Exception as e:
            return _step_error(e, services, EXIT_PARSE_ERROR)


@dataclass
class CompileStep:
    """Compile adapter model into canonical IR."""

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        """Execute compile step and propagate compile-specific exit codes."""
        rc, adapter_model, err = previous
        if rc != 0:
            return rc, None, err
        try:
            return 0, compile_adapter(adapter_model), None
        except Exception as e:
            return _step_error(e, services, EXIT_COMPILE_ERROR)


@dataclass
class ValidateStep:
    """Validate canonical IR semantics."""

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        """Execute validation step and return mapped validation result."""
        rc, ir, err = previous
        if rc != 0:
            return rc, ir, err
        try:
            validate_ir(ir)
            return 0, ir, None
        except Exception as e:
            return _step_error(e, services, EXIT_VALIDATION_ERROR)


@dataclass
class PostprocessStep:
    """Run optional postprocessing (e.g., SCC condensation)."""

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        """Execute postprocessing step with explicit fail-open fallback policy."""
        rc, ir, err = previous
        if rc != 0:
            return rc, ir, err
        try:
            return 0, scc_condense(ir), None
        except Exception as exc:
            # Explicit fail-open policy: continue with the original IR, but
            # propagate a deterministic warning for diagnostics/telemetry.
            return 0, ir, f"{_FAIL_OPEN_SCC_PREFIX}: {exc}"


@dataclass
class RenderStep:
    """Render IR into DOT text."""

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        """Execute render step and propagate render-specific exit codes."""
        rc, ir, err = previous
        if rc != 0:
            return rc, None, err
        try:
            artifact = render_artifact(ir)
            return 0, artifact.content, None
        except Exception as e:
            return _step_error(e, services, EXIT_RENDER_ERROR)


@dataclass
class OutputStep:
    """Write rendered output to stdout or file destination."""

    options: dict | None = None

    def run(self, previous: Tuple[int, Any, Any], services: Any):
        """Execute output step and return write result tuple."""
        rc, out, err = previous
        if rc != 0:
            return rc, out, err
        write_rc, write_err = write_output(
            out, self.options.get("output") if self.options else None
        )
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
        """Initialize runner with ordered step list."""
        self.steps = steps

    @staticmethod
    def _normalize_step_state(state: Any) -> Tuple[int, Any, Any]:
        if isinstance(state, tuple) and len(state) == 3:
            return state
        if isinstance(state, int):
            return int(state), None, None
        rc = int(getattr(state, "rc", 1))
        return rc, None, None

    @staticmethod
    def _set_step_span_attributes(
        *, span: Any, step_name: str, rc: int, duration_ms: int, err: Any
    ) -> None:
        setter = getattr(span, "set_attribute", None)
        if not callable(setter):
            return
        setter("pipeline.step.name", step_name)
        setter("pipeline.step.rc", rc)
        setter("pipeline.step.duration_ms", duration_ms)
        setter("pipeline.step.status", "ok" if rc == 0 else "error")
        if rc == 0 and err:
            setter("pipeline.step.degraded", True)
            setter("pipeline.step.degraded_reason", str(err))

    @staticmethod
    def _add_step_events(
        *, span: Any, step_name: str, rc: int, duration_ms: int, err: Any
    ) -> None:
        add_event = getattr(span, "add_event", None)
        if not callable(add_event):
            return
        try:
            add_event(
                "pipeline.step.completed",
                {
                    "pipeline.step.name": step_name,
                    "pipeline.step.rc": rc,
                    "pipeline.step.duration_ms": duration_ms,
                },
            )
            if rc == 0 and err:
                add_event(
                    "pipeline.step.degraded",
                    {
                        "pipeline.step.name": step_name,
                        "pipeline.step.degraded_reason": str(err),
                    },
                )
        except Exception:
            pass

    def run(self, services: Any) -> int:
        """Run all steps sequentially, stopping on first non-zero rc."""
        state: Tuple[int, Any, Any] = (0, None, None)
        tracer = get_tracer("flo.pipeline")
        for step in self.steps:
            step_name = step.__class__.__name__
            span_name = f"pipeline.step.{step_name}"
            with tracer.start_as_current_span(span_name) as span:
                start = time.perf_counter()
                state = self._normalize_step_state(step.run(state, services))
                rc = int(state[0] or 0)
                duration_ms = int((time.perf_counter() - start) * 1000)
                self._set_step_span_attributes(
                    span=span,
                    step_name=step_name,
                    rc=rc,
                    duration_ms=duration_ms,
                    err=state[2],
                )
                self._add_step_events(
                    span=span,
                    step_name=step_name,
                    rc=rc,
                    duration_ms=duration_ms,
                    err=state[2],
                )
                if rc != 0:
                    record_span_error(span, str(state[2] or ""))
                    # stop on first non-zero rc
                    return rc
        rc = int(state[0] or 0)
        return rc
