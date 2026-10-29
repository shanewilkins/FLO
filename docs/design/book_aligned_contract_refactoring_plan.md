# Book-Aligned Contract Refactoring Plan

## Status

Complete; accepted 2026-10-29. All six phases and the twelve acceptance
criteria below are verified. The final full-suite checkpoint is **2429 passed,
no failures or skips**, with seven existing Click deprecation warnings.

The [book-aligned specification](../specs/book_aligned_contract.md) owns the
contract. The [failure ledger](book_aligned_refactor_failure_ledger.md) owns
case-level dispositions and current verification results.

| Checkpoint | Disposition |
| --- | --- |
| Phase 1 contract and fixture evidence | Verified within its listed scope; terminology mapping and evidence-preservation test recorded below. |
| Phase 2 contract infrastructure | Verified within its listed scope; typed canonical entities, method restrictions, stable diagnostic categories and schema drift gate present. |
| Phase 3 semantics and consumers | Complete. Exhaustive applicability and field inventory gates, process-only collections, relation evidence validation, consistent timing presentation and entity-name resolution are verified. |
| Phase 4 compatibility removal | Complete: strict source spellings, no attrs/endpoint aliases, no constructor or renderer compatibility paths, current diagnostics. |
| Phase 5 simplification | Complete: shared local contracts, focused domain validators, canonical projections and measured source reduction. |
| Phase 6 acceptance | Complete: current documentation, boundary/schema gaps and all twelve criteria audited; evidence below. |
| Full suite | **0 failed, 2429 passed** at final acceptance; **0 failed, 2366 passed** at phases 4–5 closeout (2026-10-29); Phase 3 checkpoint was 0 failed, 2346 passed; failure-recovery checkpoint was 0 failed, 1966 passed; prior movement export checkpoint was 44 failed, 1916 passed; duration display checkpoint was 47 failed, 1913 passed; publication checkpoint was 52 failed, 1908 passed; D-004 checkpoint was 56 failed, 1904 passed; D-003 checkpoint was 56 failed, 1827 passed; recovery checkpoint was 73 failed, 1726 passed; initial checkpoint was 89 failed, 1686 passed. |

Checkboxes record a specific implementation obligation and its scoped evidence.
They do not imply that every consumer works or that the integrated refactor is
complete. Later-phase edits made before this reconciliation do not waive earlier
prerequisites. The final acceptance matrix below records integrated evidence;
the ledger retains the completed failure-recovery evidence.

This plan implements the decision recorded in
[Book-Aligned Language Conventions](./adr/book_aligned_language_conventions.md).
FLO is pre-1.0 and currently has one user, so this is an intentional breaking
change. The migration must not preserve retired names through aliases,
translation layers, or compatibility models.

## Objectives

In priority order:

1. Make FLO terminology and semantics match the modern process-improvement
   book.
2. Replace overlapping hand-written contracts with strict Pydantic boundary
   models and generated schemas.
3. Repair the known semantic correctness gaps using those contracts.
4. Reduce bespoke validation and improve authoring ergonomics without moving
   graph or analytical semantics into Pydantic.

The primary measure of success is semantic correctness, not line-count
reduction. The codebase may grow temporarily while contracts and tests are
migrated, but the completed design should remove more compatibility,
normalization, and duplicate-validation code than it adds.

## Language Decisions

### Timing vocabulary

- `cycle_time` is active processing time.
- `wait_time` is waiting before work or an explicit waiting state.
- `changeover_time` is setup or changeover time.
- Process `lead_time` is supplied observed, planned, or target evidence.
- `modeled_lead_time` is a derived analytical result and is never an authored
  step field.

Retired terms:

- `wait_before`
- `crossover_time`
- `transfer_time`
- node-level `lead_time`
- `sla_target_seconds`
- timing values nested under `metadata`

### Value classification

- Only work steps have `value_class`.
- Supported values are `VA`, `RNVA`, `NVA`, and explicit `unknown`.
- Omission means unclassified and remains distinct from explicit `unknown`.
- Processes and control nodes do not have a value classification.

### Measurement evidence

Measurements use profiles with:

- `basis`
- named `results`
- `primary`
- optional `analysis_input`
- optional observation count and unit
- optional cohort, aggregation, window, evidence reference, and extensions

Analyses use the named `analysis_input`. Renderers use `primary` unless a
specific view defines another presentation rule.

### Waiting projections

A queue may project a work step's declared waiting evidence:

```yaml
wait_time:
  ref: wash.wait_time
```

