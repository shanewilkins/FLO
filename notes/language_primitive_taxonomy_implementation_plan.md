# FLO Language Primitive Taxonomy Implementation Plan

Status: active implementation plan

## Purpose

Define the execution plan for aligning FLO's source language, compiler, IR,
renderers, fixtures, tests, and documentation with the accepted migration
contract in `docs/policy/language_primitive_migration_contract.md` and the
accepted taxonomy direction in `docs/design/language_primitive_taxonomy.md`.

This plan is implementation-facing.
It records the recommended migration order, file families likely to change, the
fixture strategy decision, and the validation posture for each phase.

## Scope

This plan covers:

- source examples under `examples/`
- compiler normalization, IR assembly, schema projection, and validation
- IR and typed metadata schemas where new primitives require structure
- renderers and exports that consume IR semantics
- fixture helpers and regression anchors in tests
- user-facing and normative documentation

This plan does not attempt to fully design future simulation semantics,
workflow execution, or runtime process-mining behavior.

## Locked Direction

The implementation should align to the following accepted taxonomy direction.

- `item` is the umbrella authored noun for the thing that flows.
- `material` and `information` are first-class item kinds.
- `resource` is the umbrella concept for performers and enabling support.
- `person` and `equipment` are first-class resource kinds.
- `location` remains first-class.
- `decision`, `queue`, `wait`, `subprocess`, `parallel_split`, and
  `parallel_join` are control-flow step kinds.
- `rework` is a relation, not a step kind.
- `handoff` is a first-class transition relation with hybrid inferred and
  explicit semantics.
- lanes remain organizing structures rather than the core semantic model.
- generic graph nodes and edges remain compiled IR forms rather than the
  primary author-facing model.

## Fixture Taxonomy Decision

Keep the current split between `examples/reference/` and
`examples/conformance/`.

Reason:

- `reference/` fixtures are broad, representative, and useful for docs, smoke
  tests, and rendered-output anchors.
- `conformance/valid/` and `conformance/invalid/` fixtures are narrow,
  rule-focused executable assertions.

Working rule:

- use `reference/` when the main question is "what does a realistic FLO model
  look like?"
- use `conformance/` when the main question is "should this exact rule pass or
  fail?"

This plan assumes the current names remain unchanged.

## Migration Principles

- no flag-day rewrite
- preserve current compatibility paths until the new source semantics are
  executable end-to-end
- move semantics and schemas before broad renderer rewrites
- keep author-facing primitives process-first and keep graph machinery derived
- add narrow conformance fixtures before broad showcase rewrites where possible
- keep validation executable at each phase rather than deferring all checks to
  the end

## Current Surfaces Expected To Change

### Examples And Fixtures

- `examples/reference/`
- `examples/conformance/valid/`
- `examples/conformance/invalid/`
- `examples/README.md`
- `examples/conformance/README.md`
- `tests/fixtures/sample_fixtures.py`

### Compiler And IR

- `src/flo/compiler/_adapter_normalization.py`
- `src/flo/compiler/_ir_assembly.py`
- `src/flo/compiler/compile.py`
- `src/flo/compiler/ir/models.py`
- `src/flo/compiler/ir/schema_projection.py`
- `src/flo/compiler/ir/validate.py`
- `src/flo/compiler/ir/validate_subprocess.py`
- `src/flo/compiler/analysis/movement.py`

### Schemas

- `schema/flo_ir.json`
- `schema/flo_types.json`
- possibly `schema/flo_types.json` examples and recommended keys

### Renderers And Exports

- `src/flo/render/_graphviz_backend_common_impl.py`
- `src/flo/render/_graphviz_dot_flowchart.py`
- `src/flo/render/_graphviz_dot_swimlane.py`
- `src/flo/render/_graphviz_dot_sppm.py`
- `src/flo/render/_graphviz_dot_spaghetti.py`
- `src/flo/render/layout_core/elk_support.py`
- `src/flo/render/_svg_flowchart.py`
- `src/flo/render/_svg_spaghetti.py`
- `src/flo/render/_svg_sppm.py`
- `src/flo/export/materials_export.py`
- `src/flo/export/movement_export.py`

