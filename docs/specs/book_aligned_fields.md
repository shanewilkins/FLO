# Book-aligned supported fields

Status: Phase 3 inventory, 2026-10-28. This table is checked against the boundary
models by `test_phase3_field_inventory.py`. Adding an authored field requires
reviewing its meaning, applicability, validation, representation and consumer.
Opaque extensions are preserved and exported; they never implicitly supply
core measurements, item/resource relations or value classification.

Collections occur **only under process** in source, include fragments and
canonical exchange. Includes merge lists and recursive groups additively;
duplicate IDs are rejected. Top-level and metadata collection declarations are
rejected. `equipment` remains a resource kind, not a collection spelling.

| Contract | Fields | Applicability | Meaning | Validation owner | Canonical representation | Consumer |
| --- | --- | --- | --- | --- | --- | --- |
| `SourceDocument` | `transitions`, `lanes`, `include`, `includes`, `spec_version`, `process`, `steps` | Document | Process identity, steps, flow and portable includes. | source/models.py; source/composition.py | Flattened IR plus composition sidecar. | source/compile.py; inspection composition/readiness |
| `SourceFragment` | `transitions`, `lanes`, `include`, `includes`, `spec_version`, `process`, `steps` | Include fragment | Supplied document fields only; process owns collections. | source/models.py; source/composition.py | Merged into the authored document before compilation. | source/composition.py |
| `SourceProcess` | `version`, `lead_time`, `render`, `extensions`, `owner`, `business_units`, `items`, `resources`, `locations`, `id`, `name` | Process | Identity, observed/target lead time, collections, publication settings and annotations. | source/models.py; ir/validate.py; validate_render_intent.py | IR process identity/context, lead_time, items/resources/locations, render_intent and extensions. | inspection; export; publication; movement and value-stream analyses |
| `FragmentProcess` | `version`, `lead_time`, `render`, `extensions`, `owner`, `business_units`, `items`, `resources`, `locations`, `id`, `name` | Partial process | Only supplied process fields participate in include composition. | source/models.py; source/composition.py | Same process fields after additive collection composition. | source/composition.py |
| `SourceStep` | `name`, `description`, `lane`, `location`, `consumes`, `produces`, `performed_by`, `uses`, `value_class`, `cycle_time`, `wait_time`, `changeover_time`, `extensions`, `subprocess_parent`, `branch`, `outcomes`, `routes`, `id`, `kind`, `attrs`, `subnodes`, `steps` | Node kind matrix below | Identity, work/wait evidence, resource/item references, flow selection and subprocess containment. | source/models.py; process/field_applicability.py; ir/validate*.py | Node first-class fields; branch control context; flattened nested children and generated edges. | timing/structure/movement/value-stream analyses; inspection; export; diagram layout/content |
| `ControlAttributes` | `subprocess_parent`, `branch`, `outcomes`, `routes` | Temporary control overlay | Control fields only; no operational overlays. Removed in phase 4. | source/models.py; source/_adapter_normalization.py | Node subprocess_parent and branch/outcomes/routes control context. | source/_ir_assembly.py; structure analysis |
| `NamedIdentity` | `id`, `name`, `extensions` | Process owner | Stable owner identity, name and opaque annotations. | source/models.py | IR.process_owner. | model inspection and exchange export |
| `BusinessUnit` | `id`, `name`, `extensions` | Process business units | Named organizational context; no lane-type field. | source/models.py | IR.business_units. | model inspection and exchange export |
| `SourceLane` | `id`, `name`, `extensions`, `type` | Lanes | Stable responsibility grouping and optional role/team/system classification. | source/models.py; ir/validate_relations.py | IR.lanes; Node.lane references. | swimlane layout; structural handoff candidates; exchange and inspection |
| `BranchConfig` | `mode`, `policy`, `eligible_resources` | Branch nodes | Selection mechanism, descriptive policy and eligible resource identities; no stochastic simulation. | source/models.py; ir/validate_structure.py; ir/validate_relations.py | Node.attrs.branch. | structural branch inspection; graph/path analysis and diagram layout |
| `SourceTransition` | `id`, `label`, `route`, `outcome`, `handoff`, `rework`, `extensions`, `source`, `target` | Explicit transition | Identity, endpoints, outcome/route, display label, structured relations and opaque annotations. | source/models.py; process/contracts.py; ir/validate.py | Edge first-class fields. | graph/structural analysis; exchange; relation evidence presentation |
| `OutcomeBranch` | `id`, `label`, `route`, `outcome`, `handoff`, `rework`, `extensions`, `target` | Named outcome or route | Annotated target or string shorthand; source endpoint and branch name supplied by owner. | source/models.py; source/_adapter_normalization.py | Edge, with owning step as source and name as outcome or route. | source/_ir_assembly.py; graph/structure and rendering |
| `MeasurementProfile` | `basis`, `results`, `primary`, `analysis_input`, `observation_count`, `observation_unit`, `cohort`, `aggregation_level`, `observation_window`, `evidence_ref`, `extensions` | Work durations; wait profiles; process lead time | Basis, named statistics, presentation/analysis selectors and provenance; omitted analysis does not inherit primary. | process/contracts.py; ir/validate.py; validate_waits.py | Node measurement or IR.lead_time profile, preserved verbatim. | timing analysis selects analysis_input; presentation selects primary; export retains full evidence |
| `MeasurementResult` | `method`, `value`, `unit`, `parameters` | Named measurement result | Method, supplied value and unit; percentile parameters or explicitly namespaced methods. Unselected non-scalar evidence is retained. | process/contracts.py; process/durations.py; ir/validate.py | Profile.results entry. | selected duration consumers; exchange evidence preservation |
| `MeasurementReference` | `ref` | Queue/wait waiting only | Direct work-step wait_time reference; no chaining or duplicate analytical contribution. | process/contracts.py; ir/validate_waits.py | Node.wait_time reference object. | timing/path analysis; render/sppm/waiting.py |
| `HandoffRelation` | `type`, `extensions` | Transitions | Explicit transfer type, optionally unspecified; annotations do not alter inference. | process/contracts.py; ir/validate.py | Edge.handoff. | structural inspection; exchange; diagram evidence |
| `ReworkRelation` | `reason`, `frequency`, `note`, `extensions` | Transitions | Explicit repetition/correction with reason, population evidence, note and opaque annotations. | process/contracts.py; ir/validate.py | Edge.rework. | structural analysis; exchange; rework routing and diagram evidence |
| `ReworkFrequency` | `basis`, `numerator`, `denominator`, `observation_unit`, `evidence_ref` | Structured rework | Finite nonnegative affected count and positive integral population; numerator <= denominator. Zero is observed evidence, not omission. | process/contracts.py; ir/validate.py | Edge.rework.frequency; retained basis/unit/evidence_ref. | rate/count/frequency inspection and diagram evidence |
| `ItemContract` | `id`, `name`, `quantity`, `extensions`, `kind` | process.items | Named material or information identity, quantity and opaque annotations. | process/contracts.py; source/models.py; ir/validate.py; validate_relations.py | IR.items; exchange process.items. | item relations; movement; value-stream flows; ingredients/exchange export |
| `ResourceContract` | `id`, `name`, `quantity`, `extensions`, `kind` | process.resources | Named person or equipment identity, quantity and opaque annotations. | process/contracts.py; source/models.py; ir/validate.py; validate_relations.py | IR.resources; exchange process.resources. | performer/equipment and eligibility references; movement; named task presentation; export |
| `LocationContract` | `id`, `name`, `quantity`, `extensions`, `kind`, `metadata`, `x`, `y`, `unit` | process.locations | Named operational place, optional type, amount and physical coordinates; spatial spelling cleanup remains phase 4. | process/contracts.py; source/models.py; ir/validate.py; validate_relations.py | IR.locations; exchange process.locations. | location references; dimensional movement; spaghetti location display; exchange |
| `CountQuantity` | `kind`, `value`, `unit`, `qualifier` | Declared entity quantity | Positive integral count of indivisible entities, each unit, optional descriptive qualifier. | process/contracts.py; ir/validate.py | Entity.quantity. | ingredients text and exchange; quantity validation |
| `MeasureQuantity` | `kind`, `value`, `unit`, `canonical_value`, `canonical_unit` | Declared entity quantity | Positive finite amount/unit and optional equivalent canonical amount/unit. | process/contracts.py; ir/validate.py; process/units.py | Entity.quantity. | Pint equivalence/dimensional checks; authored-unit export |
| `SpatialContract` | `x`, `y`, `unit` | Location spatial evidence | Finite two-dimensional coordinates and optional spatial unit. | process/contracts.py; ir/validate.py; process/units.py | Location coordinates/spatial object. | movement distance and spaghetti projection |
| `LocationMetadata` | `spatial` | Location spatial container | Spatial evidence only, not a general semantic metadata escape hatch. | process/contracts.py; ir/validate.py | Location.metadata.spatial (pending phase 4 spelling choice). | movement spatial extraction |

