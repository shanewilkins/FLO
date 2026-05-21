# FLO Artifact Taxonomy

Status: accepted shared taxonomy note

## Purpose

Define the artifact classes FLO is expected to produce, which layer owns each
artifact, and which artifacts are canonical versus derived.

This note complements `docs/policy/artifact_scope.md`.

- `docs/policy/artifact_scope.md` answers: does this artifact belong in FLO at
  all?
- This note answers: if it does belong in FLO, what kind of artifact is it and
  how should contributors think about it?

## Taxonomy Overview

FLO produces four broad artifact families:

1. Canonical model artifacts
2. Standalone presentation artifacts
3. Composed publication artifacts
4. Test and regression artifacts

These families should remain distinct. A contributor should not treat a test
fixture as the same kind of thing as a user-facing deliverable, and should not
treat a derived image as the canonical model.

## 1. Canonical Model Artifacts

These artifacts represent the process model itself or a direct serialized form
of it.

Examples:

- canonical in-memory IR
- schema-aligned JSON export
- source `.flo` documents and composed source inputs

Ownership:

- language semantics: `docs/specs/core_language.md`
- serialized structure: `schema/flo_ir.json`
- compiler and validation behavior: `src/flo/compiler/`

Canonicality:

- canonical: source `.flo` plus canonical in-memory IR
- canonical serialized form: JSON export aligned to `schema/flo_ir.json`
- derived: any convenience summaries or diagnostics generated from the model

Rule:

- No presentation artifact should be treated as the canonical process model.

## 2. Standalone Presentation Artifacts

These artifacts are user-facing diagram or summary outputs intended to stand on
their own.

Examples:

- flowchart render
- swimlane render
- spaghetti map render
- SPPM standalone figure
- ingredients summary
- movement summary

Expected output forms:

- SVG as the preferred standalone vector graphic
- PNG and PDF as derived convenience forms
- DOT as a backend-oriented projection while Graphviz remains in active use
- plain-text or structured summary exports where the artifact is not graphical

Ownership:

- artifact meaning: `docs/specs/`
- renderer design and backend strategy: `docs/design/`
- implementation: `src/flo/render/` and `src/flo/export/`

Canonicality:

- canonical standalone graphic target: SVG
- derived convenience forms: PNG, PDF
- transitional backend artifact: DOT

Rule:

- Treat DOT as an implementation-era projection, not the long-term primary
  user-facing artifact.

## 3. Composed Publication Artifacts

These artifacts assemble one or more standalone figures into a page-aware
document or publication package.

Examples:

- multi-page SPPM publication output
- future report-ready publication bundles
- publication source emitted for a document compositor
- final publication PDF

Ownership:

- publication planning and contracts: `docs/design/publication_model.md`
- render-platform layering: `docs/design/render_platform_target_architecture.md`
- composition implementation: future `src/flo/publish/`

Canonicality:

- canonical composition plan: publication plan and figure-placement model
- canonical page-oriented deliverable: composed PDF or equivalent document
- derived intermediates: compositor-specific source such as Typst input

Rule:

- Publication artifacts are not just oversized diagrams. They are a separate
  artifact family with page furniture, continuation behavior, and composition
  rules.

## 4. Test And Regression Artifacts

These artifacts exist to validate behavior, not to serve as end-user outputs.

Examples:

- reference `.flo` fixtures
- conformance fixtures (valid and invalid)
- rendered fixture outputs under `renders/`
- coverage and baseline reports

Ownership:

- fixture taxonomy: `examples/README.md`
- tests and regression harnesses: `tests/`
- supporting scripts: `scripts/`

Canonicality:

- canonical fixture source: files under `examples/`
- derived regression outputs: files under `renders/`, coverage artifacts, and
  report baselines

Rule:

- Test artifacts may anchor regressions, but they do not define product meaning
  unless a normative spec or policy explicitly says so.

## Primary Versus Derived Artifacts

Contributors should use this decision order:

1. Primary model truth: FLO source plus canonical IR
2. Primary normative contracts: policy, specs, schema
3. Primary standalone graphic target: SVG
4. Primary publication deliverable: composed document output
5. Derived convenience or transitional outputs: DOT, PNG, backend-specific
   intermediates, baseline render files

## Ownership Matrix

| Artifact family | Primary owner | Typical location |
|---|---|---|
| canonical model semantics | specs + schema | `docs/specs/`, `schema/` |
| renderer and export behavior | specs + design + code | `docs/specs/`, `docs/design/`, `src/flo/render/`, `src/flo/export/` |
| publication composition | design + future implementation | `docs/design/`, `src/flo/publish/` |
| fixtures and regression assets | examples + tests + scripts | `examples/`, `tests/`, `renders/`, `scripts/` |

## Repository Placement Guidance

Use these placement rules when adding artifacts or artifact-oriented docs.

- Put normative meaning in `docs/specs/`.
- Put governance and source-of-truth rules in `docs/policy/`.
- Put implementation-shaping artifact taxonomy, migration, or composition notes
  in `docs/design/`.
- Put user-facing summaries in `README.md` or `docs/User_Manual.md`.
- Put canonical example fixtures in `examples/`.
- Put derived regression outputs in `renders/` or other generated artifact
  locations.

## Current Direction

Given the accepted render-platform direction:

- SVG is the intended primary standalone graphics artifact.
- PDF remains a primary composed-publication deliverable.
- DOT remains a current implementation artifact while Graphviz is still active.
- Typst or similar compositor input should be treated as an intermediate
  composition artifact rather than the end-user deliverable.

## References

- `docs/policy/artifact_scope.md`
- `docs/policy/authoritative_artifacts.md`
- `docs/design/publication_model.md`
- `docs/design/render_platform_target_architecture.md`
- `examples/README.md`