### Documentation

- `docs/design/adr/language_primitive_taxonomy.md`
- `docs/specs/core_language.md`
- `docs/User_Manual.md`
- diagram specs under `docs/specs/` when new IR fields change diagram meaning
- `docs/design/typed_metadata.md`
- `docs/design/history/ontology.md`
- `docs/design/language_primitive_taxonomy.md` if the implementation reveals
  adjustments

## Locked Implementation Decisions

The migration contract now locks the following implementation decisions before
broad code edits.

- Source syntax for items:
  - canonical process-level authoring uses `items:` with typed entries
  - new docs and fixtures should not use `materials:` or `information:`

- Step-level item relations:
  - canonical step-level relations are `consumes` and `produces`
  - new docs and fixtures should not use `inputs` or `outputs`

- Resource typing:
  - canonical process-level authoring uses `resources:` with typed entries
  - new docs and fixtures should not use process-level `workers:` or
    `equipment:` as canonical surfaces
  - canonical step-level relations are `performed_by` and `uses`
  - new docs and fixtures should not use step-level `workers` or `equipment`

- Parallel syntax and IR shape:
  - Phase 1 introduces `parallel_split` and `parallel_join` as explicit step
    kinds first
  - no higher-level parallel sugar is required in the same phase

- Handoff shape:
  - explicit source surface in Phase 1 lives on transitions or edges via
    `handoff`
  - typed handoff categories such as `handoff_type` are deferred to a
    follow-on phase
  - no inferred handoff semantics are required in Phase 1

- Backward compatibility posture:
  - new examples and docs should use canonical surfaces immediately
  - compatibility aliases are not part of the migration contract

## Phase 0: Freeze The Migration Contract

Goal:
Write down the concrete migration boundaries before changing behavior.

Deliverables:

- this implementation plan in `notes/`
- accepted migration contract in
  `docs/policy/language_primitive_migration_contract.md`
- accepted fixture taxonomy decision: keep `reference/` and `conformance/`
- accepted taxonomy note in `docs/design/language_primitive_taxonomy.md`
- ADR recording the accepted language-primitive direction in
  `docs/design/adr/language_primitive_taxonomy.md`

Stop line:

- contributors can point to one source of truth for primitive hierarchy and one
  source of truth for migration order

Success criteria:

- the taxonomy note, fixture decision, and implementation plan do not conflict
- the ADR records the accepted direction in a short, decision-focused form
- contributors can identify the next execution phase without reopening the
  taxonomy debate
- no active migration work depends on unstated fixture or hierarchy decisions

Status:

- complete

## Phase 1: Introduce Source-Level Primitive Support In The Compiler

Goal:
Teach the source normalization and IR assembly layers to understand the new
primitive set without requiring renderer parity on day one.

Work:

1. Extend source normalization
   - update `src/flo/compiler/_adapter_normalization.py`
   - normalize authored item collections and typed item kinds
   - normalize any new relations such as `consumes`, `produces`, and
     transition-level handoff declarations
   - preserve current aliases such as `inputs` and `outputs` if compatibility is
     retained

2. Extend IR assembly
   - update `src/flo/compiler/_ir_assembly.py`
   - compile new step kinds `parallel_split` and `parallel_join`
   - compile explicit rework and handoff relation data onto edges or edge-like
     IR fields
   - preserve implicit sequential synthesis and local branching behavior

3. Extend typed IR models
   - update `src/flo/compiler/ir/models.py`
   - add typed support for any new node or edge fields needed for item kinds,
     handoff typing, or parallel control semantics

4. Extend validation
   - update `src/flo/compiler/ir/validate.py`
   - validate new step kinds
   - validate parallel split/join structural rules
   - validate handoff type and override consistency
   - validate item-kind usage and relation integrity

5. Extend schema projection
   - update `src/flo/compiler/ir/schema_projection.py`
   - project new typed fields cleanly to JSON export

