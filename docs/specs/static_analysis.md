# Static Analysis

This specification defines deterministic analysis derived from validated
canonical FLO IR. Static analysis describes the authored model; it does not
execute, simulate, schedule, or statistically infer process behavior.

## Timing analysis

The initial timing result is versioned as `0.1` and preserves three categories:

- cycle time: active processing time from `metadata.cycle_time`
- queue wait time: delay from `metadata.wait_time` on queue nodes
- setup or changeover time: the selected compatible setup field on work nodes

Supported source units `s`, `m`, `min`, `hr`, and `d` normalize to seconds in
the analysis result. A result retains per-node contributions, graph-wide
declared totals, path summaries, timing coverage, diagnostics, process identity,
and the changeover-exposure policy.

Graph-wide declared totals are an inventory of authored timing. They are not
automatically process lead time because mutually exclusive branches would be
double-counted.

## Path and lead-time rules

For a complete acyclic process without parallel split/join semantics, FLO
enumerates start-to-end paths in deterministic node-ID order.

- One complete path may produce one `modeled_lead_time_seconds` value.
- Multiple complete alternative paths produce minimum and maximum path lead
  times, not one falsely precise lead time.
- A work node is timing-complete when it declares valid `cycle_time`.
- A queue node is timing-complete when it declares valid `wait_time`.
- Missing expected timing keeps declared subtotals visible but prevents a
  complete modeled lead-time claim for the affected path.

Modeled path elapsed time is the sum of cycle, wait, and selected changeover
contributions encountered on that path. The initial exposure policy is one
declared changeover per visited work step. Batch allocation, product mix, and
changeover frequency require an explicit later policy and are not inferred.

## Refusal and diagnostic rules

The initial analyzer refuses to guess when elapsed-time meaning is unresolved:

- cyclic or rework flow requires an iteration policy
- parallel flow requires a critical-path and synchronization policy
- more than 256 acyclic paths requires a later bounded aggregation strategy
- multiple compatible setup/changeover fields produce an ambiguity diagnostic
- malformed timing is ignored with a diagnostic rather than coerced

For FLO 0.1 compatibility, setup/changeover lookup precedence is
`crossover_time`, then `transfer_time`, then `changeover_time`. The selected
source field is retained in each node contribution. This compatibility rule
does not make transfer and changeover conceptually identical; a future language
migration may separate them without silently changing historical results.

## Non-goals

Static timing analysis does not currently provide:

- queueing theory or capacity simulation
- observed or predicted dwell distributions
- batch-size allocation of setup time
- rework iteration estimates
- parallel critical-path elapsed time

Renderer and report surfaces should consume typed analysis results rather than
reimplement timing arithmetic. User-facing inspect reports and derived SPPM
footers are presentation surfaces over this contract.

## SPPM publication consumption

The SPPM renderer consumes this typed result for its derived timing footer. It
shows declared cycle, waiting, and changeover totals separately. A single
complete path produces one lead time; complete alternatives produce a range;
and unresolved elapsed-time semantics produce an unavailable value with a
pointer to `flo inspect` diagnostics. The renderer does not derive timing for a
partial projection from whole-process totals and does not create a timing
footer when the model declares no timing.

## Inspect command

`flo inspect <path>` runs the timing analysis after the ordinary parse,
compile, and validation pipeline. Its default `--format text` report is a
concise user-facing summary. `--format json` emits the analysis result as
deterministic, sorted, indented JSON with a trailing newline. The same input and
analysis options must produce byte-identical JSON.

The initial command surface accepts `--analysis timing`; the option is explicit
so later static analyses do not require changing the command shape. Input may
come from a path or stdin, and `-o/--output` may write either report format to a
file. Analysis diagnostics remain in the report payload and do not contaminate
machine-readable stdout.
