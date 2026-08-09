# Process Telemetry Event Contract

Purpose: define the normative semantic contract for observed process events and
their alignment to canonical FLO models.

Lifecycle: accepted for the 0.4 telemetry-model and MVP boundary. Aggregate
observed-process analysis remains scheduled for 0.5.

## Authority and ownership

- `schema/flo_trace.json` is the machine-readable structural authority.
- This specification is the semantic authority for field meaning, alignment,
  lifecycle, and conformance behavior.
- The Core Model/IR maintainer is accountable for both authorities. Until that
  role is separately staffed, the project maintainer holds it.
- Privacy handling is independently governed by
  `docs/policy/telemetry_privacy.md`.

Structural and semantic changes require Core Model/IR approval. A change that
also affects collection, persistence, disclosure, or redaction requires a
separate privacy-policy review even when the same person holds both roles.

## Product boundary

Designed FLO models and observed event datasets are separate artifacts.
Importing, validating, or aligning a trace must not silently alter FLO source,
canonical IR, model metadata, or stable identifiers.

Process telemetry is also distinct from FLO runtime observability. The optional
OpenTelemetry spans used to observe CLI and library execution do not define,
populate, or satisfy this process-event contract.

## Dataset envelope

A trace dataset contains:

- `schema_version`: currently `0.1`
- `events`: an ordered JSON array of event objects

An empty event array is structurally valid. Analysis may report that no useful
observations are available.

## Minimum event fields

Every event requires:

- `event_id`: unique, stable identity within the imported dataset
- `process_id`: identity of the designed process being observed
- `case_id`: identity of one observed process instance
- `activity_key`: stable activity identity used for explicit model alignment
- `timestamp`: RFC 3339 date-time including a UTC offset
- `lifecycle`: one of `start`, `complete`, `cancel`, or `fail`

Optional fields are:

- `process_version`: modeled process version when known
- `correlation_id`: cross-system or cross-message correlation identity
- `source`: source-system identity
- `attributes`: untrusted, potentially sensitive source-specific data

`event_id`, `process_id`, `case_id`, `activity_key`, and any supplied optional
identity field must be non-empty. Event IDs must be unique after parsing.

If `process_version` is absent, the import operation must receive an explicit
target model version. FLO must not guess a version from names, timestamps, or
repository state.

## Timestamp and ordering semantics

- Timestamps represent the observed event instant, not import time.
- Parsers must reject timestamps without an explicit UTC offset.
- Implementations may normalize timestamps to UTC internally.
- Deterministic ordering is ascending normalized timestamp followed by
  `event_id` as the stable tie-breaker.
- Equal timestamps are valid and do not imply event equivalence.

## Lifecycle semantics

- `start`: observed commencement of an activity
- `complete`: successful observed completion
- `cancel`: activity stopped without successful completion
- `fail`: activity terminated because of an observed failure

An activity may have only completion-like observations when the source system
does not emit starts. FLO must report which measures are unavailable rather
than synthesizing missing lifecycle events or durations.

## Model alignment

Alignment is explicit and deterministic:

1. An `activity_key` equal to a canonical node ID aligns directly to that node.
2. Any other `activity_key` requires an explicit import mapping to one canonical
   node ID.
3. FLO must not infer alignment from display names, labels, list position, or
   approximate text matching.

One activity key maps to at most one node within a selected model version.
Unknown or ambiguous mappings remain unresolved and appear in the alignment
report. Non-strict alignment may continue with resolved events; strict
alignment fails if any selected event is unresolved.

The alignment report must identify at least:

- target process ID and version
- total, resolved, and unresolved event counts
- unknown activity keys in deterministic order
- duplicate event IDs
- lifecycle or timestamp validation failures

## Release boundary

The 0.4 contract includes:

- structural and semantic validation
- local, explicit trace import
- deterministic model alignment
- conformance fixtures and alignment reports

The 0.5 contract adds aggregate transition frequency, dwell or wait, and rework
analysis. Those analyses consume aligned observations and must not feed inferred
values back into canonical IR without a separate explicit export/import action.

## Example

```json
{
  "schema_version": "0.1",
  "events": [
    {
      "event_id": "evt-001",
      "process_id": "order-fulfillment",
      "process_version": "2026.1",
      "case_id": "case-1042",
      "activity_key": "pack-order",
      "timestamp": "2026-08-09T15:04:05Z",
      "lifecycle": "complete",
      "source": "warehouse-system"
    }
  ]
}
```

## Privacy and output handling

All imported fields are potentially sensitive. Collection, persistence,
redaction, logging, reporting, and artifact-disclosure rules are defined in
`docs/policy/telemetry_privacy.md` and the CLI stream contract.
