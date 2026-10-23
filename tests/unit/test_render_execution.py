"""Production execution observation must preserve rendering and consumer ownership."""

from pathlib import Path
from unittest.mock import Mock

from flo import api
from flo.render import RenderOptions, render_artifact, render_execution
from flo.render.sppm import renderer

ROOT = Path(__file__).resolve().parents[2]


def _process():
    source = ROOT / "examples/conformance/valid/valid_basic_linear.flo"
    validated = api.validate(source.read_text(), source_path=str(source))
    assert validated.ok
    return validated.value


def test_observed_execution_uses_one_engine_call_and_preserves_artifact(monkeypatch):
    process = _process()
    options = RenderOptions.from_mapping({"diagram": "sppm", "layout_width": "800px"})
    expected = render_artifact(process, options)
    engine = Mock(wraps=renderer.run_elkjs_layout)
    monkeypatch.setattr(renderer, "run_elkjs_layout", engine)
    execution = render_execution(process, options, capture_layout=True)
    assert execution.artifact == expected
    assert engine.call_count == 1
    assert len(execution.layout_stages) == 1
    stage = execution.layout_stages[0]
    assert stage.request.diagram == "sppm"
    assert stage.request_payload["id"] == stage.response_payload["id"]
    assert stage.result.node_bounds
    assert not render_execution(process, options).layout_stages


def test_observer_mutation_cannot_change_production_geometry():
    process = _process()
    options = RenderOptions(diagram="sppm")
    expected, _ = renderer.render_sppm_svg_artifact(process, options)

    def mutate(stage):
        stage.request_payload.clear()
        stage.response_payload.clear()
        stage.result.node_bounds.clear()
        stage.result.edge_paths.clear()

    actual, _ = renderer.render_sppm_svg_artifact(
        process, options, layout_observer=mutate
    )
    assert actual == expected


def test_golden_builder_consumes_one_public_execution(monkeypatch, tmp_path):

    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import build_sppm_baseline_artifacts as baseline

    import flo.render

    observed = Mock(wraps=flo.render.render_execution)
    monkeypatch.setattr(flo.render, "render_execution", observed)
    case = {
        "id": "linear",
        "input": "examples/conformance/valid/valid_basic_linear.flo",
        "options": {"layout_width": "800px"},
    }
    baseline._build_case(
        case=case, outdir=tmp_path / "golden", debug_dir=tmp_path / "debug"
    )
    assert observed.call_count == 1
    assert observed.call_args.kwargs == {"capture_layout": True}
    assert (tmp_path / "debug/linear/elk_request.json").is_file()
    assert (tmp_path / "debug/linear/elk_response.json").is_file()
    assert (tmp_path / "golden/linear/layout_result.json").is_file()
    assert (tmp_path / "golden/linear/render.svg").is_file()
