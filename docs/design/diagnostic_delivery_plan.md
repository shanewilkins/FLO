# Consistent diagnostic delivery

Status: implemented and locally verified; release acceptance remains separate.
Recorded: 2026-10-23.
Verification updated: 2026-10-25.
Release track: 0.4 White Belt stabilization; no sprint dates or patch version assigned.

The committed outcomes and acceptance criteria live in
[UR-086](../requirements/user_requirements.csv) and
[TR-117](../requirements/technical_requirements.csv). This document explains
implementation sequencing and review scenarios. The implemented interface is
specified in the [CLI error contract](../specs/cli_error_contract.md).

## Need

Before this work, FLO had structured source errors, analysis findings, render reports,
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

## Completed work

- [x] Inventory existing diagnostic codes, severities, delivery paths, and
  strict-mode behavior. Link overlapping obligations such as TR-029, TR-032,
  TR-053, TR-077, and TR-079 rather than creating replacement code families.
- [x] Define a common operation-level diagnostic envelope and adapters for the
  existing typed source, analysis, and rendering records. Keep domain producers
  independent of the CLI and logging implementation.
- [x] Define deterministic ordering, duplicate identity, aggregation, and
  visibility. One underlying finding should not be printed again merely because
  layout, rendering, and output handling each encountered it.
- [x] Route actionable warnings to concise stderr output by default. Provide
  complete structured details to programmatic consumers and a documented
  machine-readable command path. Keep SVG/JSON payload stdout clean.
- [x] Add the first integrated use case: aggregate missing applicable processing,
  queue, pre-task waiting, and setup fields into one timing warning per operation.
  Include omitted optional fields represented by `?`; do not warn for an
  explicitly measured zero merely because its numeric value is falsey.
- [x] Make operation success depend on error severity rather than the presence
  of any diagnostic. `OperationResult.ok` retains successful values for
  warning/info-only results; a missing value or error remains unsuccessful.
- [x] Preserve existing fatal errors, exit codes, strict geometry failures, and
  privacy boundaries. Geometry strictness alone should not turn missing timing
  into an error.
- [x] Add regression fixtures, CLI/API checks, documentation, and a release note
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

### Delivery and compatibility decisions

- The architecture-neutral `DiagnosticReport` adapts existing source, analysis,
  and render records without replacing producer-owned types or codes.
- Reports sort by severity (error, warning, info), stage, code, source, field
  path, and serialized record content. Duplicate identity includes all record
  content except delivery stage; differing evidence remains distinct.
- `--diagnostics-format json` emits one versioned operation report to stderr,
  including an empty report on clean success. Default text shows warnings;
  verbose text also shows informational findings. Payload stdout stays separate.
- Existing `validate --format json` source records, render metadata, and
  `run_content` tuples remain supported. Python results expose `.report`;
  render artifacts expose `.diagnostic_report` without printing.
- Artifact metadata adaptation lives beside the artifact contract. Timing
  attachment depends on that contract, not vice versa, keeping render siblings
  acyclic.

### Local verification

On 2026-10-25, the full suite passed with 1,333 tests and 94.01% source
coverage (90% required). Focused report/delivery coverage passed 24 tests.
All 11 import contracts, architecture responsibilities, source typing, Ruff
lint/format checks, docstrings, unused-code checks, and strict documentation
governance passed. The SPPM drift gate matched all 13 cases / 26 committed files.
These checks do not replace final installed-package/platform release acceptance.
