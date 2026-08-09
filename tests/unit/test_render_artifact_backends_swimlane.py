from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import ensure_schema_aligned, validate_ir
from flo.render import render_artifact


def test_reference_swimlane_svg_artifact_is_deterministic():
    artifact = _render_reference_swimlane()
    rerun_artifact = _render_reference_swimlane()

    assert artifact.kind == "svg"
    assert artifact.backend == "svg"
    assert artifact.content == rerun_artifact.content
    assert _swimlane_svg_signature(artifact.content) == {
        "diagram": "swimlane",
        "backend": "svg",
        "layout_engine": "elk",
        "lanes": (
            "requester",
            "manager",
            "finance",
            "procurement",
            "vendor",
        ),
        "nodes": (
            "start",
            "draft_request",
            "manager_review",
            "budget_check",
            "request_revision",
            "create_po",
            "vendor_fulfillment",
            "receive_goods",
            "close_request",
            "notify_reject",
        ),
        "edges": (
            "budget_check->create_po",
            "budget_check->request_revision",
            "create_po->vendor_fulfillment",
            "draft_request->manager_review",
            "manager_review->budget_check",
            "manager_review->notify_reject",
            "receive_goods->close_request",
            "request_revision->draft_request",
            "start->draft_request",
            "vendor_fulfillment->receive_goods",
        ),
        "labels": ("approved", "rejected"),
    }


def _render_reference_swimlane():
    path = Path("examples/reference/swimlane.flo")
    adapter_model = parse_adapter(
        path.read_text(encoding="utf-8"), source_path=str(path)
    )
    ir = compile_adapter(adapter_model)
    validate_ir(ir)
    ensure_schema_aligned(ir)
    return render_artifact(
        ir,
        options={"diagram": "swimlane", "render_backend": "svg"},
    )


def _swimlane_svg_signature(svg: str) -> dict[str, object]:
    root = ET.fromstring(svg)
    lanes = tuple(
        element.attrib["data-lane-id"]
        for element in root.iter()
        if "data-lane-id" in element.attrib
    )
    nodes = tuple(
        element.attrib["data-node-id"]
        for element in root.iter()
        if "data-node-id" in element.attrib
    )
    edges = tuple(
        f"{element.attrib['data-edge-source']}->{element.attrib['data-edge-target']}"
        for element in root.iter()
        if "data-edge-source" in element.attrib and "data-edge-target" in element.attrib
    )
    labels = tuple(
        sorted(
            {
                (element.text or "").strip()
                for element in root.iter()
                if (element.text or "").strip() in {"approved", "rejected"}
            }
        )
    )
    return {
        "diagram": root.attrib.get("data-flo-diagram"),
        "backend": root.attrib.get("data-flo-backend"),
        "layout_engine": root.attrib.get("data-flo-layout-engine"),
        "lanes": lanes,
        "nodes": nodes,
        "edges": edges,
        "labels": labels,
    }
