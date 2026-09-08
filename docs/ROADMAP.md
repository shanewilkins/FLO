# FLO Roadmap To 1.0

This roadmap describes FLO's intended path from the current pre-1.0 releases to a stable 1.0 release.
It is criteria-first rather than date-driven.
The roadmap is a public planning document and does not override FLO's policy, specifications, or schema contracts.
Normative scope, lifecycle, acceptance criteria, and unresolved product
decisions are tracked in `docs/requirements/`.

## MVP Boundary

FLO 0.4 is the minimum viable product milestone. FLO 1.0 is the later stability
and compatibility milestone; the terms are not interchangeable.

The 0.4 MVP is cumulative across the 0.2 through 0.4 release path. It includes:

- an end-user installation path that does not require a repository checkout or
  development-environment setup
- scaffolded first-model creation with maintained templates and assisted,
  explicit stable IDs
- source-aware human and machine-readable diagnostics with actionable repair
  guidance
- a useful zero-configuration render path with visible degradation warnings
- the process-modeling language, canonical IR, validation, and canonical JSON
  workflow
- a supported public Python integration baseline for downstream tools such as
  `lss4py`
- a maintained direct-SVG SPPM surface, with swimlane and spaghetti retained
  for Yellow Belt material and value stream retained for Green Belt material
- static analysis for timing, handoffs, rework, path length, and step classification
- a concise onboarding path and maintained reference documentation

MVP acceptance includes an observed first-run journey: a representative
process-improvement professional can install FLO, create a valid three-to-five
step process, validate it, render a readable SVG, and export canonical JSON in
about ten minutes using only the maintained onboarding path.

If release capacity creates a tradeoff, this complete authoring journey takes
precedence over telemetry work. Process telemetry is therefore deferred to a
later ratified belt or 1.0 workflow rather than becoming a partial 0.4 MVP
surface.

The 0.4 MVP does not require process-telemetry import, alignment, or analysis;
those operational workflows belong to later belt or 1.0 scope. It also does not
require multi-page publication, Yellow Belt swimlane or spaghetti acceptance,
Green Belt value-stream-map acceptance, the 1.0 language and CLI freeze, or the
1.0 packaging and support guarantees.

## Belt-Aligned Delivery Sequence

The modern process-improvement book is an immediate customer of both the FLO
language and the renderer. Pre-1.0 releases therefore unlock the book in belt
order:

- 0.4 unlocks White Belt and targets the September 15, 2026 book deadline.
- 0.5 unlocks Yellow Belt.
- 0.6 unlocks Green Belt.
- 0.7 unlocks Black Belt.
- 0.8 unlocks Master Black Belt.

Each belt release includes only the language semantics, validation, exchange,
and rendering capabilities needed by that belt's accepted specification.
Later-belt presentation features do not block an earlier release. Semantic and
validation work that prevents the compiler from accepting or emitting nonsense
may move earlier regardless of the belt where the affected concept is taught.

Completed work keeps its actual implementation milestone even when it arrived
ahead of the belt that will first depend on it. Early implementation does not
make later-belt acceptance a prerequisite for an earlier release. Black Belt and
Master Black Belt scope remains provisional until their book and language
specifications are accepted.

## 1.0 Outcome

FLO 1.0 will provide a stable process-modeling language, canonical IR, CLI contract, renderer surface, and telemetry-alignment workflow.
The supported runtime baseline for 1.0 is Python 3.14.

At 1.0, the following public contracts are stable:

- FLO source syntax and documented language semantics.
- Canonical IR and its serialized schema.
- CLI commands, exit codes, diagnostics, and machine-readable exports.
- The supported Python integration API and deterministic `.flo` source writer.
- Semantic source round-tripping, comment-preserving formatting, extension
  namespaces, and version-migration behavior.
- Direct SVG and JSON artifact reproducibility on the supported CI platform.
- Telemetry event schema and model-to-trace alignment workflow.
- The stable SPPM renderer contract.

For direct FLO outputs, the same canonical input, options, renderer version, and supported platform must produce byte-stable SVG and JSON artifacts.
Determinism is verified with release-blocking regression tests.

## Renderer Tiers

FLO may describe renderer maturity using `experimental`, `maintained`, and `stable` tiers before 1.0.
SPPM is the only renderer intended to reach the `stable` tier.
Swimlane and spaghetti remain maintained Yellow Belt material, and value stream
remains maintained Green Belt material.

