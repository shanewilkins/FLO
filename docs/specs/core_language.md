# FLO Core Language

FLO describes process facts and compiles them into one canonical graph for
validation, analysis, export and rendering. The [book-aligned contract](book_aligned_contract.md)
and [field inventory](book_aligned_fields.md) define the supported fields.
Generated authored and exchange schemas are `schema/flo_source.json` and
`schema/flo_ir.json`.

## Intent

Ordered work, waiting, ownership and control flow are authored facts. Derived
metrics and renderer geometry are projections of those facts. FLO does not
infer missing evidence or execute a process simulation.

## Source document conventions

A complete YAML mapping declares `spec_version: "0.1"`, a process with nonblank
`id` and `name`, and a nonempty `steps` list. Optional top-level fields are
`transitions`, `lanes`, `include` and `includes`. Unknown fields are rejected.
Opaque annotations belong under `extensions` and contain finite JSON data.

## Authoring model

Each step has a unique `id` and a supported `kind`. Without explicit
`transitions`, adjacent non-end steps receive sequential connections. A step
with local `outcomes` or `routes` receives those connections instead of an
additional sequential connection. Explicit `transitions`, including an empty
list, replace implicit synthesis completely.

A decision declares named `outcomes`. A generic branch declares `branch.mode`
and may declare named `routes`. A named target is either a step-ID string or an
object with `target` and optional transition evidence. YAML Boolean outcome
names map to yes/no. Explicit transitions use `source` and `target`.

### Top-level conventions

`include` names one file; `includes` is a nonempty list of file paths. Fragments
may omit process identity and version, but every supplied field is validated
before composition. Paths resolve relative to the including file and must stay
inside the entry file's directory, including symlink resolution. Cycles,
duplicate identities and unsupported or conflicting versions fail. Includes
are bounded by file count, nesting depth and expanded byte size.

Steps, transitions and lanes merge additively. Process collections merge as
list/list or grouped-object/grouped-object; mixed forms fail. Local process
context overrides included context. Extensions merge as opaque annotations.
Source locations and include chains survive composition and validation.

## Canonical authored primitives

Collections occur only under `process`, including in fragments and canonical
exchange. `items` have kind material/information; `resources` have kind
person/equipment; `locations` name operational places. Collections may be flat
lists or recursively grouped objects with an optional display `name`. Entity
IDs are unique across all groups of a collection.

Work refers to entities through `consumes`, `produces`, `performed_by`, `uses`
and `location`. Lanes describe responsibility grouping. See the field inventory
for each field's owner and consumer.

## Core entities

The compiled IR consists of process context, flattened nodes and directed
edges. Process context includes optional version, owner, business units,
collections, supplied lead-time evidence, render intent and extensions. All
operational node and edge fields are first-class. Internal constructors require
Node/Edge instances; internal dictionary restoration uses their declared fields
and rejects unknown arguments rather than discarding them.

## Node types

| Kind | Meaning |
| --- | --- |
| start / end | Entry / termination boundary |
| task / system_task | Human or system work |
| subprocess | Work with optional nested `steps` |
| queue / wait | Waiting evidence or a direct waiting reference |
| decision | Evaluated condition with distinct outcomes |
| branch | Route selection with dispatch, probabilistic, external or unspecified mode |
| parallel_split / parallel_join | Concurrent activation / synchronization |

