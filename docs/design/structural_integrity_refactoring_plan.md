# Structural integrity refactoring plan

Status: all three implementation batches complete, 2026-10-30. Test-file
naming cleanup is complete. Stricter region/boundary policy remains deferred.

## Objective and scope

Close the confirmed identity and reference gaps in the
[structural inventory](structural_integrity_inventory.md), then consolidate the
graph facts used by validation and inspection. Preserve canonical evidence,
existing diagnostics and deterministic output. Cycles with exits, multiple ends
and distinct transitions sharing endpoints remain valid where already allowed.

This work covers static model integrity. Execution, token simulation, scheduling,
termination proofs and path-sensitive inventory accounting are outside scope.
The [core language](../specs/core_language.md) owns normative behavior; this
plan proposes changes rather than silently tightening existing rules.

## Batch 1: Transition and lane identity — implemented

Inventory findings G01–G03. Implemented as one coherent validation change:

- Reject repeated identical transition records, without silently deduplicating.
  Compare all canonical fields, including evidence and supplied ID. Transitions
  differing in explicit identity or annotations are not exact duplicates; any
  broader duplicate-content warning needs a separate rule. This catches the
  reproduced repeated split-to-join edge without banning distinct outcomes
  that share a target.
- Reject duplicate supplied transition IDs within a process. Keep IDs optional;
  do not introduce a shared namespace with nodes or generate replacement IDs.
- Enforce lane-ID uniqueness in domain validation as well as authored source.
  Preserve the existing source rejection and align its diagnostic category/path.
- Specify identity/duplicate rules and allocate stable FLO diagnostics. Keep
  source locations when available and canonical edge/lane paths otherwise.

Verification: source and canonical invalid cases stop validated inspect/export/
render consumers; positive cases retain distinct outcomes to one destination,
optional IDs and relation evidence. Check composed includes too. Compare the
same duplicated parallel structure against a genuinely distinct two-branch
split/join. No assumption about execution is needed for these rules.

## Batch 2: Absent versus empty lane declarations — implemented

Inventory finding G04. Implemented policy: omitted lanes retain existing free-form
labels; an explicitly declared empty collection resolves no lane references.
This follows the current item/resource/location declaration policy.

Trace source composition, IR construction, internal serialization and canonical
exchange before choosing representation. Retain declaration presence explicitly
rather than changing every existing empty default into a new error. A partial
include that omits lanes must not erase another declaration; composed lane lists
keep existing additive behavior. Document the policy before enforcing it.

Verification: omitted lanes, empty lanes, valid nonempty lanes, missing IDs,
include composition and source/internal/canonical round trips. Rendering and
inspection must not invent declarations to make a bad reference pass.

## Batch 3: Shared graph facts and cycle inspection — implemented

Inventory finding G07 and the degree/adjacency mismatch behind G01:

- Introduce a small internal graph projection from validated canonical IR.
  Retain every transition by a unique projection key and preserve mappings to
  source edges. Distinguish transition-record degree from distinct-neighbor
  degree; callers must choose deliberately. Do not change decision cardinality
  to distinct successors, since distinct outcomes may share a target.
- Consolidate repeated topology construction where this simplifies current
  validators/analyses. Keep existing diagnostic ordering and sorted public
  results. Avoid a second mutable process model or a broad renderer rewrite.
- Report actual cyclic regions, self-loops and their entry/exit edges through
  structural inspection. Reconcile existing source-order backward-edge warnings
  so they are not presented as proof of a cycle or rework. Keep intentional
  cycles valid and existing unsupported-timing warnings accurate.
- Evaluate NetworkX for SCC/condensation and potential future dominance checks.
  Compare its projection code/dependency cost with the existing SCC traversal
  on the regression corpus and representative larger graphs. Adopt one topology
  implementation if worthwhile; retain FLO-owned evidence mapping and diagnostics.
  Identity checks in batches 1–2 do not depend on this choice.

Verification: no-edge, DAG, self-loop, nested/adjacent cyclic regions, external
entry/exit edges and intentional rework; stable output under equivalent ordering.
Compare results with existing SCC tests. Preserve canonical quantities and edge
relations when creating an inspection projection. Routine checks should use
traversal/SCC algorithms rather than enumerating all paths/cycles.

NetworkX details and primary documentation links are recorded in the inventory.
If adopted, add and lock the dependency, verify packaging/import boundaries and
remove replaced traversal duplication. Resolve endpoints before creating graph
edges, since NetworkX otherwise creates nodes implicitly.

## Deferred structural policy

G05/G06/G08 require representative examples and an explicit language decision:
parallel region pairing/bypass, subprocess entry/exit boundaries and ordinary
fan-in. Do not reject these structures as a side effect of adopting a graph
library. Dominance-based inspection can be considered after the policy is clear.
G09 unused declarations is optional lint, below the confirmed defects in priority.

