"""Reproduce candidate rendering architecture observations without changing output."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import build_sppm_baseline_artifacts as baseline  # noqa: E402
from architecture_boundaries import findings  # noqa: E402


def digest(content: str | bytes) -> str:
    """Hash a reproducible artifact or structured observation."""
    return hashlib.sha256(
        content.encode() if isinstance(content, str) else content
    ).hexdigest()


def package_digest(root: Path) -> str:
    """Fingerprint runtime source, schemas, and JavaScript independent of location."""
    files = sorted(
        path
        for path in root.rglob("*")
        if path.suffix in {".py", ".json", ".js", ".mjs"}
    )
    return digest(
        "\n".join(
            f"{path.relative_to(root).as_posix()}:{digest(path.read_bytes())}"
            for path in files
        )
    )


def trace_python(process, options):
    """Inspect engine, routed, and final scene stages from one production execution."""
    import flo.render.sppm.edge_geometry as edge_geometry
    import flo.render.sppm.renderer as renderer
    from flo.render import render_execution

    emitting = False
    counts = {"labels": 0, "attachments": 0, "avoidance": 0}
    emit = renderer.emit_sppm_svg_artifact

    def observed_emit(**kwargs):
        nonlocal emitting
        emitting = True
        try:
            return emit(**kwargs)
        finally:
            emitting = False

    def observed_call(function, counter):
        def call(*args, **kwargs):
            if emitting:
                counts[counter] += 1
            return function(*args, **kwargs)

        return call

    with (
        patch.object(renderer, "emit_sppm_svg_artifact", observed_emit),
        patch.object(
            edge_geometry,
            "_resolve_edge_label_placement",
            observed_call(edge_geometry._resolve_edge_label_placement, "labels"),
        ),
        patch.object(
            edge_geometry,
            "_clip_edge_points_to_node_bounds",
            observed_call(
                edge_geometry._clip_edge_points_to_node_bounds, "attachments"
            ),
        ),
        patch.object(
            edge_geometry,
            "_avoid_bounds_overlap",
            observed_call(edge_geometry._avoid_bounds_overlap, "avoidance"),
        ),
    ):
        execution = render_execution(process, options, capture_layout=True)
    engine = execution.layout_stages[0].result
    routed = execution.geometry_stages[0]
    scene = execution.scene_stages[0]
    observations = {
        "display_geometry_stage": "before_svg",
        "routed_stage_count": len(execution.geometry_stages),
        "final_scene_count": len(execution.scene_stages),
        "labels_placed_during_svg": counts["labels"],
        "placement_calls_during_svg": sum(counts.values()),
        "policy_calls_during_svg": counts,
        "clipped_routes": sum(
            edge.points != routed.edge_paths[edge.edge].points for edge in scene.edges
        ),
        "annotations_finalized_before_svg": sum(
            len(edge.annotations) for edge in scene.edges
        ),
        "display_changes": [
            {
                "nodes_moved": sorted(
                    node
                    for node in routed.node_bounds
                    if routed.node_bounds[node] != engine.node_bounds[node]
                ),
                "routes_changed": [
                    f"{a}->{b}"
                    for (a, b), path in sorted(routed.edge_paths.items())
                    if path.points != engine.edge_paths[(a, b)].points
                ],
            }
        ],
        "routed_geometry": {
            "canvas_bounds": asdict(routed.canvas_bounds),
            "visible_lanes": [asdict(lane) for lane in routed.lanes],
            "node_bounds": {
                key: asdict(value) for key, value in sorted(routed.node_bounds.items())
            },
            "edge_paths": [
                asdict(value) for _, value in sorted(routed.edge_paths.items())
            ],
            "node_groups": {
                key: sorted(value) for key, value in routed.node_groups.items()
            },
            "edge_groups": {
                key: sorted(value) for key, value in routed.edge_groups.items()
            },
        },
        "final_scene": {
            "edges": [asdict(edge) for edge in scene.edges],
            "occupied_bounds": [asdict(box) for box in scene.occupied_bounds],
            "width": scene.width,
            "height": scene.height,
            "content_origin": asdict(scene.content_origin),
            "header": asdict(scene.header) if scene.header else None,
            "footer": asdict(scene.footer) if scene.footer else None,
            "diagnostics": [asdict(diagnostic) for diagnostic in scene.diagnostics],
        },
        "viewport": execution.artifact.metadata.get("geometry"),
    }
    return execution.artifact, observations


def cli_arguments(source: Path, options: dict, output: Path) -> list[str]:
    """Translate the explicit trace-case settings to the actual CLI surface."""
    result = ["render", str(source), "--render-to", str(output), "--diagram", "sppm"]
    for name, value in options.items():
        flag = "--" + name.replace("_", "-")
        if value is True:
            result.append(flag)
        elif value is not False and value is not None:
            result.extend([flag, str(value)])
    return result


def installed_probe(python: Path, source: Path, options: dict, workspace: Path) -> dict:
    """Run the installed CLI in isolation and fingerprint the loaded distribution."""
    code = """import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
