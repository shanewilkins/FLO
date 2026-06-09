# Unf*** SPPM Render Plan

## Objective
Restore SPPM rendering to stable, semantically correct, and visually readable output.
Prevent future regressions where tests pass but diagrams look wrong.

## Success Definition
The SPPM renderer produces consistent geometry across the canonical corpus.
Branch and return semantics are visually clear in both LR and TB orientations.
CI blocks merges that regress SPPM geometry or visual baselines.

## Status Snapshot (2026-06-09)
Phase 1 is complete.
Phase 2 is complete.
Phase 3 is complete.
Phase 3.5 is complete.
Phase 4 is in progress.
Phase 4.5 is planned.

Evidence for Phase 1 baseline lockdown exists in the corpus manifest and deterministic artifact outputs.
Manifest: `examples/conformance/sppm_corpus.json`.
Baseline artifact roots: `renders/conformance/sppm_baseline/` and `renders/conformance/valid/`.
Rebuild commands are versioned in `scripts/build_sppm_baseline_artifacts.py` and `scripts/build_all.py`.

Evidence for Phase 2 invariant coverage exists in the strategy harness invariant checks.
Invariant families are implemented in `scripts/run_sppm_strategy_matrix.py` as mainline progression, rework separation, rework attachment assertions, determinism hash stability, node overlap exclusion, lane containment, and edge-through-node exclusion.
Current canonical matrix run reports zero invariant failures across all 36 profiles.

Evidence for Phase 3 strategy matrix scoring exists in machine-readable and markdown scoreboards.
Artifacts: `renders/conformance/sppm_strategy_matrix/scoreboard.json` and `renders/conformance/sppm_strategy_matrix/scoreboard.md`.
Secondary scorecard metrics are now included: weighted edge crossings, p95 bends, p95 edge length, average bend count, average routed edge length, and average canvas area.
Current top profile under invariant-first plus secondary tie-break ordering is `part=chain_progressive|port=fixed_order|anchors=off|space=balanced`.
Current top profile scores are 10/10 passed cases, 0 failed cases, 0 invariant failures, avg_weighted_crossings=0.20, avg_p95_bends=2.48, avg_p95_edge_length_px=903.63, avg_bends=7.00, avg_edge_length_px=2909.15, and avg_canvas_area_px2=769681.50.

## Phase 1: Baseline Lockdown
### Purpose
Create a reproducible baseline so every future change can be measured.

### Work
Build a canonical SPPM corpus with 8 to 12 representative .flo inputs.
Include linear flows, single rework loops, multi-branch rework, nested rework, long labels, and stress cases.
Export artifacts per case as ELK request JSON, ELK response JSON, normalized geometry JSON, and SVG.
Add a single command that regenerates all artifacts deterministically.

### Acceptance Criteria
A fixed corpus list exists in version control and is used by all SPPM checks.
Running one command regenerates every baseline artifact with no manual steps.
The command succeeds locally on a clean checkout using uv run.
Artifact outputs are byte-stable across two consecutive runs on the same machine.

## Phase 2: Invariant Test Layer
### Purpose
Convert visual quality expectations into objective geometry checks.

### Work
Add SPPM geometry invariant tests on normalized layout output.
Enforce monotonic mainline progression in the primary direction.
Enforce rework-row separation from mainline for synthetic-row cases.
Enforce branch edge departure near the declared branch source.
Enforce return edge reconnection near the intended upstream target.
Add tolerance windows for ELK coordinate jitter where needed.

### Acceptance Criteria
Invariant tests fail on known broken layouts and pass on accepted baselines.
Each invariant has at least one positive and one negative test case.
Invariant failures report the violated rule, node or edge IDs, and measured values.
No invariant depends on pixel snapshots to pass.

## Phase 3: Strategy Matrix Harness
### Purpose
Stop guesswork by evaluating layout strategies systematically.

### Work
Introduce internal strategy switches for partition mode, port constraints, helper anchors, and spacing profile.
Run the full corpus across the strategy matrix and score each run against invariants.
Produce a machine-readable scoreboard and a markdown summary table.
Select one winning strategy profile based on highest invariant pass rate and minimal visual anomalies.

### Acceptance Criteria
At least four strategy dimensions are configurable without code edits per run.
A single command runs the matrix and emits a reproducible scoreboard.
The selected profile has zero invariant failures on the canonical corpus.
The selection rationale is documented with explicit tradeoffs.

## Phase 3.5: Render Diagnostics and Structural Guardrails
### Purpose
Stop ambiguous render state from degrading silently into hard-to-debug geometry bugs.