Focused validation:

- new or updated unit tests targeting normalization, IR assembly, schema
  projection, and validation
- keep these tests narrow before changing broad render baselines

Stop line:

- new source semantics compile to IR and validate deterministically
- canonical examples compile under the documented canonical rules

Success criteria:

- at least one updated reference fixture and one new conformance fixture compile
  through the new source path
- unit tests cover item support, handoff support, rework relation handling, and
  parallel step-kind validation
- compiler behavior is explicit about canonical source surfaces for this phase
- no renderer-specific assumptions are needed for compiler tests to pass

Status:

- complete

Completion notes:

- source normalization now supports canonical process-level `items` and
  `resources` and canonical step-level relations (`consumes`, `produces`,
  `performed_by`, `uses`) with legacy alias intake preserved for compatibility
- IR assembly and typed IR models include explicit edge-level `handoff`
  semantics and support explicit `parallel_split` and `parallel_join` step
  kinds
- validation covers canonical node fields, item and resource declaration
  integrity, resource kind checks for performer and equipment relations, explicit
  handoff typing checks, and parallel split/join structural rules
- schema projection and schema contracts align with the new fields and kinds,
  including runtime schema parity with packaged schema files
- fixtures were updated to include canonical representative and conformance
  coverage:
  - updated reference fixture:
    `examples/reference/new_semantics.flo`
  - added valid conformance fixture:
    `examples/conformance/valid/valid_canonical_relations_with_resources.flo`
  - added invalid conformance fixture:
    `examples/conformance/invalid/invalid_consumes_undeclared_item.flo`

Validation snapshot:

- focused compiler and conformance suite currently passes:
  - `uv run pytest -q tests/unit/test_conformance_examples.py tests/unit/compiler/test_compiler_import.py tests/unit/compiler/test_schema_contract.py tests/unit/test_validate_errors.py tests/unit/test_json_export_branches.py`
  - result: `87 passed`

## Phase 2: Update Schemas And Typed Metadata

Goal:
Make the new semantics explicit in the serialized and typed contracts.

Work:

1. Update `schema/flo_ir.json`
   - add any new node kinds such as `parallel_split` and `parallel_join`
   - add item- and handoff-related structural fields if they are part of the
     canonical serialized contract

2. Update `schema/flo_types.json`
   - promote handoff typing beyond the current lightweight boolean-only posture
   - add typed support for item kinds and any new item-related relations if
     those remain metadata-backed rather than structural
   - update recommended keys and examples

3. Align design notes
   - update `docs/design/typed_metadata.md` to match the actual accepted field
     shapes

Important rule:

- only place semantics in typed metadata when they truly belong there
- do not hide newly first-class primitives behind generic metadata if the IR or
  source contract now treats them as semantic structure

Focused validation:

- schema validation tests
- JSON export round-trip tests

Stop line:

- the serialized contract can express the accepted primitive set without
  ambiguity

Success criteria:

- `schema/flo_ir.json` can encode the new step kinds and any accepted new
  structural fields
- `schema/flo_types.json` no longer underspecifies handoff semantics relative
  to the implementation
- schema examples demonstrate the accepted item and handoff direction clearly
- JSON export tests prove that compiler output conforms to the updated schemas

Status:

- complete

Completion notes:

- synchronized IR schema contract between repo and packaged runtime schema:
  - `schema/flo_ir.json`
  - `src/flo/schema/flo_ir.json`
- confirmed process metadata render-intent structure is aligned in both IR
  schema copies
- advanced typed metadata contract in `schema/flo_types.json`:
  - canonical process-level typed collections now include `items`, `resources`,
    and `locations`
  - legacy process-level `materials`, `equipment`, and `workers` remain as
    compatibility aliases
  - `handoff_type` is now an explicit enum:
    `responsibility`, `information`, `material`, `system`, `location`,
    `mixed`
  - recommended keys and examples updated to canonical item/resource direction
- aligned explanatory design note `docs/design/typed_metadata.md` to canonical
  process-level typed collections and legacy alias posture
