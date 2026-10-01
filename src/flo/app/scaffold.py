"""Maintained starter-model scaffolding for first-time FLO authors."""

from __future__ import annotations

import re
from pathlib import Path

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

DECISION_TEMPLATE = """spec_version: "0.1"

process:
  id: {process_id}
  name: {process_name}

steps:
  - id: start
    kind: start
    name: Start

  - id: review_request
    kind: task
    name: Review Request

  - id: request_complete
    kind: decision
    name: Request Complete?
    outcomes:
      yes: complete_work
      no: revise_request

  - id: revise_request
    kind: task
    name: Revise Request

  - id: complete_work
    kind: task
    name: Complete Work

  - id: finish
    kind: end
    name: Complete

transitions:
  - source: start
    target: review_request
  - source: review_request
    target: request_complete
  - source: request_complete
    target: complete_work
    outcome: yes
  - source: request_complete
    target: revise_request
    outcome: no
  - source: revise_request
    target: complete_work
  - source: complete_work
    target: finish
"""

HANDOFF_TEMPLATE = """spec_version: "0.1"

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

  - id: fulfill_request
    kind: task
    name: Fulfill Request

  - id: finish
    kind: end
    name: Complete

transitions:
  - source: start
    target: receive_request
  - source: receive_request
    target: fulfill_request
    handoff: true
  - source: fulfill_request
    target: finish
"""

REWORK_TEMPLATE = """spec_version: "0.1"

process:
  id: {process_id}
  name: {process_name}

steps:
  - id: start
    kind: start
    name: Start

  - id: complete_work
    kind: task
    name: Complete Work

  - id: quality_check
    kind: decision
    name: Quality Check
    outcomes:
      accepted: finish
      revise: complete_work

  - id: finish
    kind: end
    name: Complete

transitions:
  - source: start
    target: complete_work
  - source: complete_work
    target: quality_check
  - source: quality_check
    target: finish
    outcome: accepted
  - source: quality_check
    target: complete_work
    outcome: revise
    edge_type: rework
    rework: true
"""

VALUE_STREAM_TEMPLATE = """spec_version: "0.1"

process:
  id: {process_id}
  name: {process_name}

items:
  - id: request
    name: Customer Request
    kind: information
  - id: component
    name: Component
    kind: material
  - id: completed_component
    name: Completed Component
    kind: material

steps:
  - id: start
    kind: start
    name: Start

  - id: receive_request
    kind: task
    name: Receive Request
    consumes: [request]
    produces: [component]

  - id: complete_work
    kind: task
    name: Complete Work
    consumes: [component]
    produces: [completed_component]

  - id: finish
    kind: end
    name: Complete
"""

SUPPORTED_TEMPLATES = (
    "simple-process",
    "linear-flow",
    "decision",
    "handoff",
    "rework",
    "value-stream",
)

_TEMPLATE_CONTENT = {
    "simple-process": SIMPLE_PROCESS_TEMPLATE,
    "linear-flow": SIMPLE_PROCESS_TEMPLATE,
    "decision": DECISION_TEMPLATE,
    "handoff": HANDOFF_TEMPLATE,
    "rework": REWORK_TEMPLATE,
    "value-stream": VALUE_STREAM_TEMPLATE,
}


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
    return _TEMPLATE_CONTENT[template].format(
        process_id=stable_id(process_name),
        process_name=process_name.strip() or "Simple Process",
    )


def model_path(path: str | Path) -> Path:
    """Return the normalized FLO source path without writing to disk."""
    target = Path(path)
    return target if target.suffix.lower() == ".flo" else target.with_suffix(".flo")


def create_model(
    path: str | Path,
    *,
    template: str = "simple-process",
    process_name: str = "Simple Process",
    overwrite: bool = False,
) -> Path:
    """Create a new FLO model, overwriting only when explicitly requested."""
    target = model_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = render_template(template=template, process_name=process_name)
    mode = "w" if overwrite else "x"
    with target.open(mode, encoding="utf-8") as handle:
        handle.write(content)
    return target