The queue is a reference, not a second copied measurement. References:

- resolve only to a work step's `wait_time`;
- do not chain;
- must not cause the same waiting evidence to be counted twice;
- must resolve consistently in validation, analysis, export, and rendering.

### Relations

Handoffs and rework are structured transition relations:

```yaml
handoff:
  type: responsibility

rework:
  reason: Incomplete information
  frequency:
    basis: observed
    numerator: 2
    denominator: 10
    observation_unit: cases
```

Boolean flags and metadata combinations are retired.

### Extensibility

- Unknown fields are rejected.
- Non-core data belongs under `extensions`.
- Extension measurement methods must use an explicit namespaced form.
- A supported core field must have defined semantics and a current consumer.

### Node applicability

- Control nodes are pure control-flow constructs.
- Work measurements, value classification, item/resource relations, and
  operational locations belong only on the node kinds whose semantics support
  them.
- Queue and wait nodes carry waiting evidence or a waiting reference, not work
  relations.

## Architecture

### Pydantic owns boundaries

Pydantic models are the single source of truth for:

- authored source shapes;
- canonical exchange shapes;
- local scalar and collection constraints;
- local field applicability;
- measurement and structured-relation shapes;
- generated authored and canonical JSON Schemas.

Pydantic errors must be adapted into stable FLO diagnostics. Internal Pydantic
types and error paths must not leak through the public API.

### Domain code owns semantics

Plain dataclasses and focused domain validators continue to own:

- graph topology and reachability;
- cross-references;
- include provenance and source locations;
- resource and item identity;
- Pint conversions and dimensional compatibility;
- queue-reference resolution;
- duplicate-contribution rules;
- path, cycle, branch, and parallel-flow analysis;
- derived metrics such as `modeled_lead_time`.

This separation prevents Pydantic from becoming the internal domain model.

### Generated schemas

- `schema/flo_source.json` is generated from the authored source model.
- `schema/flo_ir.json` and its packaged copy are generated from the canonical
  exchange model.
- Hand-maintained overlapping schemas are removed.
- Generation must gain a check mode and CI drift gate.

## Ordered Implementation

The order is intentional. Later phases depend on the vocabulary and contract
decisions established by earlier phases.

### Phase 1: Freeze the book-aligned contract

- [x] Record the governing ADR.
- [x] Define canonical timing and classification terms.
- [x] Define full measurement profiles.
- [x] Define process `lead_time` versus derived `modeled_lead_time`.
- [x] Define direct queue waiting references.
- [x] Define structured handoff and rework relations.
- [x] Establish pure control nodes and extension containment.
- [x] Add observation counts, observation units, windows, and evidence details
      to the book acceptance fixture.
- [x] Verify public terms against the book notes and record deliberate distinctions
      in `docs/specs/book_aligned_contract.md`. The acceptance fixture now uses
      simulated Friday 91 evidence and separates staging from notification.

### Phase 2: Establish one Pydantic contract system

- [x] Add strict source measurement and relation models.
- [x] Add strict canonical exchange models.
- [x] Generate authored and canonical schemas.
- [x] Remove the hand-authored typed-metadata schema.
- [x] Promote semantic values from opaque metadata to first-class IR fields.
- [x] Type canonical items, resources, locations, quantities, and spatial data
      instead of leaving them as `Any`.
- [x] Restrict measurement methods to core names or namespaced extensions.
- [x] Map Pydantic categories to stable FLO diagnostics, including a safe fallback
      for unknown categories; preserve authored paths without union markers.
- [x] Review module ownership: keep the cohesive boundary contracts together
      (under 500 lines) rather than introduce a second contract source. Revisit
      splitting only if a distinct ownership boundary emerges.
- [x] Add schema generation `--check` behavior and CI enforcement through the
      shared local/CI/publication pre-commit gate.

### Phase 3: Repair semantic correctness

#### 3.1 Applicability

- [x] Enforce step-only value classification.
- [x] Reject operational fields on control nodes.
- [x] Enforce work-only cycle and changeover measurements.
- [x] Enforce queue/wait relation restrictions.
- [x] Complete an explicit field-by-node-kind applicability matrix and test
      every supported field.

#### 3.2 Timing

- [x] Read named `analysis_input` results.
- [x] Use `primary` for presentation.
- [x] Remove timing aliases and metadata promotion.
- [x] Fail invalid selected duration values before analysis, export, or render.
      D-004 verifies both selectors, presentation-only profiles, conversion
      overflow, and API/CLI rejection parity.