Only subprocesses may contain nested `steps`. Flattened children retain
`subprocess_parent`; parents must exist, be subprocesses and form an acyclic
hierarchy. Work kinds support operational relations, value classification,
cycle, waiting and changeover evidence. Queue/wait kinds support location and
waiting evidence. Control nodes do not carry operational fields. The
[applicability matrix](book_aligned_fields.md#node-applicability) is exhaustive.

## Canonical relation semantics

`handoff` and `rework` are structured transition objects. Handoff may state its
transfer type. Rework may state reason, frequency, note and extensions.
Frequency supplies basis, nonnegative numerator, positive integer denominator
and observation unit; numerator cannot exceed denominator. Optional evidence
references are nonblank. Full relation evidence survives exchange and inspection.
Explicit rework changes structural analysis and routing; it does not imply an
iteration count for modeled elapsed time.

## Timing semantics

`cycle_time` means active work; `wait_time` means waiting; `changeover_time`
means setup. Process `lead_time` is supplied observed, simulated, estimated,
planned or target evidence. `modeled_lead_time` is derived, never an authored
node timing field.

A measurement profile has basis, nonempty named results and a `primary` result
selector. Optional `analysis_input` names the analytical result. Observation
count and unit occur together; cohort, aggregation level, window, evidence
reference and extensions preserve supporting context. Methods use supported
core names or explicit namespaced extension names.

Renderers select primary; analyses select analysis_input. An absent analytical
selector does not inherit primary. Omitted evidence, explicit unknown
classification and measured zero retain distinct meanings. Supplied process
lead time never fills a missing modeled total.

Queue/wait evidence may use `{ref: work_step.wait_time}`. The target must be an
existing work step with a waiting profile. References do not chain or copy
measurements. Analysis avoids counting projected waiting twice and checks
coverage separately on every path. Presentation resolves references on copies.

## Scalar timing values

Each selected result must have a finite nonnegative numeric value and an explicit
supported unit: s, m, min, hr or d. Duration m means minutes. Conversion to
seconds must remain finite. Numeric text, Boolean and nonscalar selected values
fail; unselected supported statistics retain their supplied form. Presentation-only
profiles still require a valid primary duration.

## Normative semantic rules

- Supplied transition IDs are unique within the process and optional. Their
  namespace is separate from node IDs. Repeated identical canonical transition
  records are rejected, comparing every field including ID and evidence;
  mapping order does not matter and Boolean/numeric evidence stays distinct.
  Different IDs, outcomes, routes, labels or annotations may distinguish
  transitions sharing endpoints. FLO never silently deduplicates transitions.
- Lane IDs are unique in authored source, composed includes and canonical IR.
  Omitted or optional null lanes leave the collection unspecified and permit
  free-form node lane labels. An explicit `lanes: []` declares no valid lane IDs,
  so any node lane reference fails E1316. Nonempty declarations require every
  lane reference to resolve. Includes merge lane lists additively; omission,
  null or an empty list cannot erase existing declarations. Internal serialization
  retains unspecified as null and declared-empty as []; exchange omits
  unspecified lanes and preserves declared-empty lanes.
- Exactly one start and at least one end are required. Edges cannot enter start
  or leave end. Every endpoint resolves to a declared node.
- Every non-start node has a predecessor; every non-end has a successor. Every
  node is reachable from start and can reach an end.
- A decision has at least two outgoing edges with distinct nonblank outcomes.
  Only decisions use outcomes; only generic branches use route names.
- A generic branch has at least two outgoing edges, a valid mode and distinct
  supplied route names. Optional eligible resources resolve when declared.
- Fan-out belongs to decision, branch or parallel_split. Parallel split/join
  degree and paired reachability rules apply. Cycles remain valid graphs, but
  elapsed-time analysis refuses an unsupported iteration policy.
- Value classification belongs only to work kinds and is VA, RNVA, NVA or
  explicit unknown. Omission stays unclassified; FLO does not infer correctness
  of the author's classification.
- When collections are declared, references resolve even if the collection is
  empty. performed_by requires person resources; uses requires equipment.
  Lane/location references resolve against their declarations.
- Quantities are either positive integral counts (optional each unit and
  qualifier), or finite positive measured amounts. Optional canonical amount
  and unit occur together, share a dimension and describe the same amount at
  relative tolerance 1e-9, absolute tolerance 0. Conversion must remain positive
  and finite. Supported measure units are mg, g, kg, ml, l, mm, cm and m.
- Location `spatial` holds finite x/y coordinates and optional unit mm, cm, m,
  in or ft. Mixed supported units normalize to one physical frame for distances.

## Serialization relationship

Authored source uses steps/transitions; canonical exchange uses nodes/edges.
Every first-class field and supplied evidence profile survives internal
serialization. Generated exchange validation and schema drift checks protect
that boundary. Projections never manufacture edges from annotations or promote
operational values from metadata.

## Scope boundaries

Graph semantics, cross-references, provenance, unit conversions and derived
analysis remain domain-owned. Pydantic owns local shape and scalar contracts.
Renderer options remain separate from process semantics. Display annotations
use explicit extensions: `flo:publication` for footer_metrics/footer_notes and
publication_date; `flo:continuation` for outgoing/incoming edge tokens;
`flo:spaghetti` for a boundary overlay. Owner/version come from process fields.
Subprocess extensions may provide `detail_map_ref` as display text.

## Relationship to other documents

See [static analysis](static_analysis.md), [CLI diagnostics](cli_error_contract.md),
[the manual](../User_Manual.md) and [the refactoring plan](../design/book_aligned_contract_refactoring_plan.md).
