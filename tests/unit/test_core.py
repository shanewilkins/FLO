import pytest

from flo.core import run_content, run
from flo.compiler.ir.models import IR
from flo.render import RenderArtifact
from flo.services.errors import (
    CLIError,
    ParseError,
    CompileError,
    ValidationError,
    RenderError,
)


def test_run_content_empty_returns_placeholder():
    rc, out, err = run_content("")
    assert rc == 0
    assert out == ""
    assert err == ""


def test_run_content_parse_error(monkeypatch):
    # make parse_adapter raise
    def fake_parse(content, source_path=None):
        raise Exception("parse failed")

    monkeypatch.setattr("flo.core.parse_adapter", fake_parse)
    with pytest.raises(ParseError):
        run_content("some content")


def test_run_content_compile_error(monkeypatch, ir_factory, node_factory):
    # return a minimal valid IR so schema validation is exercised
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )

    def fake_compile(adapter):
        raise Exception("compile failed")

    monkeypatch.setattr("flo.core.compile_adapter", fake_compile)
    with pytest.raises(CompileError):
        run_content("some content")


def test_run_content_validation_error(monkeypatch, ir_factory, node_factory):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )

    def fake_validate(ir):
        raise Exception("validation failed")

    monkeypatch.setattr("flo.core.validate_ir", fake_validate)
    with pytest.raises(ValidationError):
        run_content("some content")


def test_run_content_render_error(monkeypatch, ir_factory, node_factory):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)

    def fake_render(ir, options=None):
        raise Exception("render failed")

    monkeypatch.setattr("flo.core.render_artifact_and_contract", fake_render)
    with pytest.raises(RenderError):
        run_content("some content")


def test_postprocess_nonfatal(monkeypatch, ir_factory, node_factory):
    # ensure scc_condense exceptions are ignored and run_content still succeeds
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr(
        "flo.core.render_artifact_and_contract",
        lambda i, options=None: (
            RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"),
            None,
        ),
    )

    def bad_scc(ir):
        raise Exception("scc oops")

    monkeypatch.setattr("flo.core.scc_condense", bad_scc)
    rc, out, err = run_content("ok content")
    assert rc == 0
    assert out == "<svg>ok</svg>"
    assert err.startswith("fail-open postprocess: scc_condense failed:")


def test_run_wrapper():
    rc, out, err = run()
    assert rc == 0
    assert out == ""


def test_run_content_returns_svg_artifact_content(
    monkeypatch, ir_factory, node_factory
):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)
    monkeypatch.setattr(
        "flo.core.render_artifact_and_contract",
        lambda i, options=None: (
            RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"),
            None,
        ),
    )

    rc, out, err = run_content(
        "some content",
        options={"diagram": "spaghetti", "export": "svg", "render_backend": "svg"},
    )
    assert rc == 0
    assert out == "<svg>ok</svg>"
    assert err == ""


def test_run_content_render_to_writes_svg_directly(
    monkeypatch, ir_factory, node_factory, tmp_path
):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)
    monkeypatch.setattr(
        "flo.core.render_artifact_and_contract",
        lambda i, options=None: (
            RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"),
            None,
        ),
    )

    out_path = tmp_path / "out.svg"
    rc, out, err = run_content(
        "some content",
        options={
            "diagram": "spaghetti",
            "export": "svg",
            "render_backend": "svg",
            "render_to": str(out_path),
        },
    )

    assert rc == 0
    assert out == ""
    assert err == ""
    assert out_path.read_text(encoding="utf-8") == "<svg>ok</svg>"


def test_run_content_render_to_rejects_non_svg_target_for_svg_artifact(
    monkeypatch, ir_factory, node_factory
):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)
    monkeypatch.setattr(
        "flo.core.render_artifact_and_contract",
        lambda i, options=None: (
            RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"),
            None,
        ),
    )

    with pytest.raises(RenderError, match=r"only \.svg output paths"):
        run_content(
            "some content",
            options={
                "diagram": "spaghetti",
                "export": "svg",
                "render_backend": "svg",
                "render_to": "/tmp/out.png",
            },
        )


