# Render Platform Migration Plan

Status: draft

Plan state: in progress (May 2026)

## Purpose

Define the minimum viable migration path from the current Graphviz-first stack
to the accepted target stack:

- ELK for graph layout where needed
- FLO-owned SVG for standalone graphics
- Typst for true document composition

## Current State

The migration is no longer at proposal-only stage.

Completed so far:

- backend-neutral render artifacts exist in code
- backend selection is explicit in orchestration rather than implied by shared
  Graphviz-shaped helpers
- Graphviz remains available behind a compatibility path for DOT-oriented
  behavior
- Graphviz package and helper entrypoints have been moved toward backend-oriented
  naming, with legacy DOT-facing module names retained as compatibility shims
- a narrow FLO-owned SVG backend exists for spaghetti rendering
- CLI and core export flow now treat `svg` as a first-class output mode
- the direct-SVG spaghetti slice now has focused artifact-contract coverage for
  channel selection, route labels/titles/styles, boundary rendering, location
  shape semantics, missing-spatial failure behavior, and multi-route
  aggregation counts
- focused validation passes across the affected render, core, pipeline, and CLI
  slices

Current phase assessment:

- Phase 0 is complete
- Phase 1 is substantially complete for the initial boundary cut
- Phase 2 has started through the direct-SVG spaghetti slice and first-class
  SVG export semantics
- Phase 3 has started through the first ELK-facing request contract and the
  first backend-neutral final-geometry result contract in `layout_core`
- the ELK foundation now includes a normalizer from ELK-style response payloads
  into the backend-neutral `LayoutResult` contract, plus request builders for
  both `swimlane` and `flowchart`
- the ELK seam is now executable in tests through a request serializer and a
  thin injected-engine adapter function, without committing the codebase to a
  specific ELK runtime yet
- the first diagram-specific ELK caller now exists as a swimlane adapter
  entrypoint that owns `process -> request -> engine -> LayoutResult`
- the next runtime slice adds a concrete `elkjs`-backed Node wrapper plus a
  stable ELK engine error contract for unavailable runtime, subprocess failure,
  timeout, and invalid payload/response cases
- the first ELK-backed FLO-owned SVG flowchart slice now exists as a minimal
  direct-SVG backend consuming `LayoutResult`
- later Phase 3 ELK adapter work remains future work

Current working interpretation:

- DOT is now a legacy and compatibility artifact, not the target architectural
  center
- SVG is the canonical standalone graphics artifact
- PDF remains the canonical composed publication artifact once Typst
  composition lands
- `layout_core` now contains the start of the request/result seam needed for
  ELK-backed graph families without forcing ELK response shapes directly into
  renderer code

## Migration Principles

- no flag day rewrite
- preserve current CLI behavior while new paths stabilize
- keep Graphviz available as fallback until per-diagram parity exists
- move contracts before moving all implementations
- treat publication composition as a separate concern from layout

## Immediate Execution Plan: Boundary-Freeze Day

This section records the boundary-freeze execution plan that launched the
refactor. Its core objectives have now been met and should be treated as the
completed foundation for the next slices.

### Goal

Make the codebase structurally ready for the refactor without trying to land
ELK, FLO SVG, Typst composition, and package reorganization all at once.

Status:

- complete for the initial cut
- follow-on work should build on these seams rather than reopen Graphviz-first
  shared abstractions

### Priority Order

1. normalize all project automation and developer commands through `uv`
2. introduce backend-neutral render contracts in code
3. separate render intent from backend execution
4. isolate Graphviz behind an explicit legacy adapter boundary
5. stand up one narrow FLO-owned SVG path
6. preserve publication composition as a separate lane rather than extending
   DOT-driven behavior further

### Concrete Work For Today

#### 1. Finish toolchain normalization

Outcome:

- hooks, scripts, and routine developer commands resolve through `uv`
- no important workflow depends on ambient interpreter selection

Work:

- replace remaining bare `python` or tool invocations in repo automation with
  `uv run ...`
- update any stale developer-facing command examples that still imply ambient
  interpreter selection

Current state:

- repository automation for the affected quality gates has been normalized
  through `uv`
- the radon complexity hook mismatch was resolved by running it through `uv`

#### 2. Freeze the backend-neutral contracts

Outcome:

- future ELK, Graphviz, and SVG work hang off the same internal seams

Work:

- define small render-platform contracts such as `DiagramDocument`,
  `LayoutRequest`, `LayoutResult`, and `GraphicAsset`
- keep these contracts intentionally narrow and backend-neutral
- avoid encoding DOT or Graphviz assumptions into the contract names or fields