- added schema contract tests for:
  - repo versus packaged IR schema parity
  - Phase 2 typed metadata canonical key and handoff-type coverage

Validation snapshot:

- focused schema and export checks currently pass:
  - `uv run pytest -q tests/unit/compiler/test_schema_contract.py tests/unit/test_validate_schema.py tests/unit/test_json_export_branches.py`
  - result: `21 passed`

## Phase 3: Migrate Examples And Conformance Fixtures

Goal:
Make the fixture corpus reflect the new process-first semantics and new
primitives.

Work:

1. Update `examples/reference/`
   - migrate broad examples to the new item, handoff, and parallel semantics
   - keep them readable and representative rather than minimal
   - use at least one strong reference example for each of the following:
     mixed material and information flow, explicit handoff, explicit rework,
     and parallel split/join

2. Update `examples/conformance/valid/`
   - add narrow valid fixtures for:
     - item declarations and item kinds
     - consumes/produces relations
     - explicit handoff typing and override
     - parallel split/join structural validity
     - rework plus handoff coexistence

3. Update `examples/conformance/invalid/`
   - add narrow invalid fixtures for:
     - unresolved item references
     - invalid item kind
     - invalid handoff type or malformed override
     - split without matching join where required by the rule set
     - malformed parallel or rework declarations

4. Update fixture guidance docs
   - revise `examples/README.md`
   - revise `examples/conformance/README.md`
   - keep the current role distinction between `reference/` and `conformance/`

5. Update test fixture helper
   - revise `tests/fixtures/sample_fixtures.py` if the seeded reference example
     should become a newer representative fixture than `linear.flo`

Focused validation:

- parser, compiler, and validation suites loading the new fixtures directly
- smoke tests using updated reference fixtures

Stop line:

- fixture corpus demonstrates the new semantics cleanly
- fixture guidance clearly explains where new examples belong

Success criteria:

- `examples/reference/` includes realistic fixtures covering items, mixed
  material and information flow, handoff, rework, and at least one parallel
  path
- `examples/conformance/valid/` and `examples/conformance/invalid/` each gain
  narrow fixtures for the new primitive rules
- fixture docs still make the distinction between representative examples and
  rule-focused conformance fixtures obvious
- `tests/fixtures/sample_fixtures.py` points at a representative fixture that
  exercises the intended new source model

Status:

- complete

Completion notes:

- reference fixture coverage now includes strong canonical exemplars:
  - `examples/reference/new_semantics.flo`
  - `examples/reference/semantic_controls_showcase.flo`
- the reference corpus now clearly covers mixed material and information flow,
  explicit handoff, explicit rework, and explicit parallel split/join
- conformance fixtures now include narrow valid coverage for:
  - canonical item/resource relations
  - explicit handoff-bearing edges
  - rework plus handoff coexistence
  - explicit parallel split/join structure
- conformance fixtures now include narrow invalid coverage for:
  - undeclared item references
  - invalid item kind
  - wrong resource kind for canonical resource relations
  - malformed handoff override values
  - malformed parallel structure
  - malformed rework metadata
- fixture guidance docs updated:
  - `examples/README.md`
  - `examples/conformance/README.md`
- `tests/fixtures/sample_fixtures.py` now seeds integration tests from
  `examples/reference/semantic_controls_showcase.flo`
- compiler edge assembly preserves raw authored `handoff` values so malformed
  explicit handoff overrides survive to semantic validation instead of being
  silently dropped during compilation

Validation snapshot:

- focused fixture-driven coverage currently passes:
  - `uv run pytest -q tests/unit/test_conformance_examples.py tests/unit/compiler/test_compiler_import.py tests/integration/test_pipeline_integration.py tests/integration/services/test_cli_click.py tests/integration/test_cli_examples.py`
  - result: `39 passed`

## Phase 4: Deprecate Graphviz And Strengthen Export Surfaces

Goal:
Treat Graphviz and DOT as deprecated compatibility paths, not strategic
implementation targets, while making canonical JSON and human-readable export
surfaces correct and useful.