- [x] Validate process `lead_time` selected results with the same duration
      semantics, using the same shared duration-check helper as nodes.
- [x] Verify observed process lead time and derived modeled lead time remain
      visibly distinct in every output.

#### 3.3 Waiting

- [x] Replace measurement IDs and copied aggregate values with direct refs.
- [x] Reject invalid targets and reference chains.
- [x] Avoid duplicate analytical contribution.
- [x] Resolve queue references before layout measurement and SVG emission while
      preserving authored references. D-001 verifies actual book labels.
- [x] Verify references to included evidence render the primary result, preserve
      zero, distinguish analytical selectors and leave canonical IR unchanged.

#### 3.4 Handoff and rework

- [x] Replace Boolean and metadata combinations with structured relations.
- [x] Update structural analysis to consume canonical relation fields.
- [x] Complete frequency, evidence, and extension validation.
- [x] Verify renderers and inspection surfaces display relation semantics
      consistently.

#### 3.5 Items, resources, lanes, and locations

- [x] Promote step relations to `consumes`, `produces`, `performed_by`, and
      `uses`.
- [x] Update movement and value-stream analyses to read first-class fields.
- [x] Update ELK/SPPM projection to preserve first-class fields.
- [x] Remove legacy process collections (`materials`, `equipment`, `workers`)
      from composition, validators, docs, and tests.
- [x] Collections occur only under `process` in source, fragments and exchange.
      Top-level/metadata placements and retired collection names are rejected.
- [x] Make renderers resolve referenced entity IDs to display names where
      appropriate.

#### 3.6 Supported-field discipline

- [x] Inventory every authored field.
- [x] For each field, document semantics, applicability, validation owner,
      canonical representation, and consumer.
- [x] Remove any field without all five.
- [x] Add an architecture test preventing new opaque semantic metadata paths.

### Phase 4: Remove compatibility surfaces

- [x] Remove source `attrs`.
- [x] Choose one nested subprocess spelling and remove the other
      (`steps` versus `subnodes`).
- [x] Remove top-level `edges` and endpoint aliases.
- [x] Remove legacy collection placement and naming (completed in phase 3).
- [x] Remove old internal-IR coercions and metadata promotion.
- [x] Remove old diagnostic codes and suggestions that describe retired
      syntax.
- [x] Search source, tests, examples, schemas, and active documentation for all
      retired names and remove them.

No migration command, runtime aliases, compatibility warnings, or dual-read
paths will be added.

### Phase 5: Simplify implementation

- [x] Delete validators now represented by Pydantic contracts.
- [x] Split graph, relation, measurement, quantity, and provenance validation
      into focused domain modules.
- [x] Keep one normalization step at each external boundary.
- [x] Remove downstream fallback reads from metadata or aliases.
- [x] Ensure internal IR serialization round-trips every first-class field.
- [x] Compare net source and test size after compatibility removal; investigate
      remaining duplication rather than optimizing for an arbitrary line
      target.

### Phase 6: Documentation and verification

- [x] Update language specification, manual, examples, and design documents.
- [x] Mark historical documents clearly where retired terminology must remain
      for archival accuracy.
- [x] Add authored and canonical schema drift checks (phase 2 checkpoint).
- [x] Add architecture/import allowlists that keep Pydantic at boundaries.
- [x] Run formatting, Ruff, type checking, architecture tests, focused suites,
      the full test suite, all examples, and golden renders.

## Current Migration State

Implemented surfaces (all six phases accepted):

- strict measurement and relation contracts;
- first-class canonical node, edge, and process fields;
- authored and canonical schema generation;
- example migration to profiles and canonical item/resource terminology;
- queue-reference validation, duplicate-count prevention and presentation-only
  resolution before measurement/emission (D-001);
- first-class timing, movement, value-stream, and structural analysis reads;
- first-class ELK/SPPM projection;
- shared validation of selected node/process presentation and analysis durations
  (D-004); optional selectors and unselected evidence retain their meaning;
- first-class internal-IR serialization paths and evidence round-trip checks;
- removal of the hand-authored typed-metadata schema.

The final audit covers the current specifications, manual, quickstart, README,
requirements catalog and affected design records. Historical checkpoint
narratives below retain their original terminology as evidence. Broader
measurement writers and richer publication/detail views remain future roadmap
work, outside this refactor; acceptance makes no release-completion claim.

