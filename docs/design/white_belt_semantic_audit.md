# White Belt semantic pipeline audit

Status: completed semantic audit; remaining release acceptance is tracked in
[the roadmap](../ROADMAP.md). This is explanatory evidence for the semantic
portion of TR-114, not a declaration that the complete release gate has passed.
The authoritative language contract remains [core language](../specs/core_language.md).

## Pipeline and boundaries

Validated CLI consumers compile source, validate graph and relation semantics,
and check the schema projection and render intent before producing output.
Public Python `validate`, `inspect`, and `export` now run those same checks.
The Python `compile` operation intentionally remains a compilation stage without
semantic validation; callers seeking accepted process models must use `validate`.

Compilation errors retain the CLI compile exit status (3); semantic and schema
validation failures retain validation status (4). These failures return typed
source diagnostics through the API. Warning aggregation and severity-aware
success remain queued under [next-sprint diagnostic delivery](diagnostic_delivery_plan.md).

## Findings resolved

| Area | Resolution and evidence |
| --- | --- |
| API versus CLI acceptance | API validation and inspection now check the canonical schema and render intent. Schema-invalid names and invalid render intent fail every validated consumer. |
| Silent source data loss | Reject malformed process/step metadata and legacy attrs, invalid parent values, null child lists, and competing child lists before normalization. |
| Implicit control flow | Null transitions fail; only an absent transitions field requests synthesis. Existing explicit lists remain authoritative. |
| Legacy attrs | Apply the same outcome, route, branch configuration, and timing alias rules to the effective attributes used by compilation. |
| Declared entity references | Empty item/resource collections permit no references. Location and listed lane references resolve against their declarations. Grouped locations work without requiring an item/resource kind. |
| Queue and timing ownership | Queue capacity rejects booleans and null. Legacy `wait` nodes retain their existing `wait_time` support. Processing/setup and work-wait fields cannot live on control boundaries or branch/parallel nodes. |
| Typed numeric evidence | Spatial coordinates, measured and canonical quantities, and numeric rework rates/counts reject NaN, infinities, and overflowing integers with domain errors. |
| Stale positive fixture | Human review lanes now use documented `type: role`, replacing schema-invalid `kind: default`. |

`tests/integration/test_semantic_contract.py` exercises rejection before API and
CLI validation, inspection, export, and rendering; it also verifies deterministic
export of grouped context and measured zero through legacy attrs. Dedicated
cases cover timing ownership and typed numeric evidence.

`tests/unit/test_conformance_examples.py` now checks every positive conformance
fixture against the schema and through API validation, inspection, and repeated
canonical export. Every negative fixture fails both low-level validation and
all validated API operations. Existing narrow fixtures exercise identities,
decision outcomes, generic dispatch branches, parallel split/join structure,
items/resources and their kinds, handoffs, rework, queues, and unresolved edges.
Existing hierarchy and graph unit suites retain subprocess, reachability,
boundary, and cyclic-process coverage. Scalar timing state evidence remains in
`tests/integration/test_timing_correctness.py`.

## Remaining acceptance

This audit does not promote SPPM to stable or replace the renderer geometry,
visual-invariant, accessibility, installed-package, or external-consumer release
gates. Those remain tracked separately under TR-114 and the roadmap. Dedicated
generic-branch rendering remains deferred under the existing language boundary.
