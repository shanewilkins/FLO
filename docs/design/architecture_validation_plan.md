# Architecture validation before the next release

Status: assessment and R1–R3b complete; clean-candidate acceptance R4 in progress.

Results: [validation report](architecture_validation.md),
[machine evidence](architecture_validation_evidence.json), and
[accepted ownership clarification](adr/render_layout_finalization.md).

This plan implements the acceptance work required by TR-118 and the
[release architecture integrity policy](../policy/release_architecture_integrity.md).
It does not declare existing drift accepted or architecture integrity verified.

## Objective and stopping point

Establish which current architecture obligations apply to the shipped product,
identify implementation drift, and produce a reviewed ownership and migration
plan with executable acceptance criteria. Resolve blocking findings in explicit
follow-up refactoring slices before release. This assessment must not expand into
an unbounded rewrite or an engine replacement without supporting evidence.

## Validation sequence

- [x] Inventory effective decisions across process, source, rendering, application
  orchestration, optional integration boundaries, and publication. Reconcile the
  package ADR, renderer boundaries, target architecture, and implemented contracts;
  distinguish current obligations from proposed/future target structures.
- [x] Trace source -> canonical IR -> validation/analysis -> projection -> layout
  -> final geometry -> SVG/publication and diagnostics. Identify the owner,
  accepted input, produced output, mutation, and permitted dependencies at each
  stage. Review the whole repository's boundary enforcement as the first baseline.
- [x] Follow the same three representative inputs through CLI, Python rendering,
  golden generation, and installed-package paths: linear flow, width-wrapped
  Wash n' Fold correction, and long-label rework. Record exactly where geometry,
  semantic interpretation, options, or diagnostic policy can change.
- [x] Classify each finding as a violation of an effective decision, an ambiguous
  or conflicting decision needing clarification, or nonblocking implementation
  debt. Attach code evidence and observable consequences; do not infer findings
  solely from file size or passing/failing imports.
- [x] Resolve the ELK/FLO layout ownership wording. Preserve the accepted split
  between diagram policy, layout, graphics emission, and composition. Determine
  how bounded FLO-specific layout rules and authoritative final geometry fit that
  split before changing the architecture documents or implementing a new contract.
- [x] Propose the smallest concrete contract and ownership changes needed to
  eliminate confirmed violations. Review whether a single orchestration path and
  an inspectable finalized geometry result address the observed defects; names
  and package shapes remain implementation decisions until that review.
- [x] Add assessment probes for current responsibility/ownership violations,
  entrypoint parity, IR preservation, and browser-runtime boundaries; retain the
  existing dependency checks. The probes identify open AF-001–003 and deliberately
  fail the architecture check. Target finalized-geometry consumption and common
  execution call-through tests are acceptance work for remediation R1–R3, not
  claims about an already implemented final-geometry contract.
- [x] Record findings, decisions, remediation slices, and acceptance evidence.
  Gate release on closing the violations and verifying the final clean candidate.

## Initial evidence to investigate

These are observed symptoms, not completed audit dispositions:

| Observation | Evidence | Architectural question |
| --- | --- | --- |
| Several stages change positions and routes | `src/flo/render/layout_core/elk.py`, `src/flo/render/sppm/rows.py`, `src/flo/render/sppm/row_routes.py`, `src/flo/render/sppm/edges.py` | Who owns final placement, routing, attachment, and annotation geometry? |
| Golden generation still reconstructs the public rendering sequence | `scripts/build_sppm_baseline_artifacts.py`, `src/flo/render/__init__.py` | How can diagnostic traces and goldens use the production orchestrator without duplicating it? |
| Intermediate layout and emitted geometry differ | `src/flo/render/sppm/renderer.py`, `scripts/check_sppm_geometry.py` | Which typed result is authoritative and inspectable before SVG emission? |
| SPPM policy lives in nominally neutral core modules | `src/flo/render/layout_core/elk.py`, `elk_sppm_helpers.py`, `wrapped_rework.py` | Is policy ownership consistent with renderer-owned conventions and narrow engine adapters? |
| Import checks and size/complexity exclusions cover different risks | `pyproject.toml`, `scripts/check_file_length.py`, `scripts/check_complexity.py` | Which responsibility violations escape existing enforcement, and which exclusions need a remediation owner? |

The existing entrypoint parity, semantic, geometry, and installed-wheel checks
are evidence to retain. Their green status must not be represented as completion
of this architecture review.

## Deliverables

1. An effective-architecture inventory and one stage/responsibility map.
2. A findings register with severity, governing decision, affected code, and
   explicit disposition.
3. Accepted clarifications and a bounded remediation plan for confirmed drift.
4. Focused boundary checks and evidence sufficient to close each finding.
5. A blocked candidate assessment record with runtime/document fingerprints,
   installed-package identity, and explicit outstanding findings. Immutable clean
   candidate and platform evidence remain required for later release acceptance.

The assessment slice ends at the reviewable findings and remediation plan.
The release gate stays open until remediation and candidate acceptance are done.

## Assessment disposition

The validation slice is complete. Package and current import checks pass;
functional output agrees across all four traced paths. R1 closes AF-003 through shared production execution and detached stage capture.
R2 closes AF-002 through diagram-owned policy and explicit neutral engine inputs.
R3a finalizes nodes/routes and exposes routed geometry before SVG emission.
R3b closes AF-001 with a complete final scene and pure SVG consumption.
Immutable clean-candidate acceptance (R4) is the remaining architecture gate.
No production renderer changes were made to make this assessment appear green.
