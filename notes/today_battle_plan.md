# FLO Today Battle Plan Scorecard

Date: 2026-05-22
Owner: Shane + Copilot
Purpose: Keep scope boundaries clear while we stabilize routing and prepare Typst migration.

## How To Score

- Status: Not Started, In Progress, Blocked, Done
- Score: 0 = not started, 1 = partial, 2 = done
- Day target: 8 to 10 points total

## Item 1: Arrow Path Stabilization

Status: Done
Score: 2/2

Goal:
- Stabilize the top 3 most painful edge-routing path archetypes in current ELK plus SVG output.

In Scope:
- Endpoint attachment correctness
- Rework loop route clarity
- Deterministic path behavior under repeated runs

Out Of Scope:
- Typst rendering changes
- Page style and publication polish

Done Criteria:
- 3 archetypes identified and reproduced
- Golden or snapshot tests added
- No endpoint misattachment in selected fixtures

Notes:
- Archetype 1 completed: rework branch postprocess now emits orthogonal elbow path (no diagonal second leg).
- Added regression for west-target branch so final segment stays horizontal before arrow tip.
- Archetype 2 completed: wrapped-boundary contract fallback now resolves actual wrap anchor from SVG titles when anchor_id is omitted/non-sequential.
- Archetype 3 completed: return-loop fallback under missing target bounds now has explicit regression assertions for second-leg rewrite and deterministic arrowhead orientation.

## Item 1.5: Capability Matrix + Variant Validator

Status: Done
Score: 2/2

Goal:
- Enforce renderer projection support through a machine-readable capability matrix and first-class CLI diagnostics.

In Scope:
- Machine-readable capability matrix for diagram x backend support
- Variant-aware validator stage in core run pipeline before renderer dispatch
- Error/warning surfacing contract for unsupported or degraded combinations
- Spec documentation and policy authority reference for capability ownership
- Targeted tests covering matrix rules and CLI-facing failure behavior

Out Of Scope:
- Changing core language semantics
- Re-enabling deprecated Graphviz fallback behavior by default

Done Criteria:
- Matrix exists in code in machine-readable form and is used at runtime
- Unsupported combinations fail early with actionable CLI messages
- Warning/error handling shape is documented and test-covered
- docs/specs and docs/policy mention capability authority and usage

Notes:
- Preferred behavior: explicit unsupported requests fail fast; no silent backend fallback.
- Initial known unsupported pair: swimlane + svg.
- Added machine-readable runtime matrix at src/flo/render/capability_matrix.py.
- Wired early projection validation into core run path before renderer dispatch.
- Added unit coverage for matrix and CLI-facing unsupported projection errors.
- Added docs/specs/render_capabilities.md and policy authority reference.

## Item 2: Layout To Canvas Boundary Contract

Status: Done
Score: 2/2

Goal:
- Freeze the handoff contract between layout output and render consumers.

In Scope:
- Required geometry fields
- Label and anchor semantics
- Ownership boundaries across layout, renderer, and post-process

Out Of Scope:
- Changing ELK algorithms
- Full Typst visual parity

Done Criteria:
- One-page contract drafted
- Required vs optional fields listed
- Ownership and no-leak rules documented

Notes:
- Drafted one-page boundary contract in docs/design/layout_canvas_boundary_contract.md.
- Explicitly set ELK/SVG direct backend as owner of rework branch/return route-shape policy.
- Scoped Graphviz postprocess to compatibility-only behavior (no duplicate rework geometry ownership).

## Item 3: Typst Canvas Vertical Slice

Status: Not Started
Score: 0/2

Goal:
- Prove one real fixture can render through canonical canvas into Typst.

In Scope:
- Primitive mapping for nodes, edges, labels
- Placement and endpoint sanity checks

Out Of Scope:
- Full feature parity
- Multi-view orchestration

Done Criteria:
- One reference fixture renders end to end
- Node placement, edge attachment, and labels look sane
- Any unsupported features documented as follow-ups

Notes:
- _

## Item 4: Post-Processing Hardening

Status: Not Started
Score: 0/2

Goal:
- Make post-processing deterministic, ordered, and idempotent.

In Scope:
- Phase ordering contract
- Before and after snapshots
- Idempotency checks

Out Of Scope:
- Introducing new layout decisions in post-process

Done Criteria:
- Phase order documented
- Deterministic fixtures pass
- Running post-process twice yields same output

Notes:
- _

## Item 5: Migration Readiness Gate

Status: Not Started
Score: 0/2

Goal:
- Decide if we can pivot effort from ELK-heavy tuning toward Typst migration.

Gate Questions:
- Are top 3 arrow-path archetypes stable?
- Is layout-to-canvas contract approved?
- Did one Typst vertical slice pass sanity checks?
- Is post-process deterministic and idempotent?
- Did we avoid new cross-layer coupling?

Done Criteria:
- Explicit Go or No-Go captured
- Next 2-day execution direction listed

Notes:
- _

## Quick Timeline

1. Item 1: 90 min
2. Item 1.5: 75 min
3. Item 2: 60 min
4. Item 3: 90 min
5. Item 4: 45 min
6. Item 5: 15 min

## Live Scoreboard

- Item 1 Arrow Path Stabilization: 2/2
- Item 1.5 Capability Matrix + Variant Validator: 2/2
- Item 2 Layout To Canvas Contract: 2/2
- Item 3 Typst Vertical Slice: 0/2
- Item 4 Post-Processing Hardening: 0/2
- Item 5 Migration Readiness Gate: 0/2

Total: 6/12