No strict distinct-destination parallel rule, mandatory join nesting or automatic
rework inference is introduced by this plan.

## Test naming cleanup

Completed in this planning change: 20 files renamed by subject rather than
implementation milestone, generic placeholder/extra labels or coverage target.
All test functions and behavioral assertions are retained; the one cross-test
import and documentation references follow the new module names.

Examples:

| Previous filename | Current filename |
| --- | --- |
| `test_phase3_applicability.py` | `test_field_applicability.py` |
| `test_phase3_field_inventory.py` | `test_supported_field_inventory.py` |
| `test_phase6_acceptance.py` | `test_schema_runtime_parity.py` |
| `test_phase45_closeout.py` | `test_canonical_contract_boundaries.py` |
| `test_phase3_evidence.py` | `test_measurement_evidence_preservation.py` |
| `test_phase3_relations.py` | `test_relation_evidence_validation.py` |
| `test_contract_closeout.py` | `test_contract_schema_diagnostics.py` |
| `test_layout_core_elk_support_low_coverage.py` | `test_layout_core_graph_projection.py` |
| `test_materials_export.py` | `test_items_export.py` |

Keep future test modules named for a feature, invariant or boundary. Existing
package-specific names such as `pm4py` and ELK describe actual dependencies and
remain appropriate. Avoid splitting or merging test coverage during a filename
cleanup; evaluate weak smoke-test assertions separately.

## Verification and completion gates

For the naming cleanup, compare collected test IDs before/after after mapping
only module paths, then run the full suite. Test count and assertions must be
unchanged. Documentation governance, Ruff/format and whitespace checks must pass.

For runtime batches, use focused regression/consumer tests while working. Run
the full suite after batches 1–2 and at completion; run schemas, architecture,
runtime type checks and all example/golden checks when graph behavior changes.
Record intentional diagnostic additions separately from layout changes. Update
specifications, supported-field documentation if representation changes, and
this plan with concrete acceptance evidence. No aliases, skipped tests or silent
repairs should conceal malformed input.

Naming-cleanup verification (2026-10-29): all 2429 collected cases match after
module-path mapping; AST comparison confirms all function/class bodies in the
20 moved files are unchanged. Full suite: **2429 passed, no failures or skips**,
seven existing Click deprecation warnings. Ruff/format, strict documentation
governance and whitespace checks pass. That naming cleanup introduced no runtime changes; the later batch 1
implementation is recorded below.

## Batch 1 implementation evidence

Shared lane identity checking covers source composition, direct compilation and
canonical domain validation. The transition validator compares full canonical
records within endpoint groups without hashing/coercing evidence; Boolean and
numeric annotations remain different. Duplicate supplied IDs take precedence
over duplicate content. Canonical constructors and serialization preserve bad
data until explicit validation rejects it.

Diagnostics E1033/E1034/E1035 point to the second declaration. Explicit/named
transition paths and include provenance are preserved; canonical-only fields
retain canonical paths without a fabricated line. The core language, book
contract, CLI error contract and field ownership inventory document these rules.

Regression coverage: `tests/unit/ir/test_graph_identity.py` and
`tests/integration/test_graph_identity_validation.py` cover the reproduced false
parallel structure, real parallel paths, same-target distinct outcomes,
optional/separate IDs, all edge evidence fields, mapping-order independence,
source/internal/canonical preservation, direct compilation, root/include and
cross-include locations, and API/CLI validate/inspect/export/render rejection
before any consumer or output file. Existing assertions remain unchanged.

Batch 1 verification (2026-10-29): **2455 passed, no failures or skips**,
seven existing Click deprecation warnings. The 309-case identity/applicability
focused check passes. Ruff/format, runtime type checking, all 11 import
contracts, architecture/file-length policy, generated-schema drift, strict
documentation governance and whitespace checks pass. All 27 valid roots
rendered to 30 SVGs and six item summaries; 24 invalid roots rejected and three
include fragments composed. All 13 golden cases/26 files match, with zero final
geometry violations and passing accessibility checks. No golden changes or
NetworkX dependency were introduced by batch 1. All changes remain uncommitted.

## Batch 2 implementation evidence

`IR.lanes` defaults to None, preserving an unspecified declaration. Source
compilation retains explicit []; canonical projection emits [] rather than
dropping it. Internal dict/JSON serialization retains both values. Existing
optional null source/canonical lanes mean unspecified; composition treats null
like omission instead of erasing or conflicting with another declaration.
Nonempty lists retain additive composition and duplicate-ID checks.

Lane reference validation now checks declaration presence rather than
truthiness, so an empty declaration rejects references with existing E1316.
Default direct IR and omitted source declarations continue to permit free-form
labels. Inspection handles unspecified lists without inventing declarations.
Core/book contracts and field ownership documentation record the policy. No
new shape fields, schema changes, aliases or graph-library dependency are needed.