The 2026-10-27 recovery checkpoint completed at **73 failed, 1726 passed**.
It closed 16 initial failures and added 24 passing contract checks. The later
D-003 checkpoint completed at **56 failed, 1827 passed**, closing 17 more failures
and adding 84 passing integrity/delivery cases, with no new failing cases or
collection errors. Its 118-test focused suite passes. D-003 now preserves bad
relation/measurement input through constructors, internal round-trip and
exchange projection until explicit validation rejects it. Process lead-time
shape validation is included. The D-004 checkpoint then completed at
**56 failed, 1904 passed**: 77 added regression cases pass, with an unchanged
failing case set. Both selected duration roles now use the shared duration rules
on node and process profiles. The targeted selected-duration/provenance delivery
suite passes 42 cases. The publication timing closure then completed at
**52 failed, 1908 passed**, closing its four named existing failures with no new
failures or added test cases. All 23 publication tests pass; original footer
assertions are retained and the partial-projection control now uses valid timing.
No production change was needed for that slice. Duration display closure then
completed at **47 failed, 1913 passed**, closing five named unit-conversion
failures without new failures or added cases. All 101 targeted unit/display
checks pass, with original conversion and non-mutation assertions retained.
Movement export closure then completed at **44 failed, 1916 passed**, closing
three more named existing failures without new failures or added cases. All 30
movement/export focused tests pass. Their canonical fixtures now pass IR
validation and retain the original route/entity assertions, with spatial
distance also checked. No production change was needed for either slice.
The 2026-10-28 batched closure completes all 44 remaining original failures.
The final full suite passes **1966 cases** with seven existing Click deprecation
warnings and no skips. Six added regressions cover real-book reference labels,
nonmutation and text fit, included evidence with distinct presentation/analysis
selectors, book annotation collisions and subprocess extension display. ELK,
wrap planning and SVG consume the same first-class content. Structured rework
callouts and swimlane classification now consume canonical fields. A bounded
two-axis annotation search resolves the exposed callout collision. Existing
White Belt width/row/corridor assertions remain intact. The book raster was
visually inspected and all 13 corpus cases pass SVG geometry/accessibility;
reviewed goldens and drift checks pass. D-001/D-002 are closed. The subsequent phase 3 closeout below completes the
remaining semantic obligations.
The 152-test foundation suite is retained as the earlier prerequisite evidence.
`tests/unit/compiler/test_contract_closeout.py` proves typed nested canonical
entities, method restrictions, generic diagnostic delivery, read-only drift
failure behavior, CI enforcement, and book sample/evidence preservation.

### Phase 3 closeout (2026-10-28)

All phase 3 obligations are checked with executable evidence:

- `test_phase3_applicability.py` inventories every source node field and checks
  every node kind against an independent matrix at source and canonical
  boundaries, including null declarations and attempts through attrs. Only work
  is classifiable; queue/wait nodes support waiting and physical locations.
- `book_aligned_fields.md` inventories every authored boundary field with
  meaning, applicability, validation owner, representation and consumer.
  `test_phase3_field_inventory.py` fails on undocumented fields or newly
  introduced core-semantic reads from opaque metadata. The unused business-unit
  type field and unused operational attrs overlays were removed.
- Source, include fragments and canonical exchange use only `process.items`,
  `process.resources` and `process.locations`. Composition has no slot alignment
  or collection precedence. Legacy collection validation/export paths and
  internal collection promotion are removed. Rejection, additive/grouped merge,
  duplicate identity, quantity and include-provenance assertions remain.
- Complete relation profiles survive inspection/exchange, including frequency
  basis/population/evidence, notes and extensions. Invalid frequency and nested
  nonfinite/non-JSON extensions fail at both source and canonical boundaries.
  Finite zero and fractional affected counts retain their supplied meaning.
- Timing inspection retains the full supplied process lead-time profile.
  Diagrams visibly distinguish supplied basis/primary results from modeled
  totals or ranges when publication text is enabled. Value-stream cards use
  primary; timelines use analysis_input. Supplied lead time never fills a
  missing modeled total. Performer/item/location labels resolve declared names
  on presentation copies while IDs remain canonical.
- Shared wait semantics now include wait-kind presentation and matching
  triangle attachments/avoidance; a real-cookie-process geometry regression
  protects the corrected connectors.

