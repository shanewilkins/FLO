# FLO CLI Error Contract

Purpose: define the normative CLI-facing error classes, exit-code meanings, and
stream/output behavior for FLO commands.

## Error class hierarchy

Implemented in `src/flo/errors.py`:

- `DomainError`
  - Base class for expected domain-level errors.
- `CLIError`
  - CLI-facing error wrapper with exit code mapping.
- `ParseError`
  - Parse/loading failures.
- `CompileError`
  - Adapter-to-model compilation failures.
- `ValidationError`
  - Semantic/schema validation failures.
- `RenderError`
  - Output rendering failures.

## Exit codes

Current mappings:

- `0` (`EXIT_SUCCESS`): success
- `1` (`EXIT_USAGE`): CLI usage or argument issues
- `2` (`EXIT_PARSE_ERROR`): parse error
- `3` (`EXIT_COMPILE_ERROR`): compile error
- `4` (`EXIT_VALIDATION_ERROR`): validation error
- `5` (`EXIT_RENDER_ERROR`): render or export I/O/rendering error
- `70` (`EXIT_INTERNAL_ERROR`): unexpected internal failure

## Stream conventions

- Primary command output and artifacts are written to `stdout` unless an
  explicit output destination is used.
- Diagnostics and errors are written through the CLI error path, which is
  `stderr`-oriented.
- Telemetry or logging output must not be emitted on `stdout` when commands
  return payloads such as SVG or JSON.
- Process-event inputs and raw attributes must not appear in stdout payloads,
  stderr diagnostics, logs, runtime spans, or ordinary artifacts except through
  an explicit telemetry-derived export permitted by the privacy policy.
- Input `-` means read from `stdin`.
- Output `-` means write to `stdout`.

## Render vs export contract

- Renderers and exporters are separate concerns and use separate registries.
  - Renderers (human-readable visualization) live under `src/flo/render`.
  - Exporters (machine-readable or report-style projections) live under
    `src/flo/process/export`.
- `--diagram` supports `swimlane`, `spaghetti`, and `sppm` for render output.
- With no explicit diagram or source render default, `flo render` selects
  `sppm`.
- `--profile`, `--detail`, `--orientation {lr,tb}`, `--show-notes`,
  `--subprocess-view`, shared autoformat controls (`--layout-wrap`,
  `--layout-max-width-px`, `--layout-target-columns`, `--layout-width`,
  `--layout-height`, `--layout-overflow`), and all SPPM render controls are
  render-only options.
- If `--export json`, `--export ingredients`, or `--export movement` is
  selected, render-only options are rejected with usage exit code `1`.

## Renderer policy contract (pre-1.0)

- Rework edges render as dashed lines.
- Rework classification precedence is explicit metadata first, inferred back-edge
  fallback second.
- Explicit rework semantics override inferred classification when they differ.
- Exact single-page SPPM bounds reflow before scaling. The default `safe-fit`
  policy preserves aspect ratio, scales only to the `0.75` legibility floor,
  and otherwise returns exit code `5` with requested bounds, natural bounds,
  required scale, and the floor. `error`, `expand`, and unrestricted `scale`
  remain explicit alternatives; `paginate` is publication-only.

## Validation diagnostics

### Operation diagnostic report

`--diagnostics-format text|json` applies to render, export, validate, and inspect
commands and the implicit render entry point. Text is the default: actionable
warnings are visible on stderr without verbose mode; informational findings are
visible with verbose mode. JSON emits one report to stderr, including an empty
report for a successful operation with no findings. Artifact/report stdout
remains independently parseable. The existing `validate --format json` source
diagnostic record remains supported; the explicit operation-report flag takes
precedence when both JSON switches are selected.

The report has `report_version: "0.1"`, warning/error/info counts, and a
deterministically ordered `diagnostics` array. Each record contains code (which
can be null for an uncoded existing failure), severity, stage, message, optional
source/line/column/excerpt/field-path/suggestion, include chain, and `details`
retaining producer-specific data. Equivalent records differing only in delivery
stage are emitted once. Existing diagnostic codes and fatal exit mappings remain
unchanged; warning-only success remains exit 0.

