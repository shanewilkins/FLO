"""Presentation-only projection of canonical waiting references."""

from typing import Any

from flo.process.measurements import measurement_reference


def project_waiting_evidence(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve direct work references on copies, retaining canonical authored nodes."""
    by_id = {node.get("id"): node for node in nodes}
    projected = []
    for node in nodes:
        reference = measurement_reference(node.get("wait_time"))
        if reference is not None:
            target = by_id.get(reference[0], {})
            if target.get("kind") in {"task", "system_task", "subprocess"}:
                projected.append({**node, "wait_time": target.get("wait_time")})
                continue
        projected.append(node)
    return projected