A stable renderer provides:

- Documented input, option, artifact, and compatibility contracts.
- Deterministic artifact coverage for representative conformance and reference models.
- Release-blocking regression tests for supported behavior.
- Actionable diagnostics for incomplete or degraded output.
- Visual invariants for supported corpus artifacts, including no incoherent overlaps, clipped labels, missing edge endpoints, or broken routing.

SPPM must be stable by 1.0.
Flowchart direct SVG rendering is removed in 0.2.0.

## Compatibility And Deprecation

Pre-1.0 releases may change public behavior, but each change must have a documented migration path.
Public deprecations normally remain available for at least one complete minor release before removal.
Security or correctness fixes may use an accelerated removal path with explicit release notes.

The 1.0 release removes scheduled deprecated behavior, legacy aliases, and compatibility paths that do not belong in the stable public surface.
New compatibility shims are not introduced during the 0.9 release-hardening cycle unless required to fix a release-blocking defect.

## Telemetry And Privacy

Telemetry alignment is a 1.0 prerequisite.
Telemetry input is treated as potentially sensitive data.

Process-event telemetry is an opt-in external dataset that remains separate
from canonical IR and from FLO's OpenTelemetry-based runtime observability.
The Core Model/IR maintainer owns the event contract. The Security & Privacy
maintainer owns telemetry privacy policy, with the release maintainer
accountable until that role is separately staffed.

Before 1.0, FLO will document:

- The trusted-input boundary for trace and event data.
- The minimum event schema and field meanings.
- Identity, timestamp, lifecycle, and correlation semantics.
- Field-minimization and redaction guidance for sensitive data.
- Local-first processing, explicit persistence destinations, and no default
  network egress.

## Release Glide Path

### 0.2: Renderer Consolidation

- Remove the deprecated flowchart rendering surface. Complete on the 0.2 line.
- Complete shared SVG and renderer-platform primitives.
- Publish renderer tier definitions and capability expectations.
- Establish swimlane as a maintained renderer.
- Define direct SVG determinism and golden-artifact regression strategy.

0.2 closeout claims are checked against the normative registers:

- `TR-038` [0.2; Implemented]: Flowchart removal is complete.
- `UR-026` [0.2; Implemented]: Current guidance directs users to maintained renderers.
- `UR-035` [0.2; Implemented]: Standalone SPPM SVG publication context is complete.
- `TR-090` [0.2; Implemented]: Release views derive from the normative registers and roadmap claims are checked in CI.

### 0.3: Static Analytics Foundation

- [Implemented] Promote typed item, resource, location, and subprocess-membership contracts
  out of generic in-memory metadata into explicit canonical IR fields without
  changing their accepted source or serialized names.
- [Implemented] Deliver canonical IR analysis for handoffs, rework, path length,
  and step classification.
- [Implemented] Add a stable model-inspection and readiness report covering composition,
  entities, paths, named views, and missing data for requested analyses or
  diagrams.
- [Implemented] Produce analysis-oriented diagnostics and reports.
- [Implemented] Stabilize the analysis output schema and representative fixture
  corpus.
- [Implemented] Deliver unit-aware static timing analysis for cycle, queue-wait, setup or
  changeover, and modeled path lead time without guessing through incomplete,
  cyclic, or parallel flow.
- [Implemented] Add one central, extensible theme registry for maintained SVG diagrams;
  resolve deterministic publication background, typography family/scale, and
  semantic visual roles through the shared render-intent precedence; and
  protect built-in and configured themes with representative goldens.
- [Implemented] Deliver the maintained `value_stream` SVG renderer using the shared analysis
  primitives.
- [Implemented] Represent material and information flow distinctly, and diagnose partial
  data without implying that an absent flow surface exists.
- [Implemented] Implement default partial spaghetti rendering with deterministic warnings
  and partial-map notices, while retaining strict failure on request.
- [Implemented] Add capability-matrix support, deterministic fixtures, renderer tests, and
  user documentation as one release change.
- [Implemented] Deliver the White Belt book's compact wash-and-fold SVG as a dedicated
  deterministic SPPM corpus case using the maintained explicit-queue model;
  reject broken row-boundary routing and protect the book-consumed artifact
  from hand edits or baseline drift.