Current state:

- the implemented seam is currently centered on render artifacts and explicit
  backend selection rather than the fuller contract family named here
- this is sufficient for the migration stage and should be extended only when a
  concrete next backend needs the added abstraction

#### 3. Split intent from execution

Outcome:

- orchestration can choose a diagram family and rendering path without sharing
  backend-specific details across the stack

Work:

- move high-level render selection into a backend-neutral orchestration layer
- move DOT-specific lowering behind a Graphviz adapter boundary
- stop letting shared render assembly functions decide both semantics and DOT
  syntax in the same step

Current state:

- core and pipeline flow can now request render artifacts without assuming DOT
  output as the only meaningful result
- compatibility helpers still exist, but they no longer define the target
  direction of the platform

#### 4. Stand up a first non-Graphviz slice

Outcome:

- the new architecture is proven by one executable path rather than only by
  scaffolding

Work:

- implement one narrow direct-SVG path
- prefer spaghetti as the first slice because it depends more on explicit
  spatial semantics than on graph layout

Current state:

- complete for the first proving slice
- spaghetti has a narrow direct-SVG backend for explicit spatial inputs
- `--export svg` is now a first-class CLI-visible path for that slice

#### 5. Hold the line on publication scope

Outcome:

- page composition stays a separate concern while diagram rendering contracts
  stabilize

Work:

- keep publication planning distinct from standalone graphic generation
- avoid adding new DOT-era pagination or page-furniture logic to shared render
  code

Current state:

- still in force
- no new shared pagination or DOT-era document-composition logic should be
  added while SVG and layout migration continue

### Stop Line For The Day

Today is successful if all of the following are true:

- `uv run pre-commit run --all-files` passes
- backend-neutral render contracts exist in code
- Graphviz is behind an adapter seam rather than serving as the organizing
  abstraction for new work
- one narrow SVG-backed path exists
- no newly introduced shared code depends on Graphviz-specific concepts

Observed result:

- this stop line has been met for the initial migration cut

## Backend Selection Guidance

FLO does not need a broad plugin-style backend registry yet.

### Recommended near-term approach

Use an explicit in-repo backend selection layer with a small, closed mapping.

That means:

- diagram families choose from a small number of known backends
- orchestration code calls a backend-neutral adapter interface
- per-family defaults stay explicit in code rather than being dynamically
  discovered

This is enough for the migration period and keeps control flow legible.

### Why not introduce a full registry now

A true backend registry becomes valuable when FLO has several active backends,
runtime-pluggable selection, or an external extension story.

Those are not today’s problems.

Today’s risk is not "insufficient indirection". Today’s risk is letting shared
render code stay Graphviz-shaped while pretending a registry solved the design.

### What to build now instead

Build a small backend selector or factory with explicit choices such as:

- Graphviz legacy adapter
- direct SVG adapter for migrated diagram families
- later, an ELK-backed layout adapter feeding the SVG renderer

If the number of backends or selection rules grows materially, that selector
can later be promoted into a formal registry without changing the core
contracts.

## Phase 0: Freeze The New Boundaries

Status: complete

Outcome:

- architecture decision recorded
- target contracts named
- migration sequence agreed before further Graphviz-specific expansion

Work:

- adopt the accepted stack described in the ADR
- stop adding new shared abstractions that are Graphviz-shaped by default
- route new publication concerns toward shared publication contracts, not DOT
  postprocessing

## Phase 1: Extract Backend-Neutral Contracts

Status: mostly complete for the first migration cut

Outcome:

- current renderers still work
- code gains explicit seams for later backend replacement

Work:

- introduce backend-neutral diagram model contracts
- introduce layout request/result contracts
- isolate Graphviz-specific service code behind a backend adapter boundary
- stop referring to rendering as only "DOT emission" in high-level orchestration

Suggested first refactors:

- rename current Graphviz-specific helpers to live behind a Graphviz backend
  namespace
- add a standalone `GraphicAsset` contract next to the existing publication
  model
- keep the existing `PublicationPlan` family but make it reference graphic
  assets instead of backend-specific assumptions

Exit criteria:

- pipeline and core orchestration can talk about diagram artifacts without
  assuming DOT as the only intermediate

Current state:

- met for the current artifact seam
- further cleanup should reduce remaining Graphviz-oriented naming and module
  boundaries without reopening the contract shape unnecessarily
- one live shared-helper implementation has already been moved behind a
  backend-oriented implementation name, with DOT-era module paths preserved as
  compatibility shims during migration

## Phase 2: Build FLO SVG Emission