Final full suite: **2346 passed, 0 failed, no skips**, seven pre-existing Click
warnings. Ruff, formatting, type checking, all 11 import contracts, responsibility
checks, documentation governance, generated schemas, and whitespace checks pass.
All standalone valid examples validate and all invalid conformance roots reject;
include fragments are verified through composition. All 13 corpus renders pass
geometry/accessibility and deterministic golden drift checks. Ten intentional
artifact updates across nine cases were reviewed, including named performers,
explicit modeled labels, relation summaries and the wait shape. The pre-update
golden tree is preserved in `/tmp/flo-phase3-goldens-before`.

The preceding paragraph records the historical phase 3 handoff. Its remaining
compatibility and simplification work is closed by the following checkpoint.

### Phases 4–5 closeout (2026-10-29)

- Source accepts only nested subprocess `steps`, explicit `transitions`, and
  `source`/`target` endpoints. Control declarations are first-class; source and
  internal node attrs, alternate child/endpoint spellings, parser/composition
  translation and the obsolete name/content envelope are removed. Rejection
  tests cover root documents and included fragments, with source/include paths.
- Node.branch is first-class. Dataclasses no longer coerce dictionary entries,
  strip scalar values, filter malformed context or promote metadata. Explicit
  internal dictionary restoration rejects unknown fields and malformed entries.
  Internal process metadata is limited to identity; semantic context must use
  first-class fields or extensions. Invalid evidence remains intact until the
  validation boundary rejects it.
- Renderers consume canonical node/edge projections, including IDs, route,
  branch, handoff, rework and extensions. Authored graph synthesis, metadata
  hierarchy reads and movement relation aliases are gone. SCC condensation uses
  IR.edges, preserves external relations/context and records members in extensions.
- Locations have one spatial object. Display annotations use one explicit
  extension location for publication, continuation and spaghetti boundaries.
  Header owner/version resolve first-class context. The items exporter replaces
  historical ingredients/materials shims; CLI/API and example builds use
  `--export items`. Unknown formats fail instead of silently selecting JSON.
- Pydantic supplies local collection, entity, quantity, relation, classification
  and branch shapes. Shared branch contracts replace manual mode validation;
  recursive collection shapes replace handwritten source shape recursion.
  Finite-number guards prevent numeric-union overflow from escaping diagnostics.
  Domain modules separately own graph topology, relations, selected durations,
  entity identity/spatial units, quantity dimensions/equivalence and located
  errors/provenance. The former oversized validator is now a short orchestrator;
  its file-size exemption is removed.
- Internal serialization and exchange/layout projection share canonical field
  extraction. An exhaustive dataclass-field gate protects round trips and
  malformed context preservation. A six-module allowlist confines Pydantic
  imports to contracts and explicit input/validation boundaries.

Python line counts, measured against the tree at the start of phases 4–5:

| Scope | Before | After | Net |
| --- | ---: | ---: | ---: |
| Runtime source (`src/**/*.py`) | 28094 | 26947 | **−1147 (−4.1%)** |
| Tests (`tests/**/*.py`) | 26937 | 27125 | +188 |
| Runtime plus tests | 55031 | 54072 | **−959** |

These totals exclude generated schemas, SVGs, documentation and scripts. The
reduction comes from deleting compatibility, repeated coercion, duplicate local
validation and graph synthesis. Focused semantic tests, including quantity
precision/provenance and canonical input integrity, remain in place. Removed
compatibility expectations now assert rejection or exercise canonical inputs;
no skips, weakened geometry assertions or restored runtime aliases were added.

Full suite: **2366 passed, no failures or skips**, seven existing Click warnings.
Ruff/formatting, type checks, all 11 import contracts, architecture checks,
schemas, documentation governance, example validation and whitespace checks
pass. All 13 corpus cases pass geometry/accessibility and deterministic drift.
Seven reviewed SVG updates add first-class owner/version header rows; node
layouts and routing are unchanged. Linear and White Belt PNG previews were
inspected; the prior golden tree is in `/tmp/flo-phase45-goldens-before`.

The subsequent phase 6 acceptance checkpoint below closes the documentation
and integrated verification obligations.

## Phase 6 final acceptance — 2026-10-29

The audit closed source/schema gaps for entity collections, control declarations,
explicit nulls, profile-only processing/setup/process-lead fields and shared
named process identities. Valid named-target string shorthand is represented in
the generated schema. Named-target selection overrides that compilation ignored
are now rejected. Public collection validation shares contracts without crossing
private package boundaries. Source and canonical diagnostics retain FLO paths
and categories without exposing model internals or schema/input dumps.

The supported-field inventory covers 29 primary boundary models. The current
instructional-document gate checks 19 documents and their 12 YAML examples
against source models and generated structural schemas; complete examples also
pass FLO validation. Historical ADR context and future richer publication work
are explicitly distinguished from current supported behavior.