`timing-incomplete` aggregates omitted applicable processing, queue/hold waiting,
pre-task waiting, and setup fields into one warning per operation. Details list
affected node IDs and fields. Explicit integer/floating-point zero is measured;
invalid declared values retain fatal source validation instead of becoming
missing-value warnings. Footer visibility and strict geometry do not suppress
or promote this warning.

Python operation results expose the same report and treat only error severity
as diagnostic failure. Render artifacts retain producer metadata and add an
`operation_diagnostics` report; programmatic rendering does not print it.
The legacy application `run_content` tuple remains available, with warning text
in its third element; structured command consumers use `run_operation`.

Semantic validation uses stable diagnostic-style prefixes in messages (for
example `E1003`, `E1101`) so failures are easier to script against and triage.

### Structured diagnostic contract effective in 0.4

The 0.4 MVP extends parser, include, compiler, and validator diagnostics to one
typed record containing, where applicable:

- stable code and severity
- source file, line, and column
- FLO field path
- source excerpt
- suggested correction
- include chain

Human stderr and machine-readable output must be generated from the same typed
record so automation does not need to scrape prose. Sensitive telemetry input
and raw attributes remain excluded under the telemetry privacy policy.

Source structural failures carry authored field paths, including indices in
nested `steps` or `subnodes` and fields inside `attrs`. When that path is present
in the entry document, its YAML source mark supplies the location and excerpt.
Missing fields use the closest available enclosing mark. Existing compiler
codes and compile-error exit status remain in effect; model-library error dumps
are not the user-facing diagnostic format. Other producers retain their existing
location enrichment when adapted into the common operation report.
Included fragments undergo present-field shape validation before composition;
these structural failures retain compile exit `3`, originating-file paths,
authored indices, excerpts, and include chains. The complete composed model
still undergoes ordinary compiler and semantic/schema validation.

`flo validate --format json` emits this record as deterministic JSON through
the diagnostic stream. The default `--format text` renders the same record in
the compiler-style source excerpt format.

## Resource quantity diagnostics

Measured quantity canonical pairs retain the existing source/JSON syntax but
must now represent an equivalent amount. `E1222` reports incompatible
dimensions at `quantity.canonical_unit`; `E1223` reports unequal amounts at
`quantity.canonical_value` (relative tolerance `1e-9`, absolute tolerance `0`);
`E1224` reports a converted amount that overflows or underflows to zero.
These are validation failures (exit `4`), not warnings. The common report
retains authored collection/group paths, source excerpts, and repair guidance.
Existing malformed-value/unit codes remain unchanged. Export, inspect, and
render stop before producing a payload for invalid canonical quantities.

## Waiting evidence diagnostics

`E1509` rejects contradictory copies of one waiting `measurement_id`.
`E1510` rejects a queue duration unequal to its finite referenced sum or
contradictory aggregate identity. Both are semantic validation failures (exit
`4`) with source context and repair guidance. Duration equivalence uses
normalized seconds, relative tolerance `1e-9`, and absolute tolerance `0`.
Duplicate references, including whitespace-equivalent IDs, retain `E1305`.

`timing-projection-incomplete` warns when a queue-traversing path lacks the full
referenced work waiting evidence. Affected path elapsed totals and a complete
process lead-time range are unavailable. An unmeasured explicit hold joins the
aggregated `timing-incomplete` warning. These warnings do not turn otherwise
successful validate, inspect, export, or render operations into failures.

## Projection capability diagnostics

Unsupported diagram/backend projection requests are usage errors and must:

- return exit code `1` (`EXIT_USAGE`)
- include requested diagram and backend
- include supported backends for the requested diagram
- fail early before renderer dispatch

## Relationship to other documents

- Core language semantics live in `docs/specs/core_language.md`.
- Diagram meaning lives in the other files under `docs/specs/`.
- This contract is the normative CLI/interface companion to the implementation
  in `src/flo/errors.py`.
- Process-event semantics live in `docs/specs/telemetry_events.md`; privacy and
  disclosure rules live in `docs/policy/telemetry_privacy.md`.
