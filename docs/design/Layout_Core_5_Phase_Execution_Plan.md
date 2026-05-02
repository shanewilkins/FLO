# Layout Core 5-Phase Execution Plan

Status: Draft for same-day execution
Date: 2026-04-28
Owner: Rendering workstream

## Objective
Build a clean, reusable rendering architecture where placement is solved first, then corridors, then port-aware edge landing. Ensure the core can be reused by SPPM, flowchart, swimlane, and future render styles.

## Guiding Principles
- Placement is a first-class plan, not an incidental side effect of DOT hints.
- Corridors are computed from placement, not from ad hoc edge exceptions.
- Port assignment is deterministic and policy-driven.
- DOT emission is translation-only: no hidden layout decisions.
- Reuse across renderers is a required design constraint.

## API Conventions (v0.1)
To keep render architecture extensible while FLO is still pre-1.0, wrap planning
follows one canonical API pattern:

- Public entrypoint: `build_wrap_plan(nodes, options, planner=...)`
- Public plan contract: `WrapPlan`
- Public strategy selector: `WrapPlannerKind = "chunked" | "placement"`
- Strategy implementations remain private (`_build_*`)

Rationale:
- Renderer call sites stay uniform and easy to audit.
- New render styles can opt into existing or new planner strategies without
	expanding public helper surface area.
- Routing and DOT emission consume one stable `WrapPlan` contract regardless of
	planner strategy.

Extension rules:
- Add new planning behavior by adding a new `planner` strategy and private
	implementation, not by creating another public `build_*_wrap_plan` function.
- Keep option-to-geometry translation in planner code, not renderer emitters.
- Keep renderer modules translation-focused (consume plans, emit DOT).

## Non-Goals (for this plan)
- No broad visual redesign work outside the placement and routing architecture.
- No new CLI feature expansion beyond what is needed to support alignment and placement constraints.
- No renderer-specific forks of core placement logic.

## Acceptance Fixture
Primary acceptance fixture:
- examples/reference/washnfold.flo with SPPM, LR, wrap auto, width 800

Minimum acceptance checks:
- Stable row breaks at fixed settings
- Readable spacing between boxes
- Boundary transitions land on node edges
- No obvious edge paths through node interiors

---

## Phase 1: Shared Placement Core (Renderer-Agnostic)
Goal:
- Extract deterministic packing and alignment into a shared core module.

Scope:
- Compute line breaks from max width or max height
- Produce explicit placement plan data
- Support alignment options on cross-axis and stack-axis

Proposed modules:
- src/flo/render/layout_core/models.py
- src/flo/render/layout_core/placement.py

Primary data contracts:
- NodeMeasure: id, width_px, height_px, kind
- PlacementConstraints: orientation, max_width_px or max_height_px, gaps, margins, align options
- LinePlacement: ordered node ids, extents, offsets
- PlacementPlan: lines, node_line_index, boundary_edges, total extents

Deliverables:
- Deterministic packer implementation
- Unit tests for deterministic row and column packing
- Unit tests for boundary edge derivation
- Unit tests for alignment modes: start, center, end

Exit criteria:
- Placement tests pass and are stable across repeated runs
- No renderer integration yet

---

## Phase 2: Integrate PlacementPlan into SPPM
Goal:
- Make SPPM consume PlacementPlan while preserving baseline visual behavior.

Scope:
- Replace SPPM-specific wrapping math with shared placement outputs
- Keep boundary edge rendering simple and stable during this phase
- Avoid introducing new corridor geometry behavior yet

Touch points:
- src/flo/render/_graphviz_dot_sppm.py
- src/flo/render/_autoformat_wrap.py (shrink to adapter or deprecate)

Deliverables:
- SPPM renderer using shared placement outputs
- Updated unit tests asserting placement-derived boundaries
- No synthetic boundary corridor nodes by default

Exit criteria:
- Existing SPPM unit suites pass
- Acceptance fixture render is at least baseline-stable

---

## Phase 3: Shared Corridor Skeleton (Optional in Output, Required in Core)
Goal:
- Add a corridor planning stage derived from PlacementPlan.

Scope:
- Compute deterministic lanes between adjacent lines
- Build corridor graph structures independent of any renderer
- Keep corridor use in emitted DOT opt-in until validated

Proposed module:
- src/flo/render/layout_core/corridors.py

Primary data contracts:
- CorridorLane: id, line_from, line_to, channel index
- CorridorPlan: lanes, entry anchors, exit anchors, occupancy metadata

Deliverables:
- Corridor plan generator
- Unit tests for lane determinism and basic occupancy rules

Exit criteria:
- Corridor plan deterministic for fixed input and options
- No regression to default renderer output path

---

## Phase 4: Port Assignment and Edge Routing on Core Plans
Goal:
- Assign ports and route edges using PlacementPlan plus CorridorPlan.

Scope:
- Deterministic source and target port selection
- Deterministic lane assignment for boundary and non-boundary transitions
- Conflict policy for concurrent lane demands

Proposed modules:
- src/flo/render/layout_core/ports.py
- src/flo/render/layout_core/routing.py

Primary data contracts:
- PortSpec: node id, side, slot index, role
- EdgeRoute: source port, lane hops, target port
- RoutePlan: all edge routes and conflict outcomes

Deliverables:
- Routing engine with deterministic policies
- Unit tests for port selection and lane assignment
- Snapshot tests for route plan outputs
- Renderer hookup that maps core port slots to named Graphviz ports in SPPM

