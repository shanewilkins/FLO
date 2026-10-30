# Book-aligned contract

Status: accepted and implemented; final acceptance verified 2026-10-29.

This specification records the breaking contract accepted by the
[book-alignment ADR](../design/adr/book_aligned_language_conventions.md).
It supersedes the timing, value-classification, handoff/rework, semantic
metadata, and compatibility terminology in `core_language.md` and
`static_analysis.md`. The [refactoring plan](../design/book_aligned_contract_refactoring_plan.md) and
[failure ledger](../design/book_aligned_refactor_failure_ledger.md) record
implementation dispositions and executable acceptance evidence.

## Terminology and instructional evidence

The repository extraction `notes/notes-from-book.md` and the Chapter 8 activity
summary were checked on 2026-10-27. The current book's Wash n' Fold case is
simulated Friday 91: 39 orders, 65 Wash loads, 65 Dry loads, and five correction
records. Staging and readiness notification are separate activities.

| Book concept | Canonical FLO term | Meaning or deliberate distinction |
| --- | --- | --- |
| Active processing, P/T | `cycle_time` | Active work duration; not inter-departure cadence or total elapsed time. |
| Waiting, W/T | `wait_time` | Time before work or in an explicit waiting state. |
| Setup, S/T | `changeover_time` | Active setup/changeover, separate from waiting and processing. |
| Observed end-to-end lead time | process `lead_time` | Supplied profile with its own population, window, and basis. |
| Static modeled elapsed time | `modeled_lead_time` | Derived analytical result, never an authored work field. |
| Value-added, necessary non-value-added, non-value-added | `VA`, `RNVA`, `NVA` | Work classification. `unknown` is an explicit classification; omission is unclassified. |
| Comparable activity records, n | `observation_count`, `observation_unit` | Loads and orders are different populations; never substitute one count for another. |
| Statistical result | named `results` | Retain method, value, and unit; statistics are supplied, not computed by FLO. |
| Evidence and observation period | `evidence_ref`, `observation_window`, `cohort`, `aggregation_level` | Preserve provenance without fetching external event data. |
| Visible queue | `queue`, `wait_time.ref` | A structural waiting state; a direct reference projects another step's wait without adding a copy to totals. |
| Transfer of responsibility, information, material, or custody | `handoff` | Structured transition relation, with optional type. |
| Correction/repetition | `rework` | Structured transition relation, with reason and optional frequency population. |
| Flow objects | `items`, `consumes`, `produces` | Material or information objects and their work relations. |
| Performers and supporting equipment | `resources`, `performed_by`, `uses` | Person and equipment identities, distinct from flow objects. |
| Responsibility grouping and operational place | `lane`, `location` | Display responsibility versus physical operational location. |
| Non-language annotations | `extensions` | Explicit containment; no implicit analytical meaning. |

The maintained acceptance fixture is `examples/reference/book_washnfold.flo`.
Its timing means and supporting statistics come from
`washnfold_representative_activity_summary.csv` in the book repository, checked
on the date above. `basis: simulated` reflects the case generator; these are
not observations of an actual laundry. The independent 39-order release wait
is not the 65-load Wash wait. Notification and correction queues reference
the corresponding work waits. The fixture preserves measured zero setup.

## Measurement profiles

A profile requires `basis`, a non-empty `results` mapping, and `primary`.
`basis` is `observed`, `simulated`, `estimated`, `planned`, or `target`.
`primary` and optional `analysis_input` name existing results. Renderers select
`primary`; analyses select `analysis_input`, without substituting the primary
when the analytical selector is absent.

Each named result has `method`, `value`, and `unit`. Core methods are `count`,
`sum`, `minimum`, `maximum`, `mean`, `median`, `mode`, `percentile`, and
`standard_deviation`. Other methods require a lowercase namespace and name,
for example `lss4py:trimmed_mean`. A percentile supplies
`parameters.percentile` from 0 through 100. Other method-specific parameters
belong in `parameters`. Non-scalar statistics can be retained; a selected
result that a duration consumer cannot interpret must fail or report an
explicit capability limitation, never become zero.

`observation_count` is a positive integer and is paired with nonblank
`observation_unit`. Optional `cohort`, `aggregation_level`,
`observation_window`, and `evidence_ref` retain sample context. They do not
prove two measurements share a population. `extensions` is an explicit object.

A waiting reference is exactly `{ref: step_id.wait_time}`. Only queue/wait
nodes may project a work step's waiting profile. Targets must resolve directly;
references do not chain. A reference contributes the underlying waiting evidence
at most once on an analytical path. Independent profiles remain independent.

