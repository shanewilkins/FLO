# Typed Metadata (design)

Purpose
-------

This document explains the machine-readable typed metadata defined in
`schema/flo_types.json`, why we have it, and how authors and tools should use
it. The JSON schema is the authoritative form for tooling; this doc provides
human-friendly guidance and examples.

Why typed metadata
-------------------

- Enables deterministic validation and clearer diagnostics during parsing.
- Supports quantitative analyses (SLA aggregation, latency sums) and tooling.
- Keeps freeform annotations possible while encouraging a small set of
  well-typed keys for analytics and telemetry mapping.

Key typed fields (recommended)
------------------------------

- `activity_key` (string, node): stable key used to align telemetry events to a node.
- `sla_target_seconds` (duration/number, node/process): expected time budget for the step/process.
- `value_class` (enum string, node/process): high-level classification used in Lean analysis (A/B/C/unknown).
- `handoff` (boolean, edge): indicates a cross-lane or responsibility handoff.
- `expected_latency_seconds` (duration/number, edge): typical latency to traverse the edge.

Typing and coercion rules
-------------------------

- Parser behavior: attempt safe coercions (e.g., numeric string → number). If
  coercion fails, emit a validation error.
- Unknown metadata keys: allowed but flagged with a `warning: untyped_key` so
  authors can consider adding types to the schema.

Schema location and usage
-------------------------

- Machine schema: `schema/flo_types.json` — consumed by validators and CI.
- IR schema: `schema/flo_ir.json` defines structure (nodes/edges). Typed
  metadata complements the IR schema by describing common metadata keys.

Examples
--------

- Node metadata example:

  {
    "activity_key": "verify",
    "sla_target_seconds": 3600,
    "value_class": "A"
  }

- Edge metadata example:

  {
    "handoff": true,
    "expected_latency_seconds": 300
  }

- Process metadata example:

  {
    "sla_target_seconds": 86400,
    "business_impact": "high",
    "value_class": "A"
  }

Best practices
--------------

- Prefer stable, compact `id`s for nodes and use `activity_key` to map events.
- Keep metadata small and typed for critical analysis fields; use freeform
  metadata for ad-hoc notes but expect warnings.
- Use `sla_target_seconds` consistently as seconds for easier aggregation.

Extending the typed schema
--------------------------

- Add new keys to `schema/flo_types.json` with a short justification and an
  example. Each addition should be explainable in one paragraph and map to IR
  fields or analysis needs.

Tooling notes
-------------

- Validators should load both `schema/flo_ir.json` and `schema/flo_types.json`.
- Editors/IDEs can surface `recommended_keys` and show warnings for untyped
  metadata.

Next steps
----------

- Integrate typed-schema checks into the CLI `flo validate` command.
- Add examples demonstrating invalid metadata and expected diagnostics.

Document version: draft (v0.0)