`EntityGroup` adds an optional nonblank `name` and nonblank group keys whose
values are nested groups or lists. Group names preserve organization, while
identity/reference consumers traverse entity entries independent of group depth.

## Node applicability matrix

All kinds support `id`, `kind`, `name`, `description`, `lane`,
`subprocess_parent` and `extensions`. `lane` describes responsibility, while
`location` describes physical place. Optional operational fields cannot be
smuggled through attrs, even when an empty list is supplied.

| Kinds | Additional semantic fields |
| --- | --- |
| task, system_task, subprocess | location, consumes, produces, performed_by, uses, value_class, cycle_time, wait_time, changeover_time |
| queue, wait | location, wait_time (profile or direct reference) |
| decision | outcomes |
| branch | branch, routes |
| start, end, parallel_split, parallel_join | None |

Only subprocess supports nested `steps`/`subnodes`; the single-spelling decision
remains phase 4 work. A temporary `attrs` overlay accepts only subprocess_parent,
branch, outcomes and routes and observes this same matrix. Its complete removal
is phase 4. Named target `to` and include/includes compatibility likewise remain
explicit phase 4 obligations, not additional semantic fields.

## Presentation and analytical limits

Process supplied lead time retains its basis and primary result. Modeled lead
time uses analytical selectors on steps, remains separate, and may be unavailable
or a range. Inspection includes both and retains complete supplied profiles.
Canonical exchange preserves supplied evidence and does not invent a modeled
profile; derived results belong to inspection. Every diagram exposes distinct
supplied and modeled labels when supplied lead time exists and publication text
is enabled. Hiding headers/footers is an explicit display choice.

Relation inspection retains the complete handoff/rework objects, including
frequency population, basis, evidence, notes and extensions. Diagrams show human
relation summaries; extensions remain annotations in canonical exchange and
inspection rather than arbitrary text on a diagram. Performer/item/location
labels resolve declared names while reference IDs and analytical identities stay
unchanged. Quantities, spatial coordinates and evidence units are not inferred.
