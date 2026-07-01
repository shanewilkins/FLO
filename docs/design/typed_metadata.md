# Typed Metadata (design)

Status: draft

This note provides human guidance only. The authoritative typed metadata
contracts live in `schema/flo_types.json`.

This is a draft explanatory guide.
Schema remains the authoritative contract for tooling.

## Purpose

This document explains the machine-readable typed metadata defined in
`schema/flo_types.json`, why we have it, and how authors and tools should use
it. The JSON schema is the authoritative form for tooling; this doc provides
human-friendly guidance and examples.

## Why typed metadata

- Enables deterministic validation and clearer diagnostics during parsing.
- Supports quantitative analyses (SLA aggregation, latency sums) and tooling.
- Keeps freeform annotations possible while encouraging a small set of
  well-typed keys for analytics and telemetry mapping.

## Key typed fields (recommended)

- `activity_key` (string, node): stable key used to align telemetry events to a node.
- `sla_target_seconds` (duration/number, node/process): expected time budget for the step/process.
- `value_class` (enum string, node/process): high-level classification used in Lean analysis (VA/RNVA/NVA/unknown).
- `handoff` (boolean, edge): indicates a cross-lane or responsibility handoff.
- `handoff_type` (string, edge): optional typed handoff classification such as
  responsibility, information, material, system, location, or mixed.
- `expected_latency_seconds` (duration/number, edge): typical latency to traverse the edge.
- `rate` (number, rework edge): rework proportion on a rework loop, expressed as a fraction from 0 to 1.
- `reason` (string, rework edge): short cause label for why the rework loop occurs.
- `count` (number|string, rework edge): observed rework count, either as a positive number or compact text such as `3 per 40 cases`.
- `frequency` (string, rework edge): frequency text such as `avg 0.12 loops/case`.
- `note` (string, rework edge): supporting observation note shown in the rendered rework data box.
- `materials`, `equipment`, `locations`, and `workers` (process): current
  typed process-level collections used by the v0.1 schema.

## Typing and coercion rules

- Parser behavior: attempt safe coercions (e.g., numeric string → number). If
  coercion fails, emit a validation error.
- Unknown metadata keys: allowed but flagged with a `warning: untyped_key` so
  authors can consider adding types to the schema.

## Schema location and usage

- Machine schema: `schema/flo_types.json` — consumed by validators and CI.
- IR schema: `schema/flo_ir.json` defines structure (nodes/edges). Typed
  metadata complements the IR schema by describing common metadata keys.

## Examples

- Node metadata example:

  {
    "activity_key": "verify",
    "sla_target_seconds": 3600,
    "value_class": "VA"
  }

- Edge metadata example:

  {
    "handoff": true,
    "expected_latency_seconds": 300,
    "rate": 0.08,
    "reason": "Missing approvals",
    "count": "3 per 40 cases",
    "frequency": "avg 0.12 loops/case"
  }

- Process metadata example:

  {
    "sla_target_seconds": 86400,
    "business_impact": "high",
    "value_class": "VA"
  }

## Best practices

- Prefer stable, compact `id`s for nodes and use `activity_key` to map events.
- Keep metadata small and typed for critical analysis fields; use freeform
  metadata for ad-hoc notes but expect warnings.
- Use `sla_target_seconds` consistently as seconds for easier aggregation.
- For SPPM rework loops, attach rework observations to edge metadata rather than the rework task node so the renderer can place the data box on the dashed loop itself.

## Extending the typed schema

- Add new keys to `schema/flo_types.json` with a short justification and an
  example. Each addition should be explainable in one paragraph and map to IR
  fields or analysis needs.

## Tooling notes

- Validators should load both `schema/flo_ir.json` and `schema/flo_types.json`.
- Editors/IDEs can surface `recommended_keys` and show warnings for untyped
  metadata.

## Next steps

- Integrate typed-schema checks into the CLI `flo validate` command.
- Add examples demonstrating invalid metadata and expected diagnostics.
- See `docs/design/render_intent_schema.md` for the proposed source-level
  render/publication intent schema and multi-view render design.

Document version: accepted explanatory guide
