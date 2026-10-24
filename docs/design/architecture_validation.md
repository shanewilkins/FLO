# Architecture validation: White Belt candidate

Status: R1–R4 complete; all identified architecture findings closed. Candidate accepted; release cut pending.
Review date: 2026-10-24. Governing release requirement: TR-118.

## Current disposition

| Finding | Disposition | Enforced boundary |
| --- | --- | --- |
| AF-001: placement during SVG emission | Closed by R3a/R3b | RoutedGeometry and FinalScene precede emission; SVG modules cannot depend transitively on layout, attachment, or annotation policy; supplied-scene and disabled-policy tests verify actual consumption |
| AF-002: SPPM policy in neutral core | Closed by R2 | Neutral execution consumes explicit settings/transform; all core modules are scanned; independent-diagram and environment invariance tests pass |
| AF-003: duplicated golden pipeline | Closed by R1 | Golden generation calls public execution once; consumer imports and call-through tests prohibit rebuilding stages |

The [historical assessment](architecture_validation_history.md) preserves initial
findings and milestone evidence. It does not describe unresolved current drift.
The [machine evidence](architecture_validation_evidence.json) describes its recorded
candidate, with runtime/configuration/decision hashes and actual stage observations.
The [candidate acceptance record](white_belt_candidate_acceptance.md) records matching clean Linux/macOS installed-platform results and artifact identities.

## Effective architecture review

The accepted decisions are the [four-package architecture](adr/simplified_package_architecture.md),
[render stack](adr/render_stack_elk_svg_typst.md), [renderer boundaries](renderers/boundaries.md),
[SPPM design](renderers/sppm.md), and [layout finalization clarification](adr/render_layout_finalization.md).
The later sections explicitly marked Proposed in the target architecture remain future sketches.

| Subsystem | Current implementation and review |
| --- | --- |
| process | Canonical IR, validation, duration/timing analysis, export contracts. Inward dependency and private-module checks pass. Timing preserves measured zero versus unknown; canonical IR is unchanged by rendering. |
| source | Parse/compile adapters and source diagnostics depend inward on process/leaf contracts, never rendering or application. Semantic fixtures protect normalization and diagnostics. |
| render | Four independent diagram packages, one registry, neutral layout/viewport/contracts, SVG artifacts and separate Typst composition. No Graphviz or browser product runtime. |
| app and public API | Compose source/domain/render operations and own CLI delivery. Root API is a facade, not a fifth substantive package. Repeated validation composition is nonblocking debt with parity tests, not a boundary waiver. |
| optional mining | PM4Py is absent from core/runtime requirements; optional integration remains deliberately deferred, not a current obligation to create a bridge. |
| diagnostic delivery | Existing source/analysis/render diagnostics remain explicit. Unified delivery is separately committed next-sprint TR-117, not falsely claimed by this refactor. |
| publication | Page planning and Typst composition remain separate from figure layout. Full multi-page/child-map acceptance is deferred to its belt gate. |

Broad Any annotations, mutable diagnostic metadata, and existing size/complexity
exclusions were reviewed as debt rather than assumed architecture violations.
None authorizes violating ownership or data flow. Removed core/edge length
exemptions were retired, not transferred to extracted files.

## Production stage contract

1. Public rendering calls one `render_execution` sequence, preserving the existing
   artifact and artifact/contract return APIs.
2. The registry invokes diagram-owned option preparation. SPPM converts requested
   width to its wrap budget in `sppm.layout_options`, not in neutral viewport code.
3. SPPM projects/measures/builds an ELK request. Neutral execution serializes its
   supplied settings, runs the engine, normalizes coordinates, and invokes only
   the explicitly supplied diagram transformation.
4. `finalize_sppm_geometry` produces immutable routed node/edge/lane/canvas/group
   mappings without changing the engine result.
5. `finalize_sppm_scene` produces attached connector points, labels/callouts/tokens,
   annotation boxes and text baselines, occupied annotation bounds, diagnostic
   outcomes, publication band positions, natural SVG dimensions, and content origin.
6. `sppm.svg` / `edge_svg` serialize supplied geometry with paint and typography.
   Node primitives format glyphs/card internals inside supplied bounds; they do not
   move process nodes or run inter-element placement/collision policy.
7. Shared viewport resolution applies generic requested dimensions, expansion,
   scaling, and the documented 0.75 safe-fit floor. Numeric results are explicit in
   artifact metadata; optional capture exposes engine, routed, and final scene stages.

Explicit layout-only and precomputed-route helpers are named intermediate stages.
Page-local publication figures call the diagram pipeline with planner-owned figure
options. Private `edges.py` route/token adapters serve stage-level tests and are
excluded from the production emitter's enforced dependency tree.

## Executable evidence

- Eleven Import Linter contracts enforce package direction, renderer independence,
  neutral-core independence, acyclic packages, and pure-emitter dependencies.
- Policy tests require classification of new render modules and prevent contract
  exemptions/removal. Fresh-package tests exercise real bad imports.
- Source responsibility probes cover all neutral modules and current emitters.
  They detect known policy symbols, tags, reserved IDs, and environment keys;
  semantic review remains necessary for arbitrarily hidden policy.
- Supplied-scene tests alter connector points, annotation positions, bounds, and
  group membership, then disable policy functions while emitting. Output consumes
  the supplied values. Strict diagnostics fail during finalization.
- All 13 cases / 26 golden files retain byte parity. Independent SVG shape,
  attachment, orthogonality, overlap, annotation, lane, canvas, accessible-name,
  theme/non-color, and physical-unit/fit checks remain separate from goldens.
- Three representative inputs exercise Python, actual CLI, golden generation,
  installed CLI, repeated output, and full IR preservation. The trace observes
  calls during actual emission instead of assuming zero from a scene object.
- Browser consumer checks measure actual glyph bounds and fit scale over the
  release corpus on Linux/macOS; JSON and wheel/trace identities are retained.

## Candidate acceptance (R4)

The [candidate acceptance record](white_belt_candidate_acceptance.md) closes R4.
Clean CI passed 1,234 tests with 93.72% coverage, all quality/boundary gates,
13-case golden/geometry/accessibility checks, installed-wheel identity and journeys
on Linux/macOS, and actual Chrome glyph/fit measurements on both platforms.
All 643 text elements per platform pass; no clipping or unsafe-fit issue remains.

The record distinguishes the immutable source revision from GitHub's tested merge
revision and retains wheel, runtime, decision/configuration, and SVG identities.
R4 accepts the reviewed candidate architecture; it does not create a release tag
or publish a distribution. The eventual versioned release must satisfy the policy
and record its tag before it becomes the next cycle's published baseline.
