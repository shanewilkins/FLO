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

**Status (summary)**

- [x] Example files present in `examples/` and used by tests.
- [x] `schema/flo_ir.json` and `schema/flo_types.json` exist in `schema/`.
- [x] Basic ontology/docs added under `docs/`.

Remaining v0.0 work: review and finalize the IR/typed-metadata docs for v0.1.

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

    - [x] Repository and `pyproject.toml` scaffolded; package imports and tests run.

2. IR code (Phase 1)
    - [x] Implement `flo/ir/enums.py` (NodeKind, LaneType, ValueClass).
    - [x] `flo/ir/models.py` implemented (minimal `Node` / `IR` dataclasses).
    - [x] `to_dict()` / `from_dict()` helpers and JSON serialization helpers added (basic dataclass <-> JSON mapping).

3. IR utilities & validation
         - [x] SCC condensation utility (Tarjan) implemented (`flo/analysis/scc.py`) and tested.
         - [x] `flo/ir/validate.py` present and performs basic structural checks
             (id uniqueness, node presence); JSON Schema validation helper added (requires `jsonschema`).

4. YAML adapter + parser (Phase 2)
         - [x] Pydantic v2-backed adapter model abstraction (`flo/adapters/models.py`) (fallback removed — Pydantic required).
         - [x] `flo/adapters/yaml_loader.py` implemented and returns adapter model instances.

5. Compiler: YAML → IR
         - [x] `flo/compiler/compile.py` implemented as a minimal compiler that emits
             the canonical `IR` dataclass used by downstream tools.
         - [ ] Implement advanced compilation rules: sequential-edge inference,
             decision outcome wiring, and `rework` heuristics (work in progress).

6. Tests
         - [x] Extensive unit and integration tests added across `tests/` including
             parametrized example-based tests and CLI integration tests. Tests refactored to use fixtures and factories where practical. Coverage enforced in CI (>=90%) and currently ~95% locally.

7. Renderers
     - [x] Basic DOT renderers implemented (`flo/render/graphviz_dot.py`).
     - [ ] Enhance renderers to include node IDs, labels, lanes, and decision labels.

8. CLI & UX
     - [x] CLI implemented (`flo/cli.py`) using Click thin wrapper and programmatic core.
     - [x] `-o/--output` support to write rendered DOT files.
     - [ ] Add `render --style swimlane` and richer user diagnostics.

9. CI and release
         - [x] CI workflow added and extended; tests run in CI. Coverage enforcement
             configured (`--cov-fail-under=90`). Import-check merged into main CI and CI steps updated to use the project's `uv` runner for script invocations.
         - [x] JSON Schema validation script added to CI, but it currently fails because the compiler output does not yet match the schema (see notes below).

Acceptance criteria for v0.1

- `flo validate <file>` parses, compiles, and validates `.flo` files with
    helpful diagnostics. (Implemented and tested.)
- `flo compile <file>` emits canonical IR JSON that validates against
    `schema/flo_ir.json`. (Partially implemented — compiler emits the minimal `IR` dataclass; mapping to schema fields `process`/`edges` is pending.)
- `flo render --style swimlane <file>` emits a DOT graph with node IDs,
    lane clusters, and decision labels. (Basic renderer present; swimlane style pending.)
- All components use the canonical IR as the single source of truth.

Current acceptance status:

- `flo validate` — basic parsing and validation implemented and tested.
- `flo compile` — emits the canonical `IR` dataclass and JSON helpers; does not yet produce schema-shaped IR expected by `schema/flo_ir.json`.
- `flo render --style swimlane` — not implemented yet (basic DOT renderer exists).

Remaining high-priority v0.1 tasks:

- Implement mapping from compiled `IR` to the JSON Schema shape (`process`, `nodes`, `edges`) so schema validation passes in CI. This is the main outstanding reference-implementation item.
- Add advanced compilation rules: sequential-edge inference, decision outcome wiring, and `rework` heuristics.
- Expand serializer/deserializer coverage and ensure `IR.to_dict()` is schema-aligned.
- Cover remaining telemetry shutdown/span-processor branches in tests.
- Triage complexity hotspots (`scc_condense`, `main`) and address or justify thresholds.
- Address vulture findings (unused/reachable code) or add explicit markers.
    - A vulture whitelist will be used to suppress known false positives for the
        current reference implementation (for example: Click-registered CLI
        handlers and enum members that are implemented as part of later v0.1
        work).
    - Acceptance criterion: any symbol that was whitelisted because it maps to
        planned v0.1 functionality MUST be removed from the whitelist and
        validated by CI once the corresponding feature is implemented (e.g.
        `run_cmd`/Click handlers, `NodeKind`/`LaneType` members, and compiler
        edge-wiring). CI must show vulture no longer reports those items after
        un-whitelisting.

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

