# FLO Roadmap (v0.0 -- v0.3)

This roadmap breaks the work into a conceptual v0.0 phase followed by the
implementation-focused v0.1 minimal modeling core, then v0.2 (static analytics)
and v0.3 (telemetry alignment). The v0.0 and v0.1 plan below is intentionally
concrete so contributors can make incremental, reviewable progress.

## v0.0 --- Conceptual work & stabilization (goal: lock spec + schemas)

Scope & deliverables

- Document the ontology and domain vocabulary (`docs/design/ontology.md`).
- Specify the canonical Intermediate Representation and SCC/DAG conventions
    (`docs/design/FLO_IR.md`).
- Define typed metadata for analysis and telemetry (`schema/flo_types.json` and
    `docs/design/typed_metadata.md`).
- Produce authoritative machine schemas: `schema/flo_ir.json` (structure) and
    `schema/flo_types.json` (typed keys).
- Add canonical example processes in `examples/` to exercise linear and cyclic
    behaviors.

Acceptance criteria

- IR and typed-metadata schemas committed and reviewed.
- At least two canonical examples present and validated against the schema.
- High-level SCC/DAG condensation design documented and examples explained.

Notes / guardrails

- Keep the IR small and stable — changes to the IR require a documented
    migration plan. Enforce mandatory stable `id` values in v0.1 to simplify
    telemetry joins and diffs.
- Execution semantics are limited to declarative observational mappings (no
    runtime behavior or scripts in v0.x).

## v0.1 — Minimal Modeling Core (goal: reference implementation + CLI)

Overview

v0.1 delivers a strict, usable authoring surface, a deterministic compiler to
the canonical IR, validators, a DOT renderer, and a small CLI. All tools
consume only the canonical IR (no tool should read YAML directly except the
compiler).

Planned work (step-by-step)

1. Repo + package scaffolding
     - Create `reference-implementation/python/flo/` and add `pyproject.toml`.
     - Minimal packaging so `python -m pytest` runs under the reference folder.

2. IR code (Phase 1)
     - Implement `flo/ir/enums.py` (NodeKind, LaneType, ValueClass) and
         `flo/ir/models.py` (OwnerRef, Lane, Node, Edge, FlowProcess) mirroring
         `schema/flo_ir.json`.
     - Provide `to_dict()` / `from_dict()` helpers and JSON serialization.

3. IR utilities & validation
     - Implement SCC condensation utility (Tarjan/Kosaraju) and mapping tables.
     - Implement `flo/ir/validate.py` for structural checks: id uniqueness,
         reference resolution, node-kind rules (decision outcomes), and basic
         typed-metadata checks against `schema/flo_types.json`.

4. YAML adapter + parser (Phase 2)
     - Add Pydantic-based adapter models: `flo/adapters/yaml_schema.py`.
     - Implement `flo/adapters/yaml_loader.py` to load `.flo` files, coerce types,
         and return adapter model instances.

5. Compiler: YAML → IR
     - `flo/compiler/compile.py` compiles adapter models to `FlowProcess` IR.
     - Implement sequential-edge rule (implicit sequential edges), decision
         outcome wiring, and a `rework` heuristic (tagging edges that create
         back-references into ancestor SCCs).

6. Tests
     - Unit tests for compile/validate (e.g., `tests/test_compile_valid.py`,
         `tests/test_compile_invalid.py`) using examples.

7. Renderers
     - `flo/render/graphviz_dot.py` with `render_flowchart_dot(process)` and
         `render_swimlane_dot(process)` that only use the IR.

8. CLI & UX
     - `flo/cli.py` (Typer) with commands: `validate`, `compile` (emit IR JSON),
         and `render` (DOT). Provide clear diagnostics with file/step IDs and
         actionable hints.

9. CI and release
     - Add CI workflow: linting, JSON Schema checks, unit tests. Tag v0.1 once
         CI is green and docs are finalized.

Acceptance criteria for v0.1

- `flo validate <file>` parses, compiles, and validates `.flo` files with
    helpful diagnostics.
- `flo compile <file>` emits canonical IR JSON that validates against
    `schema/flo_ir.json`.
- `flo render --style swimlane <file>` emits a DOT graph with node IDs,
    lane clusters, and decision labels.
- All components use the canonical IR as the single source of truth.

Operational guardrails (v0.1)

- IDs required and stable; no implicit ID generation.
- No execution/runtime semantics embedded in v0.1 artifacts.
- Renderers and analyzers accept only IR inputs.

## v0.2 — Static Lean Analytics Layer (outline)

Scope:

- Static analyses on IR: handoff count, rework-loop detection, longest-path
    estimates (on SCC-DAG), and step classification summaries.
- Optional annotations: `sla_target_seconds`, `value_class` (promoted from
    typed metadata schema).
- Improved diagnostics and analysis reports suitable for Lean modeling.

Deliverable: FLO suitable for static Lean analysis and heuristic insights.

## v0.3 — Telemetry Alignment & Trace Model (outline)

Scope:

- Define minimal event schema (`case_id`, `activity_key`, `timestamp`, optional `actor`).
- Implement trace-to-model alignment, node visit frequency, path frequency,
    and rework-rate computations.

Non-goals: full process mining suite or high-performance streaming.

Deliverable: Tools to bridge declarative models and observed event traces.

---

Document version: roadmap update (v0.0 → v0.1 detailed)

