# FLO Roadmap To 1.0

This roadmap describes FLO's intended path from the current pre-1.0 releases to a stable 1.0 release.
It is criteria-first rather than date-driven.
The roadmap is a public planning document and does not override FLO's policy, specifications, or schema contracts.

## 1.0 Outcome

FLO 1.0 will provide a stable process-modeling language, canonical IR, CLI contract, renderer surface, and telemetry-alignment workflow.
The supported runtime baseline for 1.0 is Python 3.14.

At 1.0, the following public contracts are stable:

- FLO source syntax and documented language semantics.
- Canonical IR and its serialized schema.
- CLI commands, exit codes, diagnostics, and machine-readable exports.
- Direct SVG and JSON artifact reproducibility on the supported CI platform.
- Telemetry event schema and model-to-trace alignment workflow.
- Stable renderer contracts for SPPM, swimlane, and spaghetti maps.

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

SPPM, swimlane, and spaghetti maps must all be stable by 1.0.
Flowchart direct SVG rendering is deprecated and scheduled for removal in 0.2.0.

## Compatibility And Deprecation

Pre-1.0 releases may change public behavior, but each change must have a documented migration path.
Public deprecations normally remain available for at least one complete minor release before removal.
Security or correctness fixes may use an accelerated removal path with explicit release notes.

The 1.0 release removes scheduled deprecated behavior, legacy aliases, and compatibility paths that do not belong in the stable public surface.
New compatibility shims are not introduced during the 0.9 release-hardening cycle unless required to fix a release-blocking defect.

## Telemetry And Privacy

Telemetry alignment is a 1.0 prerequisite.
Telemetry input is treated as potentially sensitive data.

Before 1.0, FLO will document:

- The trusted-input boundary for trace and event data.
- The minimum event schema and field meanings.
- Identity, timestamp, lifecycle, and correlation semantics.
- Field-minimization and redaction guidance for sensitive data.

## Release Glide Path

### 0.2: Renderer Consolidation

- Remove the deprecated flowchart rendering surface.
- Complete shared SVG and renderer-platform primitives.
- Publish renderer tier definitions and capability expectations.
- Establish swimlane as a maintained renderer.
- Define direct SVG determinism and golden-artifact regression strategy.

### 0.3: Static Analytics Foundation

- Deliver canonical IR analysis for handoffs, rework, path length, and step classification.
- Produce analysis-oriented diagnostics and reports.
- Stabilize the analysis output schema and representative fixture corpus.

### 0.4: Telemetry Model

- Define and validate the minimum telemetry event schema.
- Document model-to-trace identity and correlation rules.
- Deliver trace-alignment prototypes and conformance fixtures.

### 0.5: Telemetry Analysis

- Support trace-derived transition frequencies, dwell or wait measures, and rework rates.
- Publish telemetry import and alignment report contracts.
- Complete privacy posture, trusted-input guidance, and redaction recommendations.

### 0.6: Renderer Stabilization

- Move SPPM, swimlane, and spaghetti to the stable renderer tier.
- Add visual-invariant coverage for node-label legibility, overlap, clipping, and
	lane-frame containment on top of the established deterministic and golden-artifact gates.
- Publish the renderer capability matrix and renderer compatibility guarantees.

### 0.7: Language, IR, And CLI Freeze Candidate

- Freeze the proposed 1.0 language, canonical IR, schema, and CLI contracts.
- Finalize the standard and verbose node-content policy, including approved
	queue-detail fields and layout requirements for verbose rendering.
- Remove or migrate legacy authoring aliases according to documented deprecation policy.
- Expand conformance coverage for stable contracts and supported migration paths.

### 0.8: Ecosystem And Operational Hardening

- Verify Python 3.14 support in CI and distribution artifacts.
- Require wheel and source-distribution installation smoke tests.
- Complete dependency automation, security reporting, contributor guidance, release process, and support policy.
- Add reproducibility and upgrade-path tests for public artifacts.

### 0.9: Release Candidate Hardening

- Freeze features.
- Accept only bug fixes, determinism corrections, documentation, test hardening, dependency or security remediation, release packaging, and previously announced deprecation removals.
- Resolve release-blocking test gaps, rendering defects, migration gaps, and documentation gaps.
- Publish the 1.0 migration guide and release-candidate checklist.

### 1.0: Final Polish And Stable Launch

- Remove all behavior scheduled for deprecation before 1.0.
- Finalize language, IR, CLI, renderer, telemetry, and support-policy compatibility guarantees.
- Complete conformance, deterministic artifact, visual-invariant, fuzz or property, package-install, security, and release checks.
- Publish stable support, upgrade, and release policies.

## 1.0 Release Gates

FLO does not release 1.0 until all of the following are true:

- The language, IR schema, CLI error contract, and telemetry schema are documented and covered by conformance tests.
- SPPM, swimlane, and spaghetti meet the stable renderer-tier criteria.
- Direct SVG and JSON outputs are byte-stable on the supported CI platform for the release corpus.
- The supported Python 3.14 installation path passes wheel and source-distribution smoke tests.
- Static analysis, test, coverage, determinism, artifact, fuzz or property, and security gates pass without unresolved release-blocking exceptions.
- Deprecated public behavior and legacy compatibility cruft scheduled for removal are gone.
- Governance, contribution, security-reporting, support, and release documentation are published and current.

## What Is Not A 1.0 Goal

This roadmap does not require FLO to become a workflow execution engine, scheduler, orchestrator, or simulation platform.
Future functionality must not weaken the stable language and artifact contracts established by 1.0.