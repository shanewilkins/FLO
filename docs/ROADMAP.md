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
- maintained direct-SVG SPPM, swimlane, spaghetti, and value-stream-map
  surfaces
- static analysis for handoffs, rework, path length, and step classification
- the minimum telemetry event schema, model-to-trace identity rules,
  trace-alignment prototypes, and conformance fixtures
- a concise onboarding path and maintained reference documentation

MVP acceptance includes an observed first-run journey: a representative
process-improvement professional can install FLO, create a valid three-to-five
step process, validate it, render a readable SVG, and export canonical JSON in
about ten minutes using only the maintained onboarding path.

If 0.4 capacity forces a scope tradeoff, this complete authoring journey takes
precedence over telemetry alignment. Telemetry work may move to its next
roadmap stage rather than allowing 0.4 to meet technical component goals without
being viable for its intended users.

The 0.4 MVP does not require the 0.5 telemetry-analysis surface, complete
multi-page SPPM publication due in 0.6, stable renderer promotion, the 1.0
language and CLI freeze, or the 1.0 packaging and support guarantees.

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
- Stable renderer contracts for SPPM, swimlane, spaghetti, and value stream
  maps.

For direct FLO outputs, the same canonical input, options, renderer version, and supported platform must produce byte-stable SVG and JSON artifacts.
Determinism is verified with release-blocking regression tests.

## Renderer Tiers

FLO may describe renderer maturity using `experimental`, `maintained`, and `stable` tiers before 1.0.
All maintained 1.0 renderers must reach the `stable` tier.

A stable renderer provides:

- Documented input, option, artifact, and compatibility contracts.
- Deterministic artifact coverage for representative conformance and reference models.
- Release-blocking regression tests for supported behavior.
- Actionable diagnostics for incomplete or degraded output.
- Visual invariants for supported corpus artifacts, including no incoherent overlaps, clipped labels, missing edge endpoints, or broken routing.

SPPM, swimlane, spaghetti, and value stream maps must all be stable by 1.0.
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

- Deliver canonical IR analysis for handoffs, rework, path length, and step classification.
- Add a stable model-inspection and readiness report covering composition,
  entities, paths, named views, and missing data for requested analyses or
  diagrams.
- Produce analysis-oriented diagnostics and reports.
- Stabilize the analysis output schema and representative fixture corpus.
- Deliver the maintained `value_stream` SVG renderer using the shared analysis
  primitives.
- Represent material and information flow distinctly, and diagnose partial
  data without implying that an absent flow surface exists.
- Implement default partial spaghetti rendering with deterministic warnings
  and partial-map notices, while retaining strict failure on request.
- Add capability-matrix support, deterministic fixtures, renderer tests, and
  user documentation as one release change.

### 0.4: Telemetry Model And MVP

- Deliver the end-user installation, scaffold/template, diagnostic, default
  rendering, and public Python API baseline required by the MVP journey.
- Validate the first-run time-to-model acceptance boundary with a representative
  process-improvement user and a fresh environment.
- Publish and validate `schema/flo_trace.json` and the normative event
  semantics.
- Deliver local, explicit trace import, deterministic model-to-trace alignment,
  and conformance fixtures without mutating canonical IR.
- Enforce the telemetry privacy defaults for validation, alignment, logging,
  runtime spans, and persisted outputs.
- Demonstrate the cumulative MVP acceptance boundary defined above.

### 0.5: Telemetry Analysis

- Support trace-derived transition frequencies, dwell or wait measures, and rework rates.
- Publish telemetry import and alignment report contracts.
- Complete aggregate and row-level report privacy modes, redaction,
  pseudonymization, and fail-closed verification.

### 0.6: Renderer Stabilization

- Complete the accepted multi-page SPPM publication boundary, including Typst
  composition, stable step references, continuation anchors, child maps,
  deterministic warnings, and strict-mode failures.
- Move SPPM, swimlane, spaghetti, and value stream maps to the stable renderer
  tier.
- Add visual-invariant coverage for node-label legibility, overlap, clipping, and
	lane-frame containment on top of the established deterministic and golden-artifact gates.
- Publish the renderer capability matrix and renderer compatibility guarantees.
- Add color-safe and monochrome accessibility gates, non-color semantic cues,
  and legibility criteria to stable renderer promotion.
- Deliver a deterministic review bundle containing selected visuals, canonical
  JSON, provenance, model identity, and warnings.

### 0.7: Language, IR, And CLI Freeze Candidate

- Freeze the proposed 1.0 language, canonical IR, schema, and CLI contracts.
- Freeze the supported Python API and structured diagnostic model.
- Deliver the deterministic `.flo` writer with semantic round-trip tests.
- Deliver an idempotent, comment-preserving formatter in check, stream, and
  explicit write modes.
- Finalize namespaced extension metadata and deterministic preservation through
  compile, JSON export, and source emission.
- Finalize the standard and verbose node-content policy, including approved
	queue-detail fields and layout requirements for verbose rendering.
- Remove or migrate legacy authoring aliases according to documented deprecation policy.
- Expand conformance coverage for stable contracts and supported migration paths.

### 0.8: Ecosystem And Operational Hardening

- Verify Python 3.14 support in CI and distribution artifacts.
- Require wheel and source-distribution installation smoke tests.
- Complete dependency automation, security reporting, contributor guidance, release process, and support policy.
- Add reproducibility and upgrade-path tests for public artifacts.
- Publish the versioned source-authoring schema, maintained snippets, and basic
  schema-aware editor setup.
- Deliver dry-run, diffable, non-destructive source-version migration tooling.
- Test the complete end-user workflow from installed artifacts on supported
  platforms without a source checkout.

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
- SPPM, swimlane, spaghetti, and value stream maps meet the stable
  renderer-tier criteria.
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