`tests/integration/test_lane_declaration_presence.py` verifies omitted/null/empty/
nonempty states; resolved/unresolved/absent node references; internal JSON and
canonical schema/export round trips; all 16 include-state combinations; included
reference locations; direct IR defaults; nonmutating rendering/inspection; and
API/CLI validate, inspect, export and render rejection before consumers/output.

Batch 2 verification (2026-10-29): **2492 passed, no failures or skips**,
seven existing Click deprecation warnings. The focused source/composition/
serialization/inspection checks pass (90 cases); the corrected field inventory,
instructional documentation and new presence checks pass (86 cases). Ruff/format,
runtime type checking, all 11 import contracts, architecture/file-length policy,
generated-schema drift, strict documentation governance and whitespace checks
pass. All 27 valid roots rendered to 30 SVGs and six item summaries; 24 invalid
roots rejected and three include fragments composed. All 13 golden cases/26
files match, with zero final geometry violations and passing accessibility
checks. No existing test assertions or golden artifacts changed for batch 2.
All workspace changes remain uncommitted.

## Batch 3 implementation and acceptance — 2026-10-30

NetworkX 3.7 is adopted using the dependency and lock update supplied by the
user. `process/graph.py` is an IR-independent leaf with a small endpoint protocol
and a frozen MultiDiGraph. Canonical edges remain authoritative; unique ordinal
keys map each graph transition to its original record without relying on optional
authored IDs. Read-only neighbor/count mappings distinguish distinct successors
from transition-record cardinality. Missing endpoints are checked before graph
construction, so projection cannot invent nodes.

Validation builds graph facts once for degree, parallel reachability and global
start/end checks. Timing, structural analysis and SCC condensation use the same
topology implementation. The old recursive Tarjan/cycle routines and separate
validation adjacency/traversal module are removed; no architecture exception is
added. NetworkX supplies iterative SCCs and multi-source BFS.

`cycle_regions` is exposed in structural and model inspection JSON and text. It
contains maximal cyclic SCC members, self-loop node IDs and full canonical
internal/entry/exit edge snapshots, with multiplicity and evidence retained.
Output does not expose input ordinals and is stable under reordered declarations.
The informational `structure-cycle-region` finding replaces the source-order
back-edge warning; no cycle implies rework. Existing explicit rework assertions
remain, with three warning expectations migrated to the new topology finding.
Tests also prove that a DAG declared against flow order receives no cycle finding.
Existing unsupported path/timing warnings and validation failures remain active.

SCC condensation additionally avoids generated-ID collisions, preserves external
transition multiplicity and retains singleton self-loops when another component
is collapsed. Core model context and relation evidence are not rewritten.

### NetworkX evaluation

The old SCC result and the shared NetworkX projection agree on all 27 valid
example roots. Exhaustive independent Floyd–Warshall tests cover all 512 directed
three-node graphs, including self-loops, and compare SCCs, cycle classification
and reachability. Deep-graph tests cover 5000-node chains and cycles.

Illustrative local projection/SCC measurements during implementation:

| Case | Previous recursive code | Shared NetworkX facts |
| --- | --- | --- |
| Median across example roots, five runs per root | 0.006 ms | 0.030 ms |
| 5000-node cycle | RecursionError | 24.5 ms |
| 20000-node cycle | RecursionError | 256.6 ms |

These are local smoke measurements, not performance guarantees. NetworkX is
adopted for maintained, nonrecursive algorithms and one topology implementation,
not a claim of faster small-graph processing. It adds about a 2.1 MB wheel and
no additional mandatory dependencies; optional scientific/plotting extras are
not requested. FLO still owns canonical evidence, deterministic projection and
diagnostics. Initial package fetches failed DNS; the user then supplied the
working dependency, which was used for all final checks.

### Completion evidence

Full suite: **2509 passed, no failures or skips**, seven existing Click
deprecation warnings. Focused coverage includes `test_graph_facts.py`,
`test_cycle_regions.py` and `test_cycle_inspection.py`, alongside existing
structural/timing, SCC, identity, lane-presence and semantic-delivery tests.

Ruff/format, runtime type checking, all 11 import contracts, architecture and
file-length policy, generated-schema drift, strict documentation governance and
whitespace checks pass. All 27 valid roots rendered to 30 SVGs and six item
summaries; 24 invalid roots were rejected and three include fragments composed.
All 13 golden cases/26 files match, with zero final geometry violations and
passing SVG accessibility. The final documentation/inventory/cycle check passes
66 cases.

The offline wheel builds successfully. Extracted-wheel smoke testing imports
all 168 packaged modules and validates, inspects and exports a self-loop model
using NetworkX 3.7. Wheel code is isolated from the source checkout; dependency
packages are supplied by the existing virtual environment, not a fresh install.
No golden files changed. All three implementation batches are complete; stricter
join/subprocess/merge policies remain explicitly deferred. Changes are uncommitted.
