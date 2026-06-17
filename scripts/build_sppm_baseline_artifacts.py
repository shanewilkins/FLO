"""Build canonical SPPM baseline artifacts for regression tracking."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

DEFAULT_MANIFEST = REPO_ROOT / "examples" / "conformance" / "sppm_corpus.json"
DEFAULT_OUTDIR = REPO_ROOT / "renders" / "conformance" / "sppm_baseline"
ENV_PARTITION_MODE = "FLO_SPPM_PARTITION_MODE"
ENV_PORT_CONSTRAINTS = "FLO_SPPM_PORT_CONSTRAINTS"
ENV_HELPER_ANCHORS = "FLO_SPPM_HELPER_ANCHORS"
ENV_SPACING_PROFILE = "FLO_SPPM_SPACING_PROFILE"


def main() -> int:
    """Build request, response, normalized layout, and SVG artifacts per corpus case."""
    parser = argparse.ArgumentParser(prog="build_sppm_baseline_artifacts.py")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to JSON corpus manifest.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help="Output directory for generated artifacts.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove output directory before generation.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Optional case id to build. Repeat to limit generation to a subset.",
    )
    args = parser.parse_args()

    manifest_path = _resolve_repo_path(args.manifest)
    outdir = _resolve_repo_path(args.outdir)
    cases = _filter_cases(_load_cases(manifest_path), case_ids=args.case_id)

    if args.clean and outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for case in cases:
        _build_case(case=case, outdir=outdir)

    print(
        f"Built {len(cases)} SPPM baseline cases into {outdir.relative_to(REPO_ROOT)}"
    )
    return 0


def _resolve_repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def _load_cases(manifest_path: Path) -> list[dict[str, Any]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError(f"Manifest has no cases: {manifest_path}")

    cases: list[dict[str, Any]] = []
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, dict):
            raise ValueError(f"Case at index {index} must be an object")
        case_id = raw_case.get("id")
        input_path = raw_case.get("input")
        options = raw_case.get("options", {})
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"Case at index {index} has invalid id")
        if not isinstance(input_path, str) or not input_path.strip():
            raise ValueError(f"Case '{case_id}' has invalid input path")
        if not isinstance(options, dict):
            raise ValueError(f"Case '{case_id}' options must be an object")
        cases.append({"id": case_id.strip(), "input": input_path, "options": options})
    return cases


def _filter_cases(cases: list[dict[str, Any]], *, case_ids: list[str]) -> list[dict[str, Any]]:
    if not case_ids:
        return cases
    wanted = {case_id.strip() for case_id in case_ids if case_id.strip()}
    if not wanted:
        return cases
    filtered = [case for case in cases if str(case.get("id")) in wanted]
    missing = sorted(wanted.difference(str(case.get("id")) for case in filtered))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Unknown case id(s): {missing_text}")
    return filtered


def _build_case(*, case: dict[str, Any], outdir: Path) -> None:
    from flo.adapters import parse_adapter
    from flo.render._svg_sppm import render_sppm_svg_artifact
    from flo.render.layout_core import (
        build_sppm_elk_layout_request,
        normalize_elk_layout_result,
        run_elkjs_layout,
        serialize_elk_layout_request,
    )
    from flo.render.layout_core.sppm_strategy import current_sppm_layout_strategy
    from flo.render.options import RenderOptions

    case_id = str(case["id"])
    source_path = _resolve_repo_path(Path(str(case["input"])))
    if not source_path.exists():
        raise FileNotFoundError(
            f"Input file not found for case '{case_id}': {source_path}"
        )

    options_mapping = {"diagram": "sppm", **dict(case.get("options", {}))}
    options = RenderOptions.from_mapping(options_mapping)

    model = parse_adapter(
        source_path.read_text(encoding="utf-8"), source_path=str(source_path)
    )
    request = build_sppm_elk_layout_request(model, options=options)
    request_payload = serialize_elk_layout_request(request)
    response_payload = run_elkjs_layout(request_payload)
    normalized_layout = normalize_elk_layout_result(response_payload, request=request)

    svg_artifact, _ = render_sppm_svg_artifact(model, options)
    strategy = current_sppm_layout_strategy()

    case_dir = outdir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        case_dir / "metadata.json",
        {
            "id": case_id,
            "input": str(source_path.relative_to(REPO_ROOT)),
            "options": options_mapping,
            "strategy_profile": _strategy_profile_id(),
            "strategy": {
                "partition_mode": strategy.partition_mode,
                "port_constraints": strategy.port_constraints,
                "helper_anchors": strategy.helper_anchors,
                "spacing_profile": strategy.spacing_profile,
            },
            "strategy_env": {
                ENV_PARTITION_MODE: os.getenv(ENV_PARTITION_MODE),
                ENV_PORT_CONSTRAINTS: os.getenv(ENV_PORT_CONSTRAINTS),
                ENV_HELPER_ANCHORS: os.getenv(ENV_HELPER_ANCHORS),
                ENV_SPACING_PROFILE: os.getenv(ENV_SPACING_PROFILE),
            },
        },
    )
    _write_json(case_dir / "elk_request.json", request_payload)
    _write_json(case_dir / "elk_response.json", response_payload)
    _write_json(
        case_dir / "layout_result.json", _layout_result_to_jsonable(normalized_layout)
    )
    (case_dir / "render.svg").write_text(svg_artifact.content, encoding="utf-8")

    print(f"Built: {_display_path(case_dir)}")


def _layout_result_to_jsonable(result: Any) -> dict[str, Any]:
    node_bounds = {
        node_id: asdict(bounds)
        for node_id, bounds in sorted(
            result.node_bounds.items(), key=lambda item: item[0]
        )
    }
    edge_paths: list[dict[str, Any]] = []
    for (source_id, target_id), path in sorted(
        result.edge_paths.items(), key=lambda item: item[0]
    ):
        edge_paths.append(
            {
                "source": source_id,
                "target": target_id,
                "points": [asdict(point) for point in path.points],
                "label": path.label,
                "label_point": asdict(path.label_point) if path.label_point else None,
                "source_port_side": path.source_port_side,
                "target_port_side": path.target_port_side,
                "is_rework": path.is_rework,
                "rework_variant": path.rework_variant,
                "callout_lines": list(path.callout_lines),
                "callout_near_source": path.callout_near_source,
                "outgoing_token": path.outgoing_token,
                "incoming_token": path.incoming_token,
            }
        )

    return {
        "orientation": result.orientation,
        "canvas_bounds": asdict(result.canvas_bounds),
        "lanes": [
            {
                "id": lane.id,
                "label": lane.label,
                "bounds": asdict(lane.bounds),
                "node_ids": list(lane.node_ids),
            }
            for lane in result.lanes
        ],
        "node_bounds": node_bounds,
        "edge_paths": edge_paths,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _strategy_profile_id() -> str:
    values = {
        ENV_PARTITION_MODE: os.getenv(ENV_PARTITION_MODE, "branch_aligned").strip().lower() or "branch_aligned",
        ENV_PORT_CONSTRAINTS: os.getenv(ENV_PORT_CONSTRAINTS, "fixed_order").strip().lower() or "fixed_order",
        ENV_HELPER_ANCHORS: os.getenv(ENV_HELPER_ANCHORS, "always").strip().lower() or "always",
        ENV_SPACING_PROFILE: os.getenv(ENV_SPACING_PROFILE, "balanced").strip().lower() or "balanced",
    }
    return (
        f"part={values[ENV_PARTITION_MODE]}|"
        f"port={values[ENV_PORT_CONSTRAINTS]}|"
        f"anchors={values[ENV_HELPER_ANCHORS]}|"
        f"space={values[ENV_SPACING_PROFILE]}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
