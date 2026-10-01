# Process Telemetry Privacy Policy

This policy governs observed process-event data imported under
`docs/specs/telemetry_events.md`.

## Authority and ownership

This file is the normative authority for process-telemetry trust boundaries,
data minimization, persistence, disclosure, and redaction.

The Security & Privacy maintainer is accountable for this policy. Until that
role is separately staffed, the release maintainer is accountable. Telemetry
schema approval and privacy approval are distinct reviews even when the same
person performs both.

## Trust boundary

All process-event inputs, including required identity fields and optional
attributes, are untrusted and potentially sensitive.

FLO does not assume that source-system identifiers are anonymous, that freeform
attributes are safe to disclose, or that an input file is authorized merely
because it is readable by the current process.

## Mandatory defaults

Process telemetry is local-first and opt-in:

- FLO performs no network egress, remote export, or exporter activation by
  default when importing, validating, aligning, or analyzing process events.
- The user must provide the trace input explicitly.
- Persisted telemetry-derived output requires an explicit destination.
- In-memory or streaming processing is preferred when persistence is not
  requested.
- Imported trace data never becomes canonical IR or model metadata implicitly.

FLO runtime observability is a separate subsystem. Enabling runtime spans does
not authorize process-event ingestion or disclosure, and process-event values
must not be copied into runtime span attributes by default.

## Data minimization

The minimum semantic fields in the trace specification are permitted for
validation and alignment. Implementations must read optional `attributes` only
when an explicitly selected analysis requires them.

Telemetry-derived reports use an allowlist. By default, reports may contain:

- modeled process and node identities
- aggregate counts, durations, rates, and conformance status
- deterministic validation codes and aggregate error counts

Raw source attributes, source payload fragments, direct personal identifiers,
and secret or credential material are not allowlisted.

## Logs, diagnostics, and command streams

- Raw event attributes and raw input records must not appear in logs,
  diagnostics, exceptions, runtime spans, or stack-context messages.
- Diagnostics identify field paths, validation codes, counts, and stable event
  IDs only when needed for remediation.
- Payload output remains on `stdout`; diagnostics remain on `stderr`.
- Trace data must not contaminate SVG, canonical JSON, publications, or other
  ordinary FLO artifacts.

## Persistence and derived artifacts

- FLO writes no raw or derived telemetry artifact without an explicit output
  destination.
- Output creation must not silently overwrite an unrelated existing artifact.
- Raw trace persistence is outside FLO's default workflow; the source system or
  user remains responsible for retention and deletion policy.
- Temporary processing data should remain in memory. If an implementation must
  use temporary storage, it must minimize content, restrict access, and remove
  the temporary artifact on normal completion.
- Derived artifacts must record whether identifiers are raw, redacted,
  pseudonymized, or aggregated.

## Redaction and pseudonymization

Redaction or pseudonymization occurs before persistence or disclosure, not as a
later cleanup step.

- Direct identifiers not required for the selected output are removed.
- Case and correlation identifiers are pseudonymized when row-level output is
  explicitly requested and raw identity is unnecessary.
- Pseudonyms must be stable within the declared analysis scope and must not
  expose the original value.
- Secret, token, credential, and unrestricted free-text values are removed,
  not merely masked visually.
- If the requested output cannot satisfy its declared privacy mode, FLO fails
  closed instead of writing a partially redacted artifact.

## Review triggers

Security & Privacy approval is required for changes that:

- add collected or persisted telemetry fields
- enable network transmission or a remote exporter
- expand an output allowlist
- place telemetry-derived content in SVG, JSON, publications, logs, or runtime
  spans
- change redaction, pseudonymization, retention, or temporary-storage behavior
- weaken explicit-input or explicit-destination requirements

## Verification requirements

Before the 1.0 gate, tests must prove:

- no default network egress
- no raw attributes in logs, diagnostics, runtime spans, or ordinary artifacts
- explicit destinations for persisted outputs
- allowlisted report fields only
- redaction or pseudonymization before persistence
- fail-closed behavior when the requested privacy mode cannot be honored