Work:

1. Mark Graphviz and DOT deprecated
   - update CLI help, option guidance, and source-level comments where needed
   - identify Graphviz-backed modules as compatibility-only surfaces
   - record a removal posture: no new feature investment, retain only until
     direct SVG/export parity is acceptable and at least one release cycle of
     deprecation messaging has elapsed

2. Freeze Graphviz behavior to compatibility-only maintenance
   - do not add new semantic parity work for DOT output
   - only make minimal repairs needed to keep existing compatibility paths from
     failing unexpectedly during the transition window
   - prefer explicit limitations or warnings over silently partial semantics

3. Keep maintained direct rendering paths honest
   - update direct SVG and related maintained rendering surfaces only where they
     are still active product paths
   - ensure maintained non-DOT rendering paths either tolerate accepted IR
     semantics or fail with deterministic, actionable limitations
   - do not force maintained rendering paths to mirror deprecated DOT behavior

4. Strengthen canonical JSON export
   - treat JSON as the sole machine-readable export target for this phase
   - do not introduce XML in this phase
   - update `src/flo/export/json_export.py` and any supporting projection code
     as needed so exported JSON is both syntactically valid and semantically
     aligned with the accepted canonical IR contract
   - ensure JSON export remains the key contract surface for downstream tools,
     analysis, and future interoperability work

5. Align text and analysis exports to canonical semantics
   - update `src/flo/export/materials_export.py`
   - update `src/flo/export/movement_export.py`
   - update `src/flo/compiler/analysis/movement.py`
   - ensure material, information, people, equipment, and location-oriented
     summaries use canonical item/resource/location semantics intentionally
     rather than relying only on legacy `inputs`, `outputs`, `workers`, and
     `equipment` fields
   - keep human-readable text exports in scope for bills of materials,
     movement summaries, and related operational reporting

Important rules:

- Graphviz and DOT are deprecated in this phase but not yet removed
- no XML export work belongs in this phase
- JSON is the authoritative machine-readable export format for this stage of
  the roadmap
- do not let deprecated renderer constraints distort the accepted semantic
  shape of the IR or export contracts
- text exports remain in scope as human-readable operational summaries, not as
  substitutes for canonical machine-readable export

Focused validation:

- narrow JSON export and schema-alignment tests
- focused text export and movement-analysis tests
- targeted CLI export tests for `json`, `ingredients`, and `movement`
- targeted deprecation messaging checks for DOT/Graphviz surfaces when those
  messages are introduced
- maintained direct SVG tests only when a maintained rendering path is touched

Stop line:

- Graphviz and DOT are clearly deprecated with an explicit compatibility-only
  posture
- canonical JSON export is trustworthy as the primary machine-readable export
  contract
- text and analysis exports reflect canonical semantics intentionally rather
  than only through legacy field assumptions

Success criteria:

- CLI and source surfaces make Graphviz/DOT deprecation visible and
  unambiguous
- no new Phase 4 implementation depends on achieving DOT feature parity
- `flo compile` and `--export json` emit schema-aligned canonical JSON that is
  semantically correct for accepted item/resource/handoff/parallel semantics
- text exports remain useful for human-readable bills of materials and movement
  summaries
- movement and related analysis exports use canonical item/resource/location
  semantics intentionally enough to support downstream Python and pandas-based
  analysis without requiring XML
- any maintained rendering path that does not yet support an accepted
  primitive fails with an actionable, deterministic limitation message

Status:

- complete

Completion notes:

- Graphviz and DOT now carry explicit deprecated compatibility-only messaging
  across CLI help, option validation, and backend/service comments:
  - `src/flo/core/cli.py`
  - `src/flo/core/cli_args.py`
  - `src/flo/core/render_option_schema.py`
  - `src/flo/core/_option_validation.py`
  - `src/flo/core/__init__.py`
  - `src/flo/render/graphviz_backend.py`
  - `src/flo/services/graphviz.py`