Exit criteria:
- Stable routing snapshots for acceptance fixture
- No mid-box edge landings on acceptance render

Implementation note:
- Phase 4 is not complete when only core `PortSpec` / `RoutePlan` data exists.
	The SPPM renderer must expose explicit named ports in emitted DOT so
	Graphviz can honor deterministic slot assignments visually.

---

## Phase 5: Reuse Validation Beyond SPPM
Goal:
- Prove the new core works across multiple render styles.

Scope:
- Integrate flowchart as second consumer first
- Optionally integrate swimlane next
- Keep renderer adapters thin and style-focused

Touch points:
- src/flo/render/_graphviz_dot_flowchart.py
- src/flo/render/_graphviz_dot_swimlane.py

Deliverables:
- Flowchart uses shared placement core
- Cross-renderer tests for placement consistency
- Documented adapter responsibilities per renderer

Exit criteria:
- At least two render styles consume shared placement core
- No duplicated placement logic reintroduced in renderer modules

---

## Alignment Options (Initial Recommendation)
Implement two orthogonal options first:
- layout_align_line: start, center, end
- layout_align_stack: start, center, end

Semantics:
- line alignment controls cross-axis positioning of items within each row or column
- stack alignment controls how shorter rows or columns align relative to longest row or column

Notes:
- Keep justification modes out of v1
- Add after baseline stability only

---

## Testing Strategy by Phase
Phase 1:
- Unit tests for packing and alignment only

Phase 2:
- SPPM integration tests and acceptance fixture render check

Phase 3:
- Corridor unit tests, no default output activation

Phase 4:
- Route and port snapshot tests plus acceptance fixture visual check

Phase 5:
- Cross-renderer consistency tests

---

## Same-Day Execution Checklist
Use this as the completion checklist for today.

1. Phase 1 complete
- Shared placement models and packer committed
- Placement tests green

2. Phase 2 complete
- SPPM wired to PlacementPlan
- SPPM tests green
- Acceptance fixture rerendered and reviewed

3. Stop-and-review checkpoint
- Confirm placement quality and baseline stability before Phase 3

Stretch goal for today:
- Start Phase 3 scaffolding only if Phases 1 and 2 are stable and accepted

---

## Risks and Mitigations
Risk:
- Reintroducing renderer-specific placement logic
Mitigation:
- Enforce adapter-only renderer responsibilities in code review

Risk:
- Visual regressions hidden by text-only tests
Mitigation:
- Keep acceptance fixture checks in every integration phase

Risk:
- Over-constraining Graphviz with mixed responsibilities
Mitigation:
- Keep placement decisions in core and DOT layer translation-only

---

## Definition of Done (Program-Level)
- Shared placement core exists and is used by at least two renderers
- Corridor and routing are separate stages with explicit data contracts
- Acceptance fixture is visually sane and stable
- Test coverage protects deterministic placement and routing behavior
- Architecture remains clean: domain, placement, corridor, routing, rendering are separated

---

## Phase 6: Two-Pass Graphviz Rendering for Exact Anchor Placement

### Background

SPPM return-loop edges (rework → mainline) require a corridor anchor node to
split the edge into two segments, enabling the characteristic L-shaped path:
exit west from the rework node, turn north once, arrive at the bottom of the
mainline box.

The problem: Graphviz places the anchor's Y position freely during rank
assignment. Any Y that differs from the rework node's Y creates an extra bend.
We cannot express "anchor Y = rework Y, anchor X = mainline X" purely in DOT.

### Solution: Two-Pass Layout

**Pass 1** — layout pass:
- Emit DOT with all nodes and constraints as normal.
- Run `dot -Tdot` (DOT output format includes computed `pos` attributes on
  every node after layout).
- Parse the `pos` of each rework source node and its corresponding mainline
  target node from the layout output.

**Anchor position injection**:
- For each return-loop anchor, compute: `x = mainline_target.x`, `y = rework_source.y`
- Inject `pos="x,y!"` on the anchor node in the DOT (the `!` pins the position).

**Pass 2** — render pass:
- Re-run Graphviz using `-n2` flag (skip node positioning, use existing `pos`,
  only route edges) with the desired output format (`-Tsvg`, `-Tdot`, etc).

### Result

The anchor is pinned at the exact corner of the desired L. Graphviz ortho
routing then produces exactly one bend per return loop with no ambiguity.

### Scope

Touch points:
- `src/flo/render/_graphviz_backend.py` (or equivalent Graphviz invocation site)
  — add `render_dot_two_pass(dot_src, format)` function
- `src/flo/render/_graphviz_dot_sppm.py` — tag return-loop anchor nodes with a
  sentinel attribute (e.g. `_sppm_return_anchor_source="rework_intake"`) so the
  post-layout injector knows which nodes to pin and which reference nodes to
  read positions from

Data flow:
```
DOT source
  → dot -Tdot       (pass 1: layout)
  → parse pos       (extract anchor, rework, mainline positions)
  → inject pos=...! (pin anchor corners)
  → dot -n2 -Tsvg   (pass 2: route + render)
  → SVG output
```

### Acceptance Criteria
- sppm_feature_showcase return loops each have exactly one bend (W→N)
- washnfold SPPM render is not regressed
- Single-rework diagrams (sppm_attachment_minimal_repro) are not regressed
- Two-pass is transparent to callers: same API as current single-pass render
