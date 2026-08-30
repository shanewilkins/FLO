# Model Inspection And Readiness

The model-inspection report is a deterministic summary of validated canonical
IR plus portable parser-owned source-composition context. It does not mutate
the model, execute the process, or turn source provenance and renderer advice
into canonical process semantics.

## Report contract

The initial report version is `0.1`. It includes:

- process identity, version, owner, business units, lanes, node count, and edge
  count;
- the entry source and root-relative included source paths;
- declared item, resource, and location counts and stable IDs;
- deterministic non-rework paths supplied by structural analysis;
- the default view and sorted named render-intent views; and
- structural diagnostics plus readiness for any explicitly requested analysis
  or diagram.

The report emits sorted, indented JSON with a trailing newline or concise text.
Identical validated input, portable source composition, and request options
produce byte-identical JSON.

## Validation and missing data

Ordinary parsing, composition, compilation, semantic validation, and schema
validation complete before a report is built. Invalid authored data therefore
fails through the ordinary structured error path rather than appearing as a
successful readiness result.

A valid model can still be incomplete for a projection. Readiness uses three
statuses:

- `ready`: required data and supported semantics are available;
- `partial`: the operation remains meaningful but optional data or a bounded
  semantic limitation affects completeness; and
- `unavailable`: required data or runtime support is absent.

Findings classify missing required data, missing optional data, semantic
limitations, and unsupported capabilities separately. Readiness advice is a
derived analysis result and never changes authored handoff, rework, location,
timing, or flow semantics.

## CLI

`flo inspect <path> --analysis model` emits the report. Optional
`--for-analysis timing|structure` and
`--for-diagram sppm|swimlane|spaghetti|value_stream` requests add readiness
results. Those options are rejected for timing and structural reports so their
meaning cannot silently change based on command context.

The entry source is reported as a portable filename, `<stdin>`, or `<memory>`.
Includes are root-relative paths in stable order; absolute checkout paths are
not part of deterministic report identity.