import flo
root=Path(flo.__file__).resolve().parent
assert root.is_relative_to(Path(sys.prefix).resolve()), str(root)
files=sorted(p for p in root.rglob('*') if p.suffix in {'.py','.json','.js','.mjs'})
payload='\\n'.join(f'{p.relative_to(root).as_posix()}:{hashlib.sha256(p.read_bytes()).hexdigest()}' for p in files)
print(json.dumps({'package_digest':hashlib.sha256(payload.encode()).hexdigest(),'location':str(root)}))
"""
    probe = subprocess.run(
        [str(python), "-c", code],
        cwd=workspace,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    identity = json.loads(probe.stdout)
    output = workspace / "installed.svg"
    result = subprocess.run(
        [str(python.with_name("flo")), *cli_arguments(source, options, output)],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(f"Installed trace failed: {result.stderr}\n{result.stdout}")
    return {**identity, "svg_digest": digest(output.read_bytes())}


def trace_case(case: dict, installed_python: Path | None = None) -> dict:
    """Compare CLI, public renderer, golden generation, and optional installed CLI."""
    from click.testing import CliRunner

    from flo import api
    from flo.app.cli import cli
    from flo.process.export import export_ir
    from flo.render import render_artifact

    source = REPO_ROOT / case["input"]
    content = source.read_text()
    validated = api.validate(content, source_path=str(source))
    if not validated.ok:
        raise RuntimeError(str(validated.diagnostics))
    process = validated.value
    before = export_ir(process)
    object_before = asdict(process)
    options = {"diagram": "sppm", **case.get("options", {})}
    with contextlib.redirect_stdout(io.StringIO()):
        artifact, observations = trace_python(process, options)
        repeated = render_artifact(process, options)
    canonical_unchanged = before == export_ir(process)
    with tempfile.TemporaryDirectory(prefix="flo-architecture-case-") as raw:
        workspace = Path(raw)
        output = workspace / "cli.svg"
        cli_result = CliRunner().invoke(
            cli, cli_arguments(source, case.get("options", {}), output)
        )
        if cli_result.exit_code:
            raise RuntimeError(cli_result.output)
        with contextlib.redirect_stdout(io.StringIO()):
            diagnostics = baseline._build_case(case=case, outdir=workspace / "golden")
        paths = {
            "python": digest(artifact.content),
            "cli": digest(output.read_bytes()),
            "golden": digest(
                (workspace / "golden" / case["id"] / "render.svg").read_bytes()
            ),
        }
        installed = (
            installed_probe(
                installed_python, source, case.get("options", {}), workspace
            )
            if installed_python
            else None
        )
        if installed:
            paths["installed_cli"] = installed["svg_digest"]
    return {
        "case": case["id"],
        "source": case["input"],
        "source_digest": digest(content),
        "options": options,
        "artifact_digests": paths,
        "paths_agree": len(set(paths.values())) == 1,
        "python_repeatable": artifact.content == repeated.content,
        "canonical_ir_unchanged": canonical_unchanged,
        "canonical_ir_object_unchanged": object_before == asdict(process),
        "render_diagnostic_count": len(artifact.metadata.get("render_diagnostics", [])),
        "golden_diagnostic_count": len(diagnostics),
        "geometry": artifact.metadata.get("geometry"),
        "observations": observations,
        "installed": installed,
    }


def cases() -> list[dict]:
    """Return the assessment's fixed linear, wrapped-correction, and stress inputs."""
    manifest = json.loads(
        (REPO_ROOT / "examples/conformance/sppm_corpus.json").read_text()
    )
    selected = {case["id"]: case for case in manifest["cases"]}
    return [
        {
            "id": "basic_linear",
            "input": "examples/conformance/valid/valid_basic_linear.flo",
            "options": {"orientation": "lr"},
        },
        selected["book_washnfold_local_rework"],
        selected["sppm_long_label_stress_lr"],
    ]


def build_report(installed_python: Path | None = None) -> dict:
    """Record observations without misrepresenting functional parity as acceptance."""
    traces = [trace_case(case, installed_python) for case in cases()]
    source_hash = package_digest(REPO_ROOT / "src/flo")
    installed_current = installed_python is not None and all(
        case["installed"]["package_digest"] == source_hash for case in traces
    )
    violations = findings(REPO_ROOT)
    architecture_docs = [
        "docs/design/adr/simplified_package_architecture.md",
        "docs/design/adr/render_stack_elk_svg_typst.md",
        "docs/design/renderers/boundaries.md",
        "docs/design/renderers/sppm.md",
        "docs/design/render_platform_target_architecture.md",
        "docs/design/adr/render_layout_finalization.md",
    ]
    return {
        "schema_version": 1,
        "assessment": "architecture validation; not release acceptance",
        "head_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip(),
        "runtime_package_digest": source_hash,
        "configuration_digests": {
            name: digest((REPO_ROOT / name).read_bytes())
            for name in (
                "pyproject.toml",
                "uv.lock",
                "package-lock.json",
                ".github/workflows/ci.yml",
                ".github/workflows/publish.yml",
                ".pre-commit-config.yaml",
            )
        },
        "assessment_tool_digests": {
            name: digest((SCRIPT_ROOT / name).read_bytes())
            for name in ("architecture_trace.py", "architecture_boundaries.py")
        },
        "installed_package_matches_source": installed_current,
        "cases": traces,
        "behavioral_checks_pass": all(
            case["paths_agree"]
            and case["python_repeatable"]
            and case["canonical_ir_unchanged"]
            and case["canonical_ir_object_unchanged"]
            and case["observations"]["placement_calls_during_svg"] == 0
            for case in traces
        ),
        "responsibility_check_pass": not violations,
        "architecture_acceptance": (
            "blocked by responsibility findings"
            if violations
            else "requires recorded clean-candidate review"
        ),
        "blocking_findings": violations,
        "architecture_document_digests": {
            name: digest((REPO_ROOT / name).read_bytes()) for name in architecture_docs
        },
        "findings_source": "docs/design/architecture_validation.md",
    }


def main() -> int:
    """Write reproducible evidence; --check fails on detected responsibility breaches."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed-python", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args.installed_python)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output, end="")
    if not report["behavioral_checks_pass"] or (
        args.installed_python and not report["installed_package_matches_source"]
    ):
        return 1
    return int(args.check and not report["responsibility_check_pass"])


if __name__ == "__main__":
    raise SystemExit(main())
