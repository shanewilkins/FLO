"""Detect the concrete responsibility breaches identified by the renderer audit.

This supplements import contracts. It checks current implementation seams, not
all architectural correctness; a clean result still requires candidate review.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

GEOMETRY_CALLS = frozenset(
    {
        "prepare_edge",
        "prepare_token",
        "finalize_sppm_scene",
        "_display_geometry",
        "_enforce_sppm_row_alignment",
        "_clip_edge_points_to_node_bounds",
        "_resolve_edge_label_placement",
        "_edge_callout_placement",
        "_avoid_bounds_overlap",
    }
)


def calls(tree: ast.AST) -> set[str]:
    """Collect direct function/method names from a module or function body."""
    aliases = {
        alias.asname or alias.name: alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    names = {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }
    return names | {aliases[name] for name in names if name in aliases}


def emitter_geometry_calls(source: str) -> list[str]:
    """Identify the current emitter's layout and annotation-policy dependencies."""
    tree = ast.parse(source)
    return sorted(calls(tree) & GEOMETRY_CALLS)


def core_policy_definitions(source: str) -> list[str]:
    """Identify SPPM-owned policy implementations inside the neutral engine seam."""
    return sorted(
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and "sppm" in node.name.lower()
    )


def core_policy_references(source: str) -> list[str]:
    """Catch diagram tags, reserved IDs, environment keys, and aliased symbols."""
    references = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Compare) and any(
            isinstance(value, ast.Attribute) and value.attr == "diagram"
            for value in (node.left, *node.comparators)
        ):
            references.add(f"diagram-dispatch:{node.lineno}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "sppm" in node.value.lower():
                references.add(f"literal:{node.value}")
        elif isinstance(node, (ast.Name, ast.Attribute, ast.alias)):
            name = getattr(node, "id", None) or getattr(node, "attr", None) or node.name
            if "sppm" in name.lower():
                references.add(f"symbol:{name}")
    return sorted(references)


def reconstructs_render_pipeline(source: str) -> bool:
    """Detect a consumer assembling engine normalization and SVG emission itself."""
    names = calls(ast.parse(source))
    return {
        "normalize_elk_layout_result",
        "render_sppm_svg_artifact_from_layout",
    } <= names


def findings(root: Path) -> list[dict]:
    """Return evidence for the three current blocking architecture findings."""
    render = root / "src/flo/render"
    emission = {}
    for relative in ("sppm/svg.py", "sppm/edge_svg.py"):
        path = render / relative
        detected = emitter_geometry_calls(path.read_text())
        if detected:
            emission[str(path.relative_to(root))] = detected
    policies = {}
    for path in sorted((render / "layout_core").rglob("*.py")):
        source = path.read_text()
        detected = sorted(
            set(core_policy_definitions(source) + core_policy_references(source))
        )
        if detected or "sppm" in path.stem:
            policies[str(path.relative_to(root))] = detected or ["diagram-owned module"]
    baseline = root / "scripts/build_sppm_baseline_artifacts.py"
    result = []
    if emission:
        result.append(
            {"id": "AF-001", "kind": "responsibility violation", "evidence": emission}
        )
    if policies:
        result.append(
            {
                "id": "AF-002",
                "kind": "ownership violation",
                "evidence": policies,
            }
        )
    if reconstructs_render_pipeline(baseline.read_text()):
        result.append(
            {
                "id": "AF-003",
                "kind": "orchestration violation after accepted clarification",
                "evidence": {
                    str(
                        baseline.relative_to(root)
                    ): "normalizes engine output and calls SVG assembly directly"
                },
            }
        )
    return result


def main() -> int:
    """Fail quickly on current responsibility breaches without running an engine."""
    violations = findings(Path(__file__).resolve().parents[1])
    print(json.dumps({"blocking_findings": violations}, indent=2, sort_keys=True))
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
