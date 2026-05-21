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