Status: in progress

Outcome:

- FLO can emit standalone SVG without Graphviz for at least one slice

Work:

- implement SVG emission from final geometry
- standardize text, markers, arrows, and reusable style tokens
- add image fixture tests around emitted SVG structure and dimensions

Recommended first adopter:

- spaghetti map

Reason:

- spaghetti already has strong analysis/render separation
- many spaghetti layouts are driven by explicit spatial metadata
- Graphviz adds less unique value here than it does for graph-structured views

Exit criteria:

- spaghetti can emit standalone SVG directly from FLO
- PNG and PDF can be derived from SVG without Graphviz-specific geometry

Current state:

- the first exit criterion is partially met for the explicit-spatial spaghetti
  slice
- SVG export is first-class in CLI/core semantics
- the direct-SVG spaghetti backend now has meaningful artifact-contract tests
  for both happy-path and failure-path behavior
- image-fixture depth, broader per-family SVG coverage, and downstream SVG to
  PNG/PDF derivation remain open work

## Phase 3: Add ELK For Graph-Like Diagram Families

Status: not started

Outcome:

- at least one graph-structured diagram family uses ELK-backed layout

Work:

- add an ELK adapter behind the layout contract
- map flowchart and swimlane diagrams onto ELK-friendly layout requests
- preserve stable semantic IDs through layout and SVG emission
- compare route quality against current Graphviz outputs with focused fixtures

Recommended first adopter:

- swimlane or flowchart

Reason:

- these diagrams are more purely graph-layout problems than SPPM publication

Exit criteria:

- one graph-structured renderer reaches acceptable parity without Graphviz
- Graphviz remains available as a fallback for non-migrated families

## Phase 4: Introduce Typst Composition

Status: not started

Outcome:

- FLO can produce a real composed publication document without asking the
  diagram backend to paginate by itself

Work:

- define `PublicationPlacement` references to standalone SVG assets
- emit Typst source from publication plans
- standardize page templates for header, footer, caption, figure body, and
  continuation references
- keep standalone figure output available alongside document output

Recommended first adopter:

- SPPM publication mode

Reason:

- SPPM already carries publication semantics that exceed single-graphic output

Exit criteria:

- SPPM can emit a composed publication artifact in addition to standalone
  graphics
- page breaks are driven by publication rules rather than DOT surgery

## Phase 5: Reduce Graphviz To Legacy Status

Status: not started

Outcome:

- Graphviz is no longer the default architectural center

Work:

- switch default backend per diagram family once parity is demonstrated
- retain Graphviz only where it remains materially better or migration is not
  yet justified
- delete Graphviz-only postprocessing that no longer serves an active path

Exit criteria:

- new renderer work targets backend-neutral contracts first
- Graphviz is an adapter, not the organizing abstraction for render code

## Recommended Order By Diagram Family

1. Spaghetti: direct SVG first
2. Flowchart or swimlane: ELK plus SVG next
3. SPPM publication: Typst composition after shared contracts and SVG exist

This order avoids using SPPM as the proving ground for every new abstraction at
once.

## Next Slices

The next implementation work should stay adjacent to the code already moved.

Priority order:

1. deepen SVG validation for the spaghetti path from focused contract tests
  toward richer fixture-style artifact coverage
2. reduce the remaining Graphviz leakage in legacy implementation module names
  where the migration value is still worth the churn
3. choose the first ELK candidate between flowchart and swimlane, then define
  the minimal layout contract expansion required for that slice
4. continue treating SPPM publication and Typst composition as a separate lane
  until SVG and layout contracts are more stable

## Validation Strategy

Each migration phase should preserve both behavior and artifact quality.

Required validation surfaces:

- unit tests for contracts and geometry helpers
- fixture-based artifact comparisons for SVG structure
- focused regression fixtures for routing and continuation behavior
- publication fixture tests for page counts, repeated furniture, and figure
  placement

## Risks

### Risk: overfitting the platform to SPPM first

Mitigation:

- prove direct SVG on spaghetti and ELK on a graph-like renderer before asking
  SPPM to validate the whole stack

### Risk: replacing Graphviz too early

Mitigation:

- keep Graphviz as fallback until parity is measured rather than assumed

### Risk: rebuilding a compositor inside FLO anyway

Mitigation:

- keep page composition responsibilities in Typst
- keep FLO focused on semantic diagrams, assets, and publication plans

## References

- `docs/design/adr_render_stack_elk_svg_typst.md`
- `docs/design/render_platform_target_architecture.md`
- `docs/design/publication_model.md`
