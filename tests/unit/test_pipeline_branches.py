from __future__ import annotations

from types import SimpleNamespace

from flo.pipeline import (
    CompileStep,
    OutputStep,
    ParseStep,
    PipelineRunner,
    PostprocessStep,
    RenderStep,
    ValidateStep,
)
from flo.services.errors import CompileError, ParseError, RenderError, ValidationError


def test_parse_step_nonzero_passthrough():
    step = ParseStep()
    assert step.run((2, "content", "err"), services=None) == (2, None, "err")


def test_parse_step_maps_domain_and_generic_errors(monkeypatch):
    step = ParseStep()
    services = SimpleNamespace(error_handler=lambda msg: None)

    monkeypatch.setattr("flo.pipeline.parse_adapter", lambda _, source_path=None: (_ for _ in ()).throw(ParseError("bad parse")))
    rc, payload, err = step.run((0, "content", None), services=services)
    assert rc == ParseError("x").code
    assert payload is None
    assert "bad parse" in err

    monkeypatch.setattr("flo.pipeline.parse_adapter", lambda _, source_path=None: (_ for _ in ()).throw(Exception("boom")))
    rc, payload, err = step.run((0, "content", None), services=services)
    assert rc == 2
    assert payload is None
    assert "boom" in err


def test_compile_step_nonzero_passthrough_and_error_mapping(monkeypatch):
    step = CompileStep()
    services = SimpleNamespace(error_handler=lambda msg: None)
    assert step.run((3, object(), "err"), services=services) == (3, None, "err")

    monkeypatch.setattr("flo.pipeline.compile_adapter", lambda _: (_ for _ in ()).throw(CompileError("bad compile")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == CompileError("x").code
    assert payload is None
    assert "bad compile" in err

    monkeypatch.setattr("flo.pipeline.compile_adapter", lambda _: (_ for _ in ()).throw(Exception("boom")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == 3
    assert payload is None
    assert "boom" in err


def test_validate_step_nonzero_passthrough_and_error_mapping(monkeypatch):
    step = ValidateStep()
    services = SimpleNamespace(error_handler=lambda msg: None)
    ir = {"id": "ir"}
    assert step.run((4, ir, "err"), services=services) == (4, ir, "err")

    monkeypatch.setattr("flo.pipeline.validate_ir", lambda _: (_ for _ in ()).throw(ValidationError("bad validate")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == ValidationError("x").code
    assert payload is None
    assert "bad validate" in err

    monkeypatch.setattr("flo.pipeline.validate_ir", lambda _: (_ for _ in ()).throw(Exception("boom")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == 4
    assert payload is None
    assert "boom" in err


def test_postprocess_step_nonzero_and_fallback(monkeypatch):
    step = PostprocessStep()
    ir = {"id": "ir"}
    assert step.run((7, ir, "err"), services=None) == (7, ir, "err")

    monkeypatch.setattr("flo.pipeline.scc_condense", lambda _: (_ for _ in ()).throw(Exception("oops")))
    rc, payload, err = step.run((0, ir, None), services=None)
    assert rc == 0
    assert payload == ir
    assert err is None


def test_render_step_nonzero_passthrough_and_error_mapping(monkeypatch):
    step = RenderStep()
    services = SimpleNamespace(error_handler=lambda msg: None)
    assert step.run((5, object(), "err"), services=services) == (5, None, "err")

    monkeypatch.setattr("flo.pipeline.render_dot", lambda _: (_ for _ in ()).throw(RenderError("bad render")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == RenderError("x").code
    assert payload is None
    assert "bad render" in err

    monkeypatch.setattr("flo.pipeline.render_dot", lambda _: (_ for _ in ()).throw(Exception("boom")))
    rc, payload, err = step.run((0, object(), None), services=services)
    assert rc == 5
    assert payload is None
    assert "boom" in err


def test_output_step_nonzero_passthrough_and_write_failure(monkeypatch):
    step = OutputStep(options={"output": "out.dot"})
    assert step.run((9, "dot", "err"), services=None) == (9, "dot", "err")

    monkeypatch.setattr("flo.pipeline.write_output", lambda out, path: (5, "write failed"))
    assert step.run((0, "dot", None), services=None) == (5, None, "write failed")


def test_pipeline_runner_handles_non_tuple_state_and_non_int_state(monkeypatch):
    class Span:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, key, value):
            return None

    class Tracer:
        def start_as_current_span(self, _name):
            return Span()

    monkeypatch.setattr("flo.pipeline.get_tracer", lambda _: Tracer())

    class IntStep:
        def run(self, _state, _services):
            return 0

    class RcObjStep:
        def run(self, _state, _services):
            return SimpleNamespace(rc=0)

    class FailObjStep:
        def run(self, _state, _services):
            return SimpleNamespace(rc=2)

    assert PipelineRunner([IntStep(), RcObjStep()]).run(services=None) == 0
    assert PipelineRunner([FailObjStep()]).run(services=None) == 2
