"""Assessment probes detect breaches while entrypoint behavior stays protected."""

import importlib.util
import sys
from functools import cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = ROOT / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

SPEC = importlib.util.spec_from_file_location(
    "flo_architecture_trace", SCRIPT_ROOT / "architecture_trace.py"
)
assert SPEC is not None and SPEC.loader is not None
TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACE)

from architecture_boundaries import (  # noqa: E402
    core_policy_definitions,
    core_policy_references,
    emitter_geometry_calls,
    findings,
    reconstructs_render_pipeline,
)


@pytest.mark.parametrize(
    "source",
    [
        "def emit(result):\n    return _display_geometry(result)",
        "def emit(points):\n    return _clip_edge_points_to_node_bounds(points)",
        "def emit(points):\n    return _resolve_edge_label_placement(points=points)",
    ],
)
def test_assessment_detects_layout_work_in_svg_emission(source):
    assert emitter_geometry_calls(source)


def test_assessment_does_not_flag_coordinate_serialization_as_layout():
    assert not emitter_geometry_calls(
        'def emit(scene):\n    return f"<path d={scene.path!r}/>"'
    )


def test_assessment_distinguishes_diagram_policy_from_generic_engine_protocol():
    assert core_policy_definitions(
        "def _apply_sppm_wrap_rows(request):\n    return request"
    ) == ["_apply_sppm_wrap_rows"]
    assert not core_policy_definitions(
        "def normalize_coordinates(response):\n    return response"
    )
    assert core_policy_definitions(
        "def factory():\n    class SppmPolicy:\n        pass\n    return SppmPolicy"
    ) == ["SppmPolicy"]


def test_assessment_detects_consumer_reconstructing_engine_and_emitter_sequence():
    assert reconstructs_render_pipeline(
        "def build():\n    result = normalize_elk_layout_result(payload)\n    return render_sppm_svg_artifact_from_layout(result=result)"
    )
    assert not reconstructs_render_pipeline(
        "def build():\n    return render_artifact(ir, options)"
    )


def test_import_aliases_do_not_hide_forbidden_emitter_work():
    assert emitter_geometry_calls(
        "from .layout import _display_geometry as prepare\n"
        "def emit(result):\n    return prepare(result)"
    ) == ["_display_geometry"]
    assert reconstructs_render_pipeline(
        "from engine import normalize_elk_layout_result as normalize\n"
        "from emitter import render_sppm_svg_artifact_from_layout as emit\n"
        "normalize(payload)\nemit(result)"
    )


def test_neutral_policy_scan_includes_new_and_nested_modules(tmp_path):
    render = tmp_path / "src/flo/render"
    (render / "sppm").mkdir(parents=True)
    (render / "layout_core/nested").mkdir(parents=True)
    for name in ("renderer.py", "svg.py", "edges.py", "edge_svg.py"):
        (render / "sppm" / name).write_text("")
    policy = render / "layout_core/nested/new_policy.py"
    policy.write_text("def sppm_spacing():\n    return 12\n")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "build_sppm_baseline_artifacts.py").write_text("")
    violations = findings(tmp_path)
    assert [item["id"] for item in violations] == ["AF-002"]
    assert str(policy.relative_to(tmp_path)) in violations[0]["evidence"]
    policy.write_text("def normalize_coordinates():\n    return 12\n")
    assert not findings(tmp_path)


@cache
def _trace(case_index):
    return TRACE.trace_case(TRACE.cases()[case_index])


@pytest.mark.parametrize("case_index", [0, 1, 2])
def test_representative_render_paths_agree_and_preserve_canonical_ir(case_index):
    result = _trace(case_index)
    assert result["paths_agree"], result["artifact_digests"]
    assert result["observations"]["placement_calls_during_svg"] == 0
    assert result["observations"]["final_scene_count"] == 1
    assert result["python_repeatable"]
    assert result["canonical_ir_unchanged"]
    assert result["canonical_ir_object_unchanged"]
    assert result["render_diagnostic_count"] == 0
    assert result["golden_diagnostic_count"] == 0


@pytest.mark.parametrize(("check", "expected"), [(False, 0), (True, 1)])
def test_recording_blocked_assessment_does_not_make_architecture_check_pass(
    monkeypatch, tmp_path, check, expected
):
    report = {
        "behavioral_checks_pass": True,
        "installed_package_matches_source": False,
        "responsibility_check_pass": False,
        "blocking_findings": [{"id": "AF-001"}],
    }
    monkeypatch.setattr(TRACE, "build_report", lambda _installed: report)
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "architecture_trace.py",
            "--output",
            str(output),
            *(["--check"] if check else []),
        ],
    )
    assert TRACE.main() == expected
    assert '"responsibility_check_pass": false' in output.read_text()


def test_neutral_policy_probe_catches_policy_without_a_named_helper():
    assert core_policy_references('if request.diagram == "future_diagram": configure()')
    assert core_policy_references('if request.diagram == "sppm": configure()')
    assert core_policy_references('prefix = "__sppm_helper_"')
    assert core_policy_references('mode = getenv("FLO_SPPM_SPACING_PROFILE")')
    assert not core_policy_references("options = request.serialization.root_options")
