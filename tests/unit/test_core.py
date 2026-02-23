import pytest

from flo.core import run_content, run
from flo.services.errors import ParseError, CompileError, ValidationError, RenderError


def test_run_content_empty_returns_placeholder():
    rc, out, err = run_content("")
    assert rc == 0
    assert out == "Hello world!"
    assert err == ""


def test_run_content_parse_error(monkeypatch):
    # make parse_adapter raise
    def fake_parse(content):
        raise Exception("parse failed")

    monkeypatch.setattr("flo.core.parse_adapter", fake_parse)
    with pytest.raises(ParseError):
        run_content("some content")


def test_run_content_compile_error(monkeypatch):
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: object())

    def fake_compile(adapter):
        raise Exception("compile failed")

    monkeypatch.setattr("flo.core.compile_adapter", fake_compile)
    with pytest.raises(CompileError):
        run_content("some content")


def test_run_content_validation_error(monkeypatch):
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: object())
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: object())

    def fake_validate(ir):
        raise Exception("validation failed")

    monkeypatch.setattr("flo.core.validate_ir", fake_validate)
    with pytest.raises(ValidationError):
        run_content("some content")


def test_run_content_render_error(monkeypatch):
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: object())
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: object())
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)

    def fake_render(ir):
        raise Exception("render failed")

    monkeypatch.setattr("flo.core.render_dot", fake_render)
    with pytest.raises(RenderError):
        run_content("some content")


def test_postprocess_nonfatal(monkeypatch):
    # ensure scc_condense exceptions are ignored and run_content still succeeds
    monkeypatch.setattr("flo.core.parse_adapter", lambda c: object())
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: object())
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.render_dot", lambda i: "dot")

    def bad_scc(ir):
        raise Exception("scc oops")

    monkeypatch.setattr("flo.core.scc_condense", bad_scc)
    rc, out, err = run_content("ok content")
    assert rc == 0
    assert out == "Hello world!"


def test_run_wrapper():
    rc, out, err = run()
    assert rc == 0
    assert out == "Hello world!"