| Criterion | Disposition and evidence |
| --- | --- |
| 1. Book-aligned authored terms | Verified: supported-field inventory, current-document contract gate, book fixture and migrated examples. |
| 2. Retired names rejected | Verified: `test_phase45_closeout.py` exercises parser/includes, named targets, constructors, restoration and export rejection without translation. |
| 3. Generated schemas, no drift | Verified: `generate_contract_schemas.py --check`; source/canonical positive and negative cases in `test_phase6_acceptance.py`. |
| 4. Field ownership and consumers | Verified: `book_aligned_fields.md`, `test_phase3_field_inventory.py`, applicability matrix and removal of ignored named-target overrides. |
| 5. Source shape diagnostics | Verified: compiler suites and phase 6 entity, null, branch, named-target and diagnostic cases. |
| 6. Domain semantic rejection | Verified: semantic/waiting/canonical integrity suites and API/CLI consumer parity checks. |
| 7. Evidence distinctions retained | Verified: phase 3 evidence, phase 6 grouped-profile round-trip, waiting integrity, measurement and quantity suites. |
| 8. Shared canonical meanings | Verified: phase 3 evidence/relations, canonical round-trip and phase 4–5 projection tests; no metadata fallback. |
| 9. Pydantic boundary confinement | Verified: explicit seven-module allowlist, 11 import contracts kept, architecture scan has no blocking findings. |
| 10. Book fixture semantics/visuals | Verified: book rendering/evidence suites and deterministic `book_washnfold_local_rework` golden. |
| 11. Integrated verification | Verified: 2429 passed, no failures/skips; Ruff/format, runtime `ty check src`, schemas, governance, file-length policy and whitespace pass. All 27 valid roots rendered to 30 SVGs and six item summaries; 24 invalid roots rejected and three include fragments composed. All 13 golden cases/26 files match; 13 SVGs pass geometry/accessibility. |
| 12. Current documentation | Verified: README, Quickstart, manual, active specifications, requirements and affected design records reconciled; executable-document gate passes. |

Final Python physical-line counts, using the same scope as the phase 4 baseline:

| Scope | Before phase 4 | Final | Delta |
| --- | ---: | ---: | ---: |
| Runtime (`src/**/*.py`) | 28094 | 27049 | −1045 |
| Tests (`tests/**/*.py`) | 26937 | 27433 | +496 |
| Combined | 55031 | 54482 | −549 |

Generated schemas, documentation, scripts and artifacts are excluded. The final
audit adds boundary checks and meaningful regression coverage while retaining
the runtime reduction. No tests were skipped, behavioral assertions weakened,
or retired runtime aliases restored. All workspace changes remain uncommitted.

## Acceptance Criteria

The refactoring is complete only when all of the following are true:

1. The authored language uses only book-aligned terms.
2. Retired names are rejected rather than translated.
3. Authored and canonical schemas are generated from Pydantic and have no
   drift.
4. Every supported field has documented semantics, applicability, a validation
   owner, a canonical representation, and a current consumer.
5. Invalid local shapes fail at the source boundary with FLO diagnostics.
6. Invalid graph, reference, unit, and analytical semantics fail in domain
   validation before inspect, export, or render.
7. Omitted, explicit unknown, measured zero, referenced, observed, target, and
   derived values remain distinguishable.
8. Analysis, inspection, export, and rendering consume the same canonical
   meanings without alias precedence or metadata fallbacks.
9. Pydantic imports remain confined to boundary/contract modules.
10. The book fixture demonstrates the intended vocabulary and produces the
    expected semantic and visual results.
11. Ruff, formatting, type checks, architecture tests, the full test suite,
    example validation/rendering, schema checks, and golden checks all pass.
12. Active documentation contains no unsupported or retired language.

## Verification Strategy

Use layered verification:

1. Contract unit tests for valid and invalid source/canonical shapes.
2. Applicability matrix tests for every field and node kind.
3. Domain tests for graph, reference, provenance, unit, and analytical rules.
4. End-to-end API/CLI parity tests proving invalid models stop every validated
   consumer.
5. Round-trip tests for authored source, canonical exchange, and internal IR.
6. Book-fixture acceptance tests for terminology, measured evidence, modeled
   lead time, value classification, handoffs, rework, and rendering.
7. Generated-schema and architecture drift gates.
8. Full repository validation with no compatibility-only tests remaining.

