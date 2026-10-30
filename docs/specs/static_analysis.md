# Static Analysis

This specification defines deterministic analysis derived from validated
canonical FLO IR. Static analysis describes the authored model; it does not
execute, simulate, schedule, or statistically infer process behavior.

## Structural analysis

The structural result is versioned as `0.1` and reports designed process
structure without telemetry:

- explicit handoff edges, including declared type and endpoint lanes;
- unmarked cross-lane edges as separately labeled handoff candidates, never as
  canonical handoffs;
- explicit rework edges, preserving their structured evidence;
- topology-derived cyclic regions, self-loops, and their canonical internal,
  entry and exit transitions;
- deterministic non-rework start-to-end paths with node, edge, and interior
  step counts; and
- every node's canonical kind, declared Lean `value_class`, aggregate counts,
  and IDs of classifiable work steps without a declared value class.

Path length means edge count. Structural analysis also publishes node and
interior-step counts so consumers do not need to guess which convention was
used. Identified rework edges are excluded from path enumeration because one
traversal is not an iteration policy. The initial analyzer refuses to report
path lengths when remaining non-rework flow is cyclic, uses parallel
split/join semantics, lacks valid start/end boundaries, has no complete path,
or exceeds 256 paths. Other structural findings remain available.

Handoff candidates and cyclic regions are analysis findings, not mutations of
canonical process semantics. Node declaration order does not establish a cycle
or imply rework. Only supplied rework relations classify transitions as rework. Identical validated IR produces byte-identical
sorted JSON, and analysis never mutates the input.

## Cycle-region contract

Structural and model inspection expose `cycle_regions` as a deterministic list
of maximal cyclic strongly connected components (SCCs). A singleton is included
only when it has a self-loop. Overlapping/nested cycles within the same SCC form
one region; individual simple cycles are not enumerated.

Each region has sorted `node_ids`, sorted `self_loop_node_ids`, and
`internal_edges`, `entry_edges`, `exit_edges`. Edge records retain every
canonical field and supplied evidence, including IDs, outcomes, routes, labels,
handoff/rework and extensions; parallel transitions remain distinct. An edge
between regions appears in the source region's exits and target region's
entries. No ordinal or synthetic cycle ID is exposed, so equivalent declaration
orders produce the same JSON. Result serialization detaches evidence from IR.

`structure-cycle-region` is informational, one per region. It replaces the
source-order `structure-ambiguous-backward-edge` warning. A cycle is not a
validation failure or an inferred rework declaration; path/timing limitations
retain their existing warnings. DAGs ordered against their flow direction have
no cycle finding. Text inspection reports region members, self-loops and
entry/exit counts; JSON retains full edge evidence.

Validation and analysis share a frozen NetworkX MultiDiGraph projection.
Transition ordinal keys map to original IR edges independently of optional
supplied IDs. Record degree and distinct-neighbor adjacency remain separate;
reachability/SCC operations never add missing endpoint nodes or rewrite IR.
Existing end/start, reachability, cardinality and declaration rules remain in
force. No stricter join/subprocess rules or execution semantics are introduced.

SCC condensation remains a separate derived view. Generated member IDs avoid
colliding with original node IDs; external transitions retain multiplicity and
evidence, and singleton self-loops survive when another component is collapsed.

## Timing analysis

The initial timing result is versioned as `0.1` and preserves three categories:

- cycle time: active processing time from `cycle_time`
- waiting time: work and queue/wait evidence from `wait_time`
- setup or changeover time: `changeover_time` on work nodes

Supported source units `s`, `m`, `min`, `hr`, and `d` normalize to seconds in
the analysis result. Duration `m` means minutes, not spatial metres. Conversion
does not rewrite authored values/units or expand the supported unit vocabulary.
A result retains per-node contributions, graph-wide
declared totals, path summaries, timing coverage, diagnostics, process identity,
and the changeover-exposure policy.
Each node also retains `declared_wait_time_seconds`, the normalized authored
waiting value before deduplication. Diagrams consume this field for local
waiting annotations; a suppressed contribution is not missing measurement data.

Graph-wide declared totals are an inventory of authored timing. They are not
automatically process lead time because mutually exclusive branches would be
double-counted.

## Timing states

Omitted duration fields remain absent in canonical exchange and produce null
category totals when no values were declared. A missing expected work, queue, or hold
duration produces `timing-incomplete`. Explicit null and malformed durations
are invalid, not omissions: the validated CLI rejects them, while analysis of
unvalidated IR emits `timing-invalid-duration`. Declared numeric zero remains
zero. An unavailable derived lead time is null with a reason, such as missing
or invalid inputs, cycles, parallel flow, or numeric overflow. Timing coverage
can be complete while a cycle or unsupported elapsed-time policy makes lead
time unavailable. None of these states supplies an implicit zero.

## Path and lead-time rules

For a complete acyclic process without parallel split/join semantics, FLO
enumerates start-to-end paths in deterministic node-ID order.

- One complete path may produce one `modeled_lead_time_seconds` value.
- Multiple complete alternative paths produce minimum and maximum path lead
  times, not one falsely precise lead time.
- A work node is timing-complete when it declares valid `cycle_time`.
- A queue or explicit `wait` hold is timing-complete when it declares valid
  `wait_time`; measured zero is valid.
- A queue/wait profile using `{ref: work.wait_time}` projects the work waiting
  evidence directly, without a second copied measurement.
- Deduplication is path-local. An uncovered reference produces a
  timing-projection-incomplete warning and leaves that path elapsed total
  unavailable, while retaining known category subtotals and visible evidence.
- Independent authored waiting profiles remain independent contributions.
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
- malformed timing in directly supplied IR is ignored with a diagnostic rather
  than coerced; any invalid declared duration, including an optional setup or
  pre-task wait, prevents a complete lead-time claim on the affected path
- numeric overflow produces `timing-total-overflow` and an unavailable elapsed
  total, never infinity, a crash, or a partial sum presented as complete

Analysis selects only the named analysis_input result. Presentation selects
primary. Supplied process lead time remains evidence and does not replace
modeled totals or ranges. No selected statistic implies an empirical
end-to-end mean, percentile or iteration policy.

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

## Value-stream projection

The versioned `0.1` value-stream projection is a backend-neutral derived model
over canonical nodes, edges, typed items, and static timing. It separates
information and material item flows, connects consumers only to reachable
producers, represents external inputs and outputs explicitly, and emits stable
diagnostics when either flow surface is absent. It does not mutate canonical IR
or infer item movement from control flow alone.

## SPPM publication consumption

The SPPM renderer consumes this typed result for its derived timing footer. It
shows declared cycle, waiting, and changeover totals separately. A single
complete path produces one lead time; complete alternatives produce a range;
and unresolved elapsed-time semantics produce an unavailable value with a
pointer to `flo inspect` diagnostics. The renderer does not derive timing for a
partial projection from whole-process totals and does not create a timing
footer when the model declares no timing.

## Inspect command

`flo inspect <path>` runs the selected analysis after the ordinary parse,
compile, and validation pipeline. Its default `--format text` report is a
concise user-facing summary. `--format json` emits the analysis result as
deterministic, sorted, indented JSON with a trailing newline. The same input and
analysis options must produce byte-identical JSON.

The command surface accepts `--analysis timing` and `--analysis structure`.
Input may come from a path or stdin, and `-o/--output` may write either report
format to a file. Analysis diagnostics remain in the report payload and do not
contaminate machine-readable stdout.
