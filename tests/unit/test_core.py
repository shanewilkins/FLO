import pytest

from flo.core import run_content, run
from flo.services.errors import ParseError, CompileError, ValidationError, RenderError


def test_run_content_empty_returns_placeholder():
    rc, out, err = run_content("")
    assert rc == 0
    assert out == ""
    assert err == ""


def test_run_content_parse_error(monkeypatch):
    # make parse_adapter raise
    def fake_parse(content):
        raise Exception("parse failed")

    monkeypatch.setattr("flo.core.parse_adapter", fake_parse)
    with pytest.raises(ParseError):
        run_content("some content")


def test_run_content_compile_error(monkeypatch, ir_factory, node_factory):
    # return a minimal valid IR so schema validation is exercised
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))

    def fake_compile(adapter):
        raise Exception("compile failed")

    monkeypatch.setattr("flo.core.compile_adapter", fake_compile)
    with pytest.raises(CompileError):
        run_content("some content")


def test_run_content_validation_error(monkeypatch, ir_factory, node_factory):
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))

    def fake_validate(ir):
        raise Exception("validation failed")

    monkeypatch.setattr("flo.core.validate_ir", fake_validate)
    with pytest.raises(ValidationError):
        run_content("some content")


def test_run_content_render_error(monkeypatch, ir_factory, node_factory):
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)

    def fake_render(ir):
        raise Exception("render failed")

    monkeypatch.setattr("flo.core.render_dot", fake_render)
    with pytest.raises(RenderError):
        run_content("some content")


def test_postprocess_nonfatal(monkeypatch, ir_factory, node_factory):
    # ensure scc_condense exceptions are ignored and run_content still succeeds
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: (lambda ir: setattr(ir, "schema_aligned", True) or ir)(ir_factory(name="t", nodes=[node_factory("n")])))
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.render_dot", lambda i: "dot")

    def bad_scc(ir):
        raise Exception("scc oops")

    monkeypatch.setattr("flo.core.scc_condense", bad_scc)
    rc, out, err = run_content("ok content")
    assert rc == 0
    assert out == "dot"


def test_run_wrapper():
    rc, out, err = run()
    assert rc == 0
    assert out == ""
