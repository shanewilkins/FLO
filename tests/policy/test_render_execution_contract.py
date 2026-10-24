"""Golden tooling observes production rendering rather than owning pipeline stages."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _render_imports(source):
    targets = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            targets.update(
                alias.name
                for alias in node.names
                if alias.name.startswith("flo.render")
            )
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "flo.render"
        ):
            targets.update(f"{node.module}.{alias.name}" for alias in node.names)
    return targets


def test_golden_render_dependencies_are_only_public_execution_and_options():
    source = (ROOT / "scripts/build_sppm_baseline_artifacts.py").read_text()
    assert _render_imports(source) == {
        "flo.render.render_execution",
        "flo.render.options.RenderOptions",
    }


def test_consumer_import_detector_recognizes_aliases_and_nested_imports():
    assert _render_imports(
        "def build():\n    from flo.render.layout_core import execute_elk_layout as run"
    ) == {"flo.render.layout_core.execute_elk_layout"}
    assert _render_imports("import flo.render.sppm.renderer as emit") == {
        "flo.render.sppm.renderer"
    }


def test_sppm_svg_emitter_has_an_enforced_layout_policy_boundary():
    import tomllib

    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    contract = next(
        item
        for item in config["tool"]["importlinter"]["contracts"]
        if item["name"] == "SPPM SVG emission cannot run node or route layout policy"
    )
    assert contract["source_modules"] == [
        "flo.render.sppm.svg",
        "flo.render.sppm.edge_svg",
    ]
    assert set(contract["forbidden_modules"]) == {
        "flo.render.sppm.scene",
        "flo.render.sppm.edge_geometry",
        "flo.render.sppm.edge_layout",
        "flo.render.sppm.attachments",
        "flo.render.sppm.avoidance",
        "flo.render.sppm.edges",
        "flo.render.sppm.geometry",
        "flo.render.sppm.rows",
        "flo.render.sppm.row_routes",
        "flo.render.sppm.layout",
        "flo.render.sppm.layout_wrap",
        "flo.render.sppm.layout_spacing",
        "flo.render.sppm.wrapped_rework",
        "flo.render.layout_core.elk",
    }
    assert not contract.get("ignore_imports")
    assert not contract.get("allow_indirect_imports", False)
