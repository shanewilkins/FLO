# Render Platform Migration Plan

Status: proposed implementation plan (May 2026)

## Purpose

Define the minimum viable migration path from the current Graphviz-first stack
to the accepted target stack:

- ELK for graph layout where needed
- FLO-owned SVG for standalone graphics
- Typst for true document composition

## Migration Principles

- no flag day rewrite
- preserve current CLI behavior while new paths stabilize
- keep Graphviz available as fallback until per-diagram parity exists
- move contracts before moving all implementations
- treat publication composition as a separate concern from layout

## Immediate Execution Plan: Boundary-Freeze Day

This is the recommended battle plan for the next implementation session now
that the design direction is locked.

### Goal

Make the codebase structurally ready for the refactor without trying to land
ELK, FLO SVG, Typst composition, and package reorganization all at once.

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

#### 2. Freeze the backend-neutral contracts

Outcome:

- future ELK, Graphviz, and SVG work hang off the same internal seams

Work:

- define small render-platform contracts such as `DiagramDocument`,
  `LayoutRequest`, `LayoutResult`, and `GraphicAsset`
- keep these contracts intentionally narrow and backend-neutral
- avoid encoding DOT or Graphviz assumptions into the contract names or fields

#### 3. Split intent from execution

Outcome:

- orchestration can choose a diagram family and rendering path without sharing
  backend-specific details across the stack

Work:

- move high-level render selection into a backend-neutral orchestration layer
- move DOT-specific lowering behind a Graphviz adapter boundary
- stop letting shared render assembly functions decide both semantics and DOT
  syntax in the same step

#### 4. Stand up a first non-Graphviz slice

Outcome:

- the new architecture is proven by one executable path rather than only by
  scaffolding

Work:

- implement one narrow direct-SVG path
- prefer spaghetti as the first slice because it depends more on explicit
  spatial semantics than on graph layout

#### 5. Hold the line on publication scope

Outcome:

- page composition stays a separate concern while diagram rendering contracts
  stabilize

Work:

- keep publication planning distinct from standalone graphic generation
- avoid adding new DOT-era pagination or page-furniture logic to shared render
  code

### Stop Line For The Day

Today is successful if all of the following are true:

- `uv run pre-commit run --all-files` passes
- backend-neutral render contracts exist in code
- Graphviz is behind an adapter seam rather than serving as the organizing
  abstraction for new work
- one narrow SVG-backed path exists
- no newly introduced shared code depends on Graphviz-specific concepts

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

## Phase 2: Build FLO SVG Emission

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

## Phase 3: Add ELK For Graph-Like Diagram Families

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