- Phase 4 implementation was intentionally constrained away from DOT feature
  parity work; Graphviz surfaces were limited to compatibility messaging and
  minimal guardrail repairs rather than new semantic investment
- canonical JSON export was strengthened as the authoritative machine-readable
  contract surface:
  - `src/flo/compiler/ir/schema_projection.py` now preserves authored process
    identity from canonical metadata when projecting schema-shaped JSON
  - JSON export and schema-alignment tests cover canonical process metadata,
    branch behavior, and schema parity expectations
- text export surfaces now prefer canonical process semantics when available:
  - `src/flo/export/materials_export.py` prefers `items` and `resources` over
    legacy `materials` and `equipment`
  - human-readable ingredient/material summaries remain available as an
    operational reporting surface rather than a machine-readable contract
- movement analysis now uses canonical authored relations intentionally:
  - `src/flo/compiler/analysis/movement.py` prefers
    `produces`/`consumes` and `performed_by` with legacy fallback to
    `outputs`/`inputs` and `workers`
  - movement exports therefore reflect canonical item/resource/location
    semantics without requiring XML or deprecated renderer behavior
- targeted export coverage now exercises canonical semantics through both the
  registry and CLI layers:
  - `tests/unit/export/test_materials_export.py`
  - `tests/unit/analysis/test_movement.py`
  - `tests/unit/test_export_registry.py`
  - `tests/integration/test_cli_export_flag.py`
  - `tests/integration/test_cli_render_options.py`
  - `tests/integration/services/test_cli_click.py`

Validation snapshot:

- focused Phase 4 export and deprecation slices passed during implementation:
  - `uv run pytest -q tests/integration/services/test_cli_click.py tests/integration/test_cli_render_options.py`
  - `uv run pytest -q tests/unit/test_json_export_branches.py tests/unit/test_export_registry.py tests/integration/test_cli_export_flag.py`
  - `uv run pytest -q tests/unit/export/test_materials_export.py tests/unit/analysis/test_movement.py tests/unit/test_export_registry.py tests/integration/test_cli_export_flag.py`
- full repository checkpoint currently passes:
  - `uv run pytest -q`
  - result: `851 passed`
- full repository hook gate currently passes:
  - `uv run pre-commit run --all-files`

## Phase 5: Update Tests And Regression Baselines

Goal:
Bring the test suite and generated regression assets into alignment with the
new semantics.

Work:

1. Update unit tests
   - compiler and validation tests for primitive semantics
   - renderer tests for new node kinds and edge semantics
   - movement-analysis tests for item/resource/location interplay

2. Update integration tests
   - CLI compile and render paths using updated reference fixtures
   - conformance tests loading the new valid and invalid fixtures

3. Update any generated render baselines under `renders/`
   - only after semantic outputs are stable for the affected fixtures

4. Keep fixture sourcing centralized
   - continue loading from `examples/` instead of inlining YAML in tests where a
     real fixture would be clearer

Focused validation:

- narrow pytest slices first
- then broader regression slices once baselines are updated

Stop line:

- tests fail only for real semantic regressions, not for fixture drift or stale
  assumptions about old primitives

Success criteria:

- compiler, renderer, and integration suites each contain explicit coverage for
  the new primitives most relevant to that layer
- generated baselines under `renders/` are updated only for agreed semantic
  changes, not accidental formatting drift
- tests load real fixtures from `examples/` wherever a source fixture is more
  useful than inline YAML
- a clean targeted test run exists for each migration phase before broader
  regression runs are required

## Phase 6: Update Normative And User-Facing Documentation

Goal:
Make the documentation describe the language that now exists.

Work:

1. Normative core semantics
   - update `docs/specs/core_language.md`
   - make the locked primitive set and relation model normative where accepted

2. Diagram specs
   - update specs under `docs/specs/` where new IR fields or step kinds affect
     diagram meaning

3. User manual
   - update `docs/User_Manual.md`
   - teach items, material versus information, handoff, and parallel flow using
     realistic examples

