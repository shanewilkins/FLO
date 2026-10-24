# Consistent diagnostic delivery: next sprint

Status: queued for the next sprint; implementation pending.
Recorded: 2026-10-23.
Release track: 0.4 White Belt stabilization; no sprint dates or patch version assigned.

The committed outcomes and acceptance criteria live in
[UR-086](../requirements/user_requirements.csv) and
[TR-117](../requirements/technical_requirements.csv). This document explains
implementation sequencing and review scenarios. It does not change the current
[CLI error contract](../specs/cli_error_contract.md).

## Need

FLO already has structured source errors, analysis findings, render reports,
logging, and runtime tracing. Their delivery differs by producer. A timing
warning visible in `flo inspect` can be absent from an ordinary render command;
render warnings have a separate logging path; some degraded-success messages
require verbose output. Users cannot reliably tell whether a successful command
has incomplete inputs or degraded output, and integrations cannot collect all
findings through one consistent operation-level report.

The missing-timing case makes this concrete: diagrams now show `?` for missing
applicable durations and retain measured zero, but rendering does not provide a
corresponding concise missing-timing warning. Missing optional waiting or setup
values are also absent from the existing `timing-incomplete` coverage warning.

## Existing building blocks

| Concern | Current implementation | Integration work |
| --- | --- | --- |
| Expected errors and exit codes | `src/flo/errors.py` | Preserve exception and exit-code mappings. |
| Source-aware diagnostics | `src/flo/source/diagnostics.py` | Preserve location, excerpt, field path, repair guidance, and include context. |
| Analysis findings | `src/flo/process/analysis/timing.py`, `structure.py`, and inspection reports | Adapt findings without losing producer-specific meaning. |
| Rendering findings | `src/flo/render/_diagnostics.py` and artifact metadata | Reuse reports and preserve degradation and partial-output context. |
| CLI delivery | `src/flo/app/cli.py` and `runtime_services.py` | Apply one visibility and aggregation policy at the command boundary. |
| Python callers | `src/flo/api.py` and render artifacts | Expose warnings without turning successful results into failures. |
| Observability | `src/flo/app/logging.py` and `telemetry.py` | Retain trace context without duplicating user-facing diagnostics or contaminating stdout. |

## Next-sprint work

- [ ] Inventory existing diagnostic codes, severities, delivery paths, and
  strict-mode behavior. Link overlapping obligations such as TR-029, TR-032,
  TR-053, TR-077, and TR-079 rather than creating replacement code families.
- [ ] Define a common operation-level diagnostic envelope and adapters for the
  existing typed source, analysis, and rendering records. Keep domain producers
  independent of the CLI and logging implementation.
- [ ] Define deterministic ordering, duplicate identity, aggregation, and
  visibility. One underlying finding should not be printed again merely because
  layout, rendering, and output handling each encountered it.
- [ ] Route actionable warnings to concise stderr output by default. Provide
  complete structured details to programmatic consumers and a documented
  machine-readable command path. Keep SVG/JSON payload stdout clean.
- [ ] Add the first integrated use case: aggregate missing applicable processing,
  queue, pre-task waiting, and setup fields into one timing warning per operation.
  Include omitted optional fields represented by `?`; do not warn for an
  explicitly measured zero merely because its numeric value is falsey.
- [ ] Make operation success depend on error severity rather than the presence
  of any diagnostic. The current `OperationResult.ok` treats any diagnostic as
  failure, so warning delivery needs an explicit compatibility review.
- [ ] Preserve existing fatal errors, exit codes, strict geometry failures, and
  privacy boundaries. Geometry strictness alone should not turn missing timing
  into an error.
- [ ] Add regression fixtures, CLI/API checks, documentation, and a release note
  together with implementation. Review warning volume on untimed starter models
  and on the book's Wash n' Fold diagram.

The first implementation slice covers existing producers and the missing-timing
use case. New measurement profiles, statistical computation, a new external
logging backend, global warnings-as-errors controls, and an audit of every
possible new warning condition are outside this sprint item.

## Review scenarios

| Input or condition | Planned user-visible result |
| --- | --- |
| Valid process with omitted applicable timing | Diagram is produced with `?`; one aggregated timing warning; exit 0. |
| Several missing optional wait/setup fields | Same nonfatal treatment; concise summary with field-level detail available. |
| Explicit integer or floating-point zero | Display zero; no missing-value warning for that field. |
| Malformed or non-finite declared duration | Existing source-aware validation error; exit 4; no misleading artifact. |
| Unsupported elapsed-time calculation, such as a cycle | Reason remains available in the analysis report and reaches the common delivery path without duplicate warnings. |
| Existing actionable render degradation | Warning remains visible on successful output; structured report identifies the artifact and affected entities. |
| Existing strict geometry failure | Existing rendering error and exit 5 are preserved. |
| Warning-only public API operation | Successful value remains available and success stays true; warnings are inspectable. |
| Repeated operation or reordered discovery of equivalent findings | Same diagnostic content and ordering, without repeated user-facing messages. |
| JSON/SVG stdout output | Parseable artifact payload; warnings use stderr or the documented structured diagnostic destination. |

## Verification and completion

The implementation is ready for acceptance when UR-086 and TR-117 have executable
coverage, the existing error/strictness tests still pass, and diagnostics remain
deterministic across CLI, API, and artifact reporting. Timing fixtures should
cover no timing at all, partially measured models, multiple missing fields,
measured zeros, invalid input, unavailable analysis, and disabled publication
footers. Hiding a diagram footer should not hide the command's warning.

Before implementation, the shared envelope shape, structured-output command
syntax, and compatibility handling for existing metadata/result fields need to
be specified in the current CLI/API contracts. Those interface details are
implementation decisions for this sprint, not claims about today's behavior.
