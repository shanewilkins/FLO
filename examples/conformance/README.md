# FLO Conformance Fixtures

This directory contains canonical v0.1 fixture files for conformance testing.

Layout:

- `valid/`: files that should pass parse + compile + validation
- `invalid/`: files that should fail validation with deterministic diagnostics

Notes:

- These fixtures are intentionally separate from top-level `examples/*.flo` so
  existing smoke/integration tests can keep using stable examples.
- Test suites should load fixtures directly from these folders when asserting
  specific validation rules.

Current coverage intent:

- `valid/` should include narrow fixtures for canonical item/resource
  declarations, consumes/produces, handoff-bearing edges, parallel
  split/join structure, and rework-plus-handoff coexistence.
- `invalid/` should include narrow fixtures for undeclared references, invalid
  item/resource kinds, malformed handoff values, malformed parallel structure,
  and malformed rework metadata.

Authoring rule:

- Prefer adding one small fixture per rule over building one large mixed-case
  negative example.