4. Design notes

   - add `docs/design/adr/language_primitive_taxonomy.md`
   - update `docs/design/history/ontology.md`
   - update `docs/design/typed_metadata.md`
   - keep `docs/design/language_primitive_taxonomy.md` consistent with the
     implementation reality

Focused validation:

- docs governance checks
- targeted editor diagnostics on touched docs

Stop line:

- contributors no longer need to infer the new language model from code or test
  fixtures alone

Success criteria:

- `docs/design/adr/language_primitive_taxonomy.md` records the accepted
  architecture decision separately from the broader explanatory design note
- `docs/specs/core_language.md` describes the accepted primitive model without
  falling back to graph-first framing
- `docs/User_Manual.md` teaches items, handoffs, rework, and parallel flow with
  updated examples
- relevant diagram specs describe any changed IR meaning introduced by the new
  primitives
- the design notes remain explanatory and consistent with the implemented
  semantics rather than serving as the only place the new model is described

## Recommended Execution Order

Recommended order:

1. Phase 1 compiler support
2. Phase 2 schema and typed contract alignment
3. Phase 3 fixture migration
4. Phase 4 Graphviz deprecation and export updates
5. Phase 5 tests and baselines
6. Phase 6 documentation alignment

This order is intentional.
The compiler and schema layers should decide the semantics before broad
renderer or docs rewrites lock in accidental shapes.

## Validation Strategy

For each phase, prefer the narrowest executable check that can falsify the
current change.

Recommended progression:

1. focused unit tests for the touched compiler or renderer slice
2. conformance fixture tests for new valid and invalid rules
3. targeted integration tests for affected CLI and render flows
4. broader regression suites only after local behavior is stable

Representative validation families likely to matter:

- compiler and validation tests under `tests/unit/`
- integration flows under `tests/integration/`
- policy and boundary tests under `tests/policy/`
- docs governance via `uv run python scripts/check_docs_governance.py`

## Risks And Failure Modes

1. Hiding first-class semantics in metadata
   - risk: item, handoff, or parallel semantics remain half-implemented and
     ambiguous
   - mitigation: decide explicitly which fields become structural versus typed
     metadata

2. Breaking renderers through stale node-kind assumptions
   - risk: new step kinds compile but fail in Graphviz or SVG paths
   - mitigation: update shared render lowering before mass fixture migration

3. Fixture drift across reference and conformance roles
   - risk: showcase examples become overloaded with narrow validation intent
   - mitigation: preserve the current split and add narrow conformance fixtures
     first

4. Over-widening the change set
   - risk: compiler, schema, renderer, and docs changes land without a stable
     contract
   - mitigation: complete the compiler and schema stop lines before broad
     renderer or baseline churn

5. Ambiguous backward compatibility rules
   - risk: old examples continue to compile, but no one knows which surfaces
     are deprecated
   - mitigation: document alias and compatibility posture explicitly in the
     phase where it is implemented

## Concrete Early Milestones

The first useful milestone is not full feature parity.
It is one end-to-end slice proving the new semantics.

Recommended first milestone:

- one updated reference example showing items, material versus information,
  explicit handoff, and rework
- one valid conformance fixture for parallel split/join
- one invalid conformance fixture for malformed handoff or item reference
- compiler and schema support sufficient to compile and validate those fixtures
- renderer compatibility sufficient to render the updated reference example

Once that slice is stable, proceed with broader fixture and renderer migration.

## Open Questions To Resolve During Execution

- whether `inputs` and `outputs` remain as aliases or are fully replaced by
  `consumes` and `produces`
- whether source syntax exposes top-level `items:` plus typed item kinds,
  separate top-level `materials:` and `information:`, or both
- whether handoff typing is modeled structurally on the edge contract or partly
  through typed metadata
- whether parallel validation requires strict split/join pairing in v0.1
  compatibility mode or supports a narrower initial rule set
- whether movement analysis should treat information movement as a first-class
  export concept alongside material and people movement

These questions should be resolved in the implementation itself and then folded
back into the specs and taxonomy note.