`wait_before`, `crossover_time`, `transfer_time`, node `lead_time`,
`sla_target_seconds`, and timing under `metadata` are retired, with no runtime
translation. Process `lead_time` is a profile, not a reference. Selected duration
results require finite nonnegative numeric values and explicit supported units.

## Field inventory and ownership

Pydantic owns external shape, scalar constraints, and field applicability.
Domain validators own identities, graph meaning, reference resolution, unit
compatibility, analytical contribution, and provenance. Generated
`schema/flo_source.json` and `schema/flo_ir.json` describe authored and exchange
shapes. Internal IR stays plain dataclasses. JSON Schema captures structural
constraints; selector validity, field applicability, graph/reference rules, and
unit semantics also require FLO validation. Schema validation alone does not
establish semantic validity.

| Surface | Supported fields | Canonical representation and consumer |
| --- | --- | --- |
| Document | `spec_version`, `process`, `steps`, `transitions`, `lanes`, `include`, `includes` | Source compiler and include composition; canonical IR flattens steps into nodes/edges. |
| Process | `id`, `name`, `version`, `owner`, `business_units`, `items`, `resources`, `locations`, `render`, `lead_time`, `extensions` | Exchange process context; identity/relations, render-intent resolver, and measurement consumers. Collections occur only under `process`, including include fragments; there is no placement precedence. |
| Identity | `id`, `name`, `extensions`; lane `type` | Identity/reference validators, headers and lane layout. Lane type: role, team, system. |
| Work | `id`, `kind`, `name`, `description`, `lane`, `location`, `subprocess_parent`, `consumes`, `produces`, `performed_by`, `uses`, `value_class`, `cycle_time`, `wait_time`, `changeover_time`, `extensions` | First-class node fields; graph, timing, movement, value-stream, inspection, exchange, and rendering. |
| Queue/wait | Identity/display/hierarchy, `location`, `wait_time`, `extensions` | Waiting/reference validation, timing and queue rendering; no work measurements, value classification, or item/resource relations. |
| Control | Identity/display/hierarchy, `branch`, `outcomes`, `routes`, `extensions` where applicable | Pure flow selection/synchronization; no operational measurements, work relations, or location. |
| Branch configuration | `mode`, `policy`, `eligible_resources` | Graph branch validation, eligible-resource references, branch inspection. Modes: dispatch, probabilistic, external, unspecified. |
| Transition | `source`, `target`, `id`, `label`, `outcome`, `route`, `handoff`, `rework`, `extensions` | First-class edge fields; graph/structure analysis and rendering. |
| Named target | `target`, `id`, `label`, `handoff`, `rework`, `extensions`, or target-ID string shorthand | Owning step supplies source; the outcome/route key supplies selection. Inner outcome/route overrides are rejected. |
| Handoff | `type`, `extensions` | Structural handoff analysis. Type: responsibility, information, material, system, location, mixed. |
| Rework | `reason`, `frequency`, `note`, `extensions` | Structural rework analysis and relation presentation. |
| Rework frequency | `basis`, `numerator`, `denominator`, `observation_unit`, `evidence_ref` | Explicit affected count and population; numerator cannot exceed denominator. |
| Item | `id`, `name`, `kind`, `quantity`, `extensions` | Relation resolution, material movement, quantity exports. Kind: material or information. |
| Resource | `id`, `name`, `kind`, `quantity`, `extensions` | Performer/equipment resolution and quantity exports. Kind: person or equipment. |
| Location | `id`, `name`, optional `kind`, `quantity`, spatial coordinates, `extensions` | Location references and movement distances; spatial evidence has one first-class spatial container. |
| Quantity | `kind`, `value`, `unit`, count `qualifier`, measure `canonical_value`/`canonical_unit` | Typed count/measure boundary; Pint domain conversion and equivalence checks. |
| Spatial evidence | `x`, `y`, `unit` | Finite coordinates; spatial dimensional conversion remains domain-owned. |

The exhaustive [field inventory and applicability matrix](book_aligned_fields.md)
records each supported field, its meaning, validation owner, canonical form and
consumer. A drift test requires every boundary field to appear in that inventory;
a semantic-metadata architecture gate prevents new opaque core-field reads.
Collections belong only under `process` in complete source, include fragments and
canonical exchange. Top-level and metadata placements and legacy collection names
are rejected rather than translated. `equipment` remains a resource kind.
Nested subprocesses use only steps. Named branch targets use target. Source
attrs, top-level edges, alternate endpoint keys and location metadata/coordinate
aliases are rejected. Canonical constructors retain invalid supplied evidence
for explicit validation and do not coerce dictionary entries or promote context.