### 0.4: Completed Increments

- [Implemented] Preserve omitted queue-wait timing as absent and render an
  explicitly measured zero queue wait as `WT: 0 min` in maintained SPPM output.
- [Implemented] Preserve omitted timing categories as absent through static
  timing analysis, inspection JSON, and SPPM publication totals rather than
  supplying an implicit zero.
- [Implemented] Provide a maintained scaffold command with linear-flow,
  decision, handoff, rework, and value-stream templates; explicit stable IDs;
  template listing; target preview; and explicit overwrite acknowledgement.
- [Implemented] Add typed source diagnostics for parser, compiler, and
  validator failures, with stable codes, source excerpts, field paths, targeted
  repair suggestions where available, composition include chains, and `flo
  validate --format json` output generated from the same record as
  human-readable diagnostics.
- [Implemented] Document the isolated `uv tool install flo-lang` first-run path
  and rehearse scaffold, validation, default SVG render, and canonical JSON
  export in an isolated temporary workspace.
- [Implemented] Expose the lightweight `flo` Python facade with exception-free
  typed results for parse, compile, validate, inspect, and export operations.
- [Implemented] Resolve direct-SVG geometry requests with inspectable natural,
  requested, and final bounds; fail overflowing exact requests by default and
  support explicit canvas expansion without rescaling or clipping diagram
  coordinates.
- [Implemented] Support explicit direct-SVG scale-down-to-fit with uniform
  aspect preservation; scaling never enlarges a smaller natural diagram.
- [Implemented] Emit page-aware SPPM Typst source with deterministic sibling SVG
  figures, semantic-order pagination for linear flows, page-and-step continuation
  references, and explicit warning-or-error behavior when non-linear
  continuation would be ambiguous.

### 0.4: Remaining White Belt Delivery

- Complete invalid and unavailable timing-state preservation across validation,
  static analysis, canonical exchange, and SPPM, including focused end-to-end
  coverage alongside the implemented omitted-versus-measured-zero behavior.
- Audit the White Belt authoring and compiler path so accepted source always
  produces schema-valid canonical IR and invalid identities, references,
  timing values, or graph structure fail with actionable diagnostics rather
  than being repaired or guessed by a renderer.
- Complete deterministic single-page SPPM width and height control with
  unit-bearing dimensions, inspectable natural and final bounds, explicit safe
  fit or overflow behavior, and no clipping or unreadable forced scaling.
- Move the single-page SPPM surface needed by White Belt to the stable renderer
  tier without making multi-page or child-map publication part of the 0.4 gate.
- Add visual-invariant coverage for node-label legibility, overlap, clipping, and
  lane-frame containment on top of the established deterministic and golden-artifact gates.
- Publish the renderer capability matrix and renderer compatibility guarantees.
- Add color-safe and monochrome accessibility gates, non-color semantic cues,
  and legibility criteria to SPPM stable renderer promotion.
- Rehearse the complete White Belt install, author, validate, render, size, and
  canonical-export journey and regenerate the book-consumed reference artifact
  from a clean checkout.

The 0.4 gate explicitly excludes multi-page publication, automatic child maps,
Yellow Belt swimlane and spaghetti acceptance, and Green Belt value-stream-map
acceptance.

### 0.5: Yellow Belt Delivery

- Complete the accepted multi-page SPPM publication boundary, including Typst
  composition, stable step references, continuation anchors, child maps,
  deterministic warnings, and strict-mode failures.
- Make first-class authored locations and optional spatial geometry complete and
  well-validated for Yellow Belt source, canonical IR, JSON, and public API use.
- Deliver Yellow Belt acceptance for swimlane maps and for material, people,
  aggregate, and worker-level spaghetti maps, including deterministic partial
  rendering and strict missing-spatial behavior.
- Provide the deterministic review bundle needed for multi-page and multi-view
  review, with canonical JSON, provenance, model identity, and warnings.
- Keep telemetry, measurement-profile migration, and value-stream-map belt
  acceptance out of the 0.5 release gate.

### 0.6: Green Belt Delivery

- Ratify the Green Belt language and book specification before adding new
  release-blocking scope.
- Complete formal Green Belt acceptance for the maintained value-stream-map
  renderer, including explicit material and information flows and honest
  partial-data behavior.
