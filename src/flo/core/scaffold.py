"""Maintained starter-model scaffolding for first-time FLO authors."""

from __future__ import annotations

from pathlib import Path
import re


SIMPLE_PROCESS_TEMPLATE = """spec_version: "0.1"

process:
  id: {process_id}
  name: {process_name}

steps:
  - id: start
    kind: start
    name: Start

  - id: receive_request
    kind: task
    name: Receive Request

  - id: complete_work
    kind: task
    name: Complete Work

  - id: finish
    kind: end
    name: Complete
"""

SUPPORTED_TEMPLATES = ("simple-process",)


def stable_id(value: str) -> str:
    """Convert a user-facing name into a readable stable FLO identifier."""
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not normalized:
        return "simple_process"
    if normalized[0].isdigit():
        return f"process_{normalized}"
    return normalized


def render_template(*, template: str, process_name: str) -> str:
    """Render a maintained starter template with explicit stable IDs."""
    if template not in SUPPORTED_TEMPLATES:
        choices = ", ".join(SUPPORTED_TEMPLATES)
        raise ValueError(f"Unknown template '{template}'. Choose from: {choices}.")
    return SIMPLE_PROCESS_TEMPLATE.format(
        process_id=stable_id(process_name),
        process_name=process_name.strip() or "Simple Process",
    )


def create_model(
    path: str | Path,
    *,
    template: str = "simple-process",
    process_name: str = "Simple Process",
) -> Path:
    """Create a new FLO model without overwriting an existing file."""
    target = Path(path)
    if target.suffix.lower() != ".flo":
        target = target.with_suffix(".flo")
    target.parent.mkdir(parents=True, exist_ok=True)
    content = render_template(template=template, process_name=process_name)
    with target.open("x", encoding="utf-8") as handle:
        handle.write(content)
    return target