Relation frequency counts must be finite, numerator nonnegative and denominator
a positive integer, with numerator no greater than denominator. Basis and
observation unit are explicit; a supplied evidence reference must be nonblank.
Zero frequency remains distinct from omission. Relation extensions contain only
portable finite JSON data and never supply core semantics. Inspection retains
the complete relation objects, including evidence and annotations.

All diagrams distinguish supplied process lead time (including its basis) from
modeled totals when publication text is enabled. Canonical export preserves the
supplied profile; derived modeled results belong to inspection, not authored
exchange. Value-stream cards select primary results while their analytical
timeline uses analysis_input. Diagram labels resolve entity display names on
presentation copies without changing references or analytical identities.

## Canonical input integrity

Plain canonical dataclasses retain malformed supplied relation and measurement
values until explicit validation rejects them. Invalid list containers or
members must not become empty relations; invalid measurements or Boolean
handoff/rework values must not become absent evidence. Construction detaches
mutable supplied values without changing their meaning. Internal JSON
round-trips and exchange projections must preserve malformed values rather than
hide them through truthiness filtering.

Canonical relation shape failures use `E1310` (container) or `E1311` (member);
measurement shape failures use `E1301`; invalid structured edge relations use
`E1401`. Process `lead_time` must have profile shape. Selected duration
semantics are validated separately with `E1303`, as specified below.

Validated source operations reject malformed compiler output before inspection,
export or rendering runs. Omitted measurements remain absent; measured integer
and floating-point zero remain supplied values; valid empty relation lists and
structured relations retain their intended shapes. Retired context paths are rejected rather than normalized.

## Selected duration validation

For node `cycle_time`, `wait_time`, and `changeover_time`, including queue
profiles, both `primary` and any supplied `analysis_input` must select usable
durations. The same rules apply to process `lead_time`. Presentation-only
profiles still require a usable primary duration. An absent or null
`analysis_input` does not inherit `primary` or become measured zero.

Selected durations require finite, nonnegative numeric values, explicit
supported time units, and conversion to a finite number of seconds. Numeric
text and non-scalar values cannot serve as selected durations. Invalid selected
results fail with `E1303` before validated downstream consumers run. References
retain their identity; the owning work profile is subject to the same rules.

Unselected results remain supplied evidence and may contain supported
non-scalar statistics or non-time counts. Validation does not rewrite selectors,
coerce results, or use supplied process lead time as a derived modeled total.
Display continues to use `primary`, while analysis uses `analysis_input`.

## Graph identity

Supplied transition IDs are optional and unique within the process, independently
of node IDs. Identical full canonical transition records are invalid; distinct
outcomes, routes, IDs, labels or evidence may share endpoints. Comparison includes
all canonical fields and preserves Boolean/numeric distinctions in extensions;
mapping order is irrelevant. Records are rejected rather than deduplicated.
Lane IDs are unique across source/includes and canonical IR. Omitted or
optional null lanes are unspecified and allow free-form node lane labels;
`lanes: []` is a declared-empty collection and rejects all node lane references
with E1316. Nonempty declarations resolve every reference. Include lane lists
merge additively; omission/null/empty declarations do not erase existing lanes.
IR uses None for unspecified and [] for declared-empty. Internal JSON retains
null versus []; canonical exchange omits unspecified lanes and emits [] for
an explicit empty declaration. These cross-record
invariants require FLO validation in addition to the generated shape schemas.

## Boundary diagnostics

Pydantic errors are adapted to FLO diagnostics with an authored field path,
source location, and stable code. Existing specific codes remain where defined.
Generic unsupported fields use `E0220`, missing fields `E0221`, and invalid
local shapes/values `E0222`. These are FLO categories independent of Pydantic's
internal union arms, type names, and validation dumps. Unknown error categories
use the stable invalid-value fallback. Domain errors retain their domain codes.

Malformed authored entity and quantity shapes fail during compilation (stage 3),
retaining their specific `E12xx` codes. Dimensional compatibility and canonical
quantity equivalence remain domain validation errors (stage 4), including
`E1222`, `E1223`, and `E1224`.

Graph identity failures use `E1033` for an identical transition record, `E1034`
for a repeated supplied transition ID, and `E1035` for a repeated lane ID.
When both transition rules apply, duplicate ID is reported first. Source lane
identity failures remain an early structural check (stage 3); canonical lane
identity and transition duplicates fail domain validation (stage 4).