- Add Green Belt book fixtures, documentation, and deterministic render checks
  without promoting value stream to the stable SPPM tier.
- Preserve the 0.3 value-stream implementation as early groundwork rather than
  rewriting its implementation history.

### 0.7: Black Belt Delivery

- Ratify the Black Belt book, language, and rendering specification before its
  candidate features become release gates.
- Treat measurement profiles, observed frequencies, trace import and alignment,
  conformance, process families and variants, and richer source exchange as
  provisional Black Belt candidates rather than inferred curriculum scope.
- Preserve the accepted architecture boundaries for those candidates so later
  work cannot mutate canonical designed-process truth or leak analytical
  methodology into the core compiler.
- Schedule the formal language, IR, public API, and CLI freeze after Black Belt
  and Master Black Belt semantics are known.

### 0.8: Master Black Belt Delivery

- Ratify the Master Black Belt book, language, and rendering specification
  before its candidate features become release gates.
- Treat object-centric event import, process discovery, advanced conformance,
  and process-mining reproducibility as provisional Master Black Belt
  candidates rather than assumed curriculum requirements.
- Retain ecosystem and operational hardening work that is independently needed
  for 1.0, including installed-distribution smoke tests, source-authoring schema,
  migration tooling, dependency and security automation, reproducibility, and
  support policy.
- Do not let provisional advanced-analysis work weaken or bypass canonical IR
  validation.

### 0.9: Release Candidate Hardening

- Freeze features.
- Accept only bug fixes, determinism corrections, documentation, test hardening, dependency or security remediation, release packaging, and previously announced deprecation removals.
- Resolve release-blocking test gaps, rendering defects, migration gaps, and documentation gaps.
- Publish the 1.0 migration guide and release-candidate checklist.
- Repeat the first-run journey on fresh supported machines and resolve
  release-blocking installation, diagnostic, documentation, or default-render
  usability failures.

### 1.0: Final Polish And Stable Launch

- Remove all behavior scheduled for deprecation before 1.0.
- Finalize language, IR, CLI, renderer, telemetry, and support-policy compatibility guarantees.
- Complete conformance, deterministic artifact, visual-invariant, fuzz or property, package-install, security, and release checks.
- Publish stable support, upgrade, and release policies.
- Publish compatibility guarantees for the public Python API, `.flo` writer,
  source formatter, extension namespaces, structured diagnostics, and source
  migration workflow.

## 1.0 Release Gates

FLO does not release 1.0 until all of the following are true:

- The language, IR schema, CLI error contract, and telemetry schema are documented and covered by conformance tests.
- The public Python API, structured diagnostics, deterministic `.flo` writer,
  semantic round trip, comment-preserving formatter, extension namespaces, and
  migration workflow are documented and covered by conformance tests.
- SPPM meets the stable renderer-tier criteria.
- Direct SVG and JSON outputs are byte-stable on the supported CI platform for the release corpus.
- The supported Python 3.14 installation path passes wheel and source-distribution smoke tests.
- Static analysis, test, coverage, determinism, artifact, fuzz or property, and security gates pass without unresolved release-blocking exceptions.
- Deprecated public behavior and legacy compatibility cruft scheduled for removal are gone.
- Governance, contribution, security-reporting, support, and release documentation are published and current.
- A fresh representative user can complete the maintained install, create,
  validate, render, and exchange journey without repository knowledge.

## What Is Not A 1.0 Goal

This roadmap does not require FLO to become a workflow execution engine, scheduler, orchestrator, or simulation platform.
It does not require BPMN import, BPMN export, or BPMN round-trip compatibility.
Future functionality must not weaken the stable language and artifact contracts established by 1.0.

## Committed Post-1.0 Direction

The first BPMN bridge is a one-way importer for a documented subset. It
preserves usable source IDs, emits `.flo` through the public writer, and
produces a human- and machine-readable fidelity report that distinguishes
mapped, approximated, ignored, and unsupported constructs. It does not add BPMN
export, promise round-trip fidelity, silently guess unsupported semantics, or
expand core FLO merely to reproduce BPMN's worldview.

Post-1.0 authoring work may also add cross-file rename/refactoring support and a
full language server after the source schema and public API have proven stable.

Item-level commitments and their exact target releases are normative in
`docs/requirements/`; this document describes milestone themes and gates rather
than duplicating the full register.
