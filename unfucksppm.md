# Unf*** SPPM Render Plan

## Objective
Restore SPPM rendering to stable, semantically correct, and visually readable output.
Prevent future regressions where tests pass but diagrams look wrong.

## Success Definition
The SPPM renderer produces consistent geometry across the canonical corpus.
Branch and return semantics are visually clear in both LR and TB orientations.
CI blocks merges that regress SPPM geometry or visual baselines.

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

## Phase 4: Stabilization Implementation
### Purpose
Apply the selected strategy profile to production SPPM rendering paths.

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
Create the canonical corpus manifest and generation command.
Implement the first three invariants and failing test fixtures.
Build the strategy matrix runner and initial scoring report.