### Work
Add unified render-namespace validation before ELK request serialization for node IDs, lane IDs, helper IDs, and reserved renderer-owned IDs.
Raise a hard error on lane/node or helper/user ID collisions instead of allowing ambiguous ELK child graphs.
Introduce structured render diagnostics for lossy fallback and partial recovery paths using warning or error severity.
Warn or fail when normalized ELK output drops requested edges, yields unknown edge containers, or cannot resolve expected edge geometry.
Warn when route planning or port assignment omits edges because placement metadata is incomplete or inconsistent.
Review reserved synthetic IDs such as `unassigned` and either namespace them or validate them explicitly against user-defined IDs.
Decide which render-time conditions are always fatal versus warning-only under a strict diagnostics mode.

### Failure Mode Map
Failure mode: namespace ambiguity in ELK-visible IDs (node, lane, helper, reserved synthetic IDs).
Surface: hard `RenderError` from request validation before ELK execution.
Matrix gate: request build must succeed for every case/profile.

Failure mode: missing normalized geometry (missing requested edges, missing lane frames, unresolved endpoints, unusable edge geometry).
Surface: structured diagnostics under `missing_geometry` category.
Matrix gate: zero diagnostic errors and zero `partial_output` cases.

Failure mode: lossy normalization fallback (unknown edge container, unexpected edges, publication fallback).
Surface: structured diagnostics under `lossy_recovery` category.
Matrix gate: zero `partial_output` cases.

Failure mode: advisory-only recovery notes that do not compromise geometry.
Surface: structured diagnostics under `uncategorized` category when not mapped to geometry-loss classes.
Matrix use: secondary warning-burden tiebreak only, not a hard invariant.

Failure mode: strict-mode escalation paths for diagnostics that are warning in normal mode.
Surface: strict diagnostics convert selected recovery diagnostics into `RenderError` at execution boundary.
Matrix gate: no strict-mode errors for profiled corpus settings.

### Matrix Additions
Primary invariants now include diagnostics cleanliness.
Invariant: zero diagnostic errors per case.
Invariant: zero `partial_output` per case.

Secondary scorecard now includes diagnostic warning burden and diagnostic warning counts.
Warning burden weights: `missing_geometry` > `lossy_recovery` > `uncategorized`.
Tie-break uses diagnostic warning burden before geometric quality metrics.

### Acceptance Criteria
Render preparation fails fast on cross-namespace ID collisions with an error that names the conflicting IDs and object kinds.
Render normalization emits structured diagnostics for dropped edges, unknown containers, and other partial-recovery conditions.
At least one strict-mode path can convert selected render warnings into errors for debugging and CI.
The lane/node collision class that affected SPPM cannot recur silently.
The diagnostics contract is documented with clear examples of warning versus error cases.
The strategy matrix includes diagnostics-based invariants and warning-burden secondary scoring.

## Phase 4: Stabilization Implementation
### Purpose
Apply the selected strategy profile to production SPPM rendering paths.

### Kickoff Status (2026-06-09)
Production default strategy is now frozen to `part=chain_progressive|port=fixed_order|anchors=off|space=balanced`.
Phase 4 now focuses on policy centralization cleanup, artifact validation, and CI hardening around the frozen profile.

### Work
Refactor SPPM layout code to centralize strategy application in one module.
Remove or gate ad hoc behavior that conflicts with the selected profile.
Align partition assignment, helper anchor insertion, and port constraints with the chosen policy.
Update unit tests to assert policy behavior directly.
Regenerate reference artifacts after implementation.

### Acceptance Criteria
SPPM production path uses exactly one default strategy profile.
All SPPM unit and integration tests pass under uv run pytest.
All SPPM invariant tests pass for LR and TB orientation samples.
Reference artifact diff is reviewed and limited to expected changes.
No new complexity gate failures are introduced.

## Phase 4.5: ELK-Native Geometry and Post-Process Boundaries
### Purpose
Minimize post-processing by making ELK and normalization the authoritative source of SPPM geometry.
Ensure post-process behavior is narrow, diagnosable, and non-semantic.

### Architectural Decisions
ELK-native layout owns semantic geometry.
Semantic geometry includes row separation, branch and return anchor alignment intent, partition assignments, and edge attachment side intent.

Normalization owns geometry fidelity checks and render diagnostics.
Normalization validates requested versus produced nodes, lanes, and edges, and emits structured diagnostics before any SVG-only adjustments.