def test_run_content_svg_export_rejects_non_svg_backend_override(
    monkeypatch, ir_factory, node_factory
):
    monkeypatch.setattr(
        "flo.core.parse_adapter",
        lambda c, source_path=None: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr(
        "flo.core.compile_adapter",
        lambda a: ir_factory(name="t", nodes=[node_factory("n")]),
    )
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)

    with pytest.raises(CLIError, match="SVG export currently requires"):
        run_content(
            "some content",
            options={
                "diagram": "spaghetti",
                "export": "svg",
                "render_backend": "graphviz",
            },
        )


def test_run_content_applies_render_metadata_defaults_to_render_options(
    monkeypatch, node_factory
):
    ir = IR(
        name="t",
        nodes=[node_factory("n")],
        process_metadata={
            "render": {
                "defaults": {
                    "diagram": "spaghetti",
                    "layout": {"wrap": "auto", "target_columns": 4},
                    "spaghetti": {"channel": "people"},
                }
            }
        },
    )

    monkeypatch.setattr("flo.core.parse_adapter", lambda c, source_path=None: ir)
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: ir)
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)

    captured = {}

    def fake_render(i, options=None):
        captured["options"] = options
        return RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"), None

    monkeypatch.setattr("flo.core.render_artifact_and_contract", fake_render)

    rc, out, err = run_content("some content")
    assert rc == 0
    assert out == "<svg>ok</svg>"
    assert err == ""

    render_options = captured["options"]
    assert render_options.diagram == "spaghetti"
    assert render_options.layout_wrap == "auto"
    assert render_options.layout_target_columns == 4
    assert render_options.spaghetti_channel == "people"


def test_run_content_cli_options_override_render_metadata_defaults(
    monkeypatch, node_factory
):
    ir = IR(
        name="t",
        nodes=[node_factory("n")],
        process_metadata={
            "render": {
                "defaults": {
                    "diagram": "spaghetti",
                    "layout": {"wrap": "auto"},
                    "spaghetti": {"channel": "people"},
                }
            }
        },
    )

    monkeypatch.setattr("flo.core.parse_adapter", lambda c, source_path=None: ir)
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: ir)
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)

    captured = {}

    def fake_render(i, options=None):
        captured["options"] = options
        return RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"), None

    monkeypatch.setattr("flo.core.render_artifact_and_contract", fake_render)

    rc, out, err = run_content(
        "some content",
        options={
            "diagram": "flowchart",
            "layout_wrap": "off",
            "spaghetti_channel": "material",
        },
    )
    assert rc == 0
    assert out == "<svg>ok</svg>"
    assert err == ""

    render_options = captured["options"]
    assert render_options.diagram == "flowchart"
    assert render_options.layout_wrap == "off"
    assert render_options.spaghetti_channel == "material"


def test_run_content_without_render_metadata_keeps_default_diagram(
    monkeypatch, node_factory
):
    ir = IR(name="t", nodes=[node_factory("n")], process_metadata=None)

    monkeypatch.setattr("flo.core.parse_adapter", lambda c, source_path=None: ir)
    monkeypatch.setattr("flo.core.compile_adapter", lambda a: ir)
    monkeypatch.setattr("flo.core.validate_ir", lambda i: None)
    monkeypatch.setattr("flo.core.scc_condense", lambda i: i)

    captured = {}

    def fake_render(i, options=None):
        captured["options"] = options
        return RenderArtifact(kind="svg", content="<svg>ok</svg>", backend="svg"), None

    monkeypatch.setattr("flo.core.render_artifact_and_contract", fake_render)

    rc, out, err = run_content("some content")
    assert rc == 0
    assert out == "<svg>ok</svg>"
    assert err == ""

    render_options = captured["options"]
    assert render_options.diagram == "flowchart"