Post-process owns only deterministic presentation refinement.
Refinement includes shape-boundary clipping for rendered edge endpoints, bounded non-overlapping annotation placement, and canvas-safe clamping.
Post-process must not redefine semantic routing intent or reorder semantic node placement.

Any post-process correction that materially changes route topology is a design bug.
Such cases must become ELK request-shaping or normalization fixes, not permanent post-process patches.

### Diagnostics Contract for Post-Process
Add a dedicated post-process diagnostic stage after normalized `LayoutResult` and before SVG emission.
Emit diagnostics for endpoint shape miss distance, annotation overlap with nodes or labels, row-gap minimum violations, and branch or return alignment deltas.

Severity policy is strict.
Topology loss remains error-level diagnostics.
Presentation degradation remains warning-level diagnostics by default and can escalate under strict mode.

Diagnostics must include stable machine-readable metadata.
Metadata fields include `edge`, `node`, measured values, thresholds, and applied fallback decisions.
These diagnostics feed matrix invariants where appropriate and warning-burden secondary scoring otherwise.

### Work
Implement edge endpoint clipping against actual rendered shapes in direct SVG SPPM.
Use queue triangle, decision diamond, rounded rectangle, and subprocess ellipse boundary intersection logic.

Activate existing secondary-row alignment pass in the direct SVG path, then constrain it to presentation-safe transforms only.
Add explicit min-gap policy between mainline and rework rows and report violations through diagnostics.

Replace branch-only rework partition anchoring with branch-plus-return anchoring in ELK request shaping.
Branch targets align to branch-source partition intent, and return-source tasks align to return-target partition intent.

Upgrade annotation placement search from local offsets to bounded multi-candidate segment search.
When unresolved overlap persists, emit diagnostics and deterministic fallback placement rather than silent collision.

### Acceptance Criteria
Queue and decision edge attachments terminate on rendered shape boundaries with no visible floating endpoints in reference SPPM artifacts.
Mainline and rework rows satisfy a configured minimum vertical separation on canonical SPPM cases.
Known showcase rework alignment expectations are met: rework queue under branch decision and rework task under reintegration target where semantically intended.
Rework loop labels and callouts avoid node overlaps in canonical reference renders or emit explicit diagnostics when fallback is used.
No post-process step changes semantic route topology without a corresponding diagnostics error.

### Implementation Order
Step 1: shape-boundary endpoint clipping plus focused unit tests.
Step 2: activate and constrain secondary-row presentation alignment plus row-gap diagnostics and invariants.
Step 3: implement branch-plus-return partition anchoring in ELK request shaping.
Step 4: harden annotation placement with overlap diagnostics and deterministic fallback policy.
Step 5: regenerate reference artifacts, review SPPM diffs, and lock accepted baselines.

## Phase 5: Regression Gates and CI Enforcement
### Purpose
Make SPPM quality self-defending in CI.

### Work
Add invariant test suite to CI as a required check.
Add baseline artifact drift detection for canonical cases.
Fail CI when geometry invariants fail or approved baselines drift unexpectedly.
Document update procedure for intentional baseline changes.

### Acceptance Criteria
CI blocks merges on SPPM invariant failure.
CI blocks unexpected baseline drift for canonical SPPM artifacts.
The documented baseline update workflow is tested end to end once.
A contributor can follow docs and successfully perform an intentional baseline update.

## Phase 6: Controlled Improvement Loop
### Purpose
Enable safe future iteration after stabilization.

### Work
Open improvements one at a time behind temporary strategy flags.
Require each improvement to add or update invariants before merge.
Review visual diffs and invariant score changes as part of PR review.
Remove temporary flags only after two successful cycles without regressions.

### Acceptance Criteria
Each improvement PR includes invariant impact notes and artifact diff summary.
No merged improvement introduces unresolved invariant regressions.
Temporary flags are retired according to the documented policy.
SPPM rendering remains stable for two consecutive release cycles.

## Operating Rules
No SPPM layout change ships without invariant coverage.
No spacing or port behavior tweak ships without corpus diff review.
No helper-node behavior change ships without branch and return semantics validation.

## Immediate Next Actions
Refactor remaining SPPM layout entry points to consume the centralized strategy policy module only.
Execute Phase 4.5 step 1 and step 2 with focused diagnostics-first tests before any further strategy tuning.
Run full SPPM tests against the frozen profile and confirm zero diagnostic invariant regressions.
Regenerate and review reference SPPM artifacts, then document accepted diffs for Phase 4 closure.
