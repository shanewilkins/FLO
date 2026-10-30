# Structural integrity inventory

Status: proposed follow-up; audited 2026-10-29 against the uncommitted working
tree after the book-aligned refactor. This inventory records the original rules,
verified gaps and candidate checks. It does not itself change the language
contract or claim execution soundness; implementation updates are recorded below.

## Scope and severity

The goal is a connected, internally consistent process description: identities,
references, entry/exit boundaries, flow topology and containment. Execution,
tokens, deadlock proofs, scheduling, resource contention, inventory accounting
and guaranteed termination are outside this inventory's implementation scope.

- **Existing error**: violates an enforced structural contract.
- **Proposed error**: unambiguous identity/reference corruption, or a new rule to
  adopt explicitly in the specification before enforcing it.
- **Candidate warning**: a suspicious structure that can be intentional.
- **Language decision**: the contract cannot currently establish incorrectness.

Reachability means a path exists. It does not mean every execution follows it.
Cycles with exits and multiple end nodes are permitted. No new diagnostic codes
are allocated by this design note.

## Implementation follow-up

Batch 1 implemented on 2026-10-29: G01–G03 now reject duplicate records (E1033),
transition IDs (E1034) and lane IDs (E1035), including canonical lanes. The tables
and probes below retain the original audit baseline. Current implementation and
verification are recorded in the [refactoring plan](structural_integrity_refactoring_plan.md).
Batch 2 also closes G04: unspecified lanes use None, explicit empty uses [],
and E1316 applies to empty declarations. Includes and serialization retain
presence. Batch 3 closes G07 with NetworkX graph facts and cycle-region
inspection; stricter region/boundary policy remains deferred. The audit tables retain
the original observed behavior rather than claiming these gaps are still live.

## Existing protection

| ID | Invariant and current behavior | Implementation / evidence |
| --- | --- | --- |
| S01 | Nonempty graph; node IDs unique. Errors E1001/E1002. | `ir/validate.py`; `tests/unit/test_validate_errors.py`. Source also checks IDs during composition/normalization. |
| S02 | Exactly one start, at least one end. Errors E1003/E1010. Multiple ends are valid. | `ir/validate_graph.py`; `test_validate_errors.py`. |
| S03 | Every transition endpoint resolves to a node. E1004. | `ir/validate_graph.py`; `test_validate_errors.py`. |
| S04 | No transition enters start or leaves end. E1023/E1024. | `ir/validate_graph.py`; `test_validate_errors.py`. |
| S05 | Every non-start has a predecessor; every non-end has a successor. E1006/E1007. Queue also has specific E1103/E1104 checks. | `ir/validate_graph.py`; `test_validate_errors.py`. Generic connectivity also covers wait nodes. |
| S06 | Every node reachable from start. E1008 catches isolated nodes and disconnected islands, including internally connected cycles. | `ir/validate_graph.py`; `test_validate_errors.py`; probe A below. |
| S07 | Every node can reach some end. E1009 catches reachable closed cycles even when their nodes all have successors. | `ir/validate_graph.py`; `test_validate_errors.py`; probe B. |
| S08 | Fan-out only on decision, branch or parallel_split. E1025. | `ir/validate_graph.py`; `test_validate_errors.py`. Counts transition records, not distinct successors. |
| S09 | Decision has at least two outgoing transitions, each with a nonblank, case-insensitively unique outcome. Outcome belongs only to decision; route belongs only to branch. | E1005, E1020–E1022, E1027/E1028/E1031; `ir/validate_graph.py`; `test_validate_errors.py`. |
| S10 | Branch has at least two outgoing transitions and valid config; supplied route names are unique ignoring case. | E1026/E1032 plus local contract validation; compiler/applicability and graph tests. Unnamed routes are allowed. |
| S11 | Parallel split has at least two outgoing transitions and reaches some join; join has at least two incoming transitions and some upstream split. | E1011–E1014; `ir/validate_structure.py`; `test_validate_errors_relations_parallel.py`. This does not pair regions or establish distinct branches. |
| S12 | Subprocess parent exists, has subprocess kind, is not self, and parent chains are acyclic. | E1330–E1332/E1334; `ir/validate_subprocess.py`; `test_validate_subprocess.py`. Containment is separate from flow connectivity. |
| S13 | Item/resource/location collection IDs unique, including groups; declared item/resource references resolve, with performer/equipment kind restrictions. | E1221, E1312–E1315; `ir/validate_entities.py`, `ir/validate_relations.py`; relation/quantity suites. Resolution is conditional on collection presence. |
| S14 | Lane and location references resolve against declarations. | E1316; `ir/validate_relations.py`. Locations distinguish absent from empty; lanes use a truthiness check, so an empty lane list skips resolution (gap G04). |
| S15 | Queue/wait measurement references resolve to an existing work step's declared waiting profile; chains rejected. | E1504/E1507/E1510; `ir/validate_waits.py`; `test_waiting_integrity.py`. No flow-order requirement is imposed. |
| S16 | Source lane IDs unique. | `source/composition.py`, `source/_adapter_normalization.py`; probe I. Canonical/direct-IR parity is missing (G03). |

Implementation paths above are relative to `src/flo/process/` unless a source or
test path is specified. Existing source/canonical local-shape and field-kind
checks supplement this graph inventory; they are not repeated here.

## Confirmed gaps and candidate additions

| ID | Finding | Current behavior | Proposed disposition / priority | NetworkX contribution |
| --- | --- | --- | --- | --- |
| G01 | Identical transition records inflate parallel degree. | `s -> p`, two identical `p -> j` records, `j -> e` validates with p=parallel_split/j=parallel_join. The adjacency set has one successor while degree counts two records. | **P1 proposed error:** reject exact duplicate transitions. Define parallel branch cardinality explicitly before requiring distinct destinations. Preserve legitimate different outcomes/routes to the same destination. | None needed for duplicate detection; a simple keyed comparison suffices. |
| G02 | Duplicate supplied transition IDs. | Two different linear edges can both have `id: same`; accepted by authored validation. | **P1 proposed error:** supplied edge IDs unique within the process, with source/canonical parity and a located diagnostic. No need to require IDs on all edges or make edge/node namespaces identical. | None needed; identity-set check. |
| G03 | Duplicate lane IDs at canonical/direct-IR boundary. | Source rejects duplicate lanes, but `validate_ir` and `ensure_schema_aligned` accept the equivalent duplicate canonical lanes. | **P1 proposed error:** enforce source identity invariant in domain validation too. | None needed; identity-set check. |
| G04 | Empty lane declarations skip reference checking. | `lanes: []` plus `lane: missing` validates. An undeclared collection may intentionally permit free-form lane labels; empty and absent currently collapse in source-to-IR handling. | **P1 language/parity decision:** confirm empty means declared-empty, then retain declaration presence and reject unresolved references. Do not reject existing free-form labels implicitly. | None needed; declaration-presence and reference policy. |
| G05 | Parallel regions can bypass joins or use a join unrelated to some branches. | Only existential split/join reachability is enforced; probe G validates. | **P2 candidate warning:** show branch paths escaping a candidate common join, or joins not covered by a common split. **Language decision** before mandatory structured nesting/pairing. | Dominators, post-dominators and reachability support structural evidence; they do not by themselves prove incorrectness. |
| G06 | Cross-subprocess flow has no boundary policy. | Parents validate, but edges can connect children of different parents directly; probe H validates. Existing valid tests also connect child directly to outer end. | **P2 language decision:** define whether subprocess is grouping, a single-entry/exit region, or supports explicit cross-boundary ports. No blanket rejection now. | Ancestor chains/set checks often suffice. Dominance can help if single-entry/exit regions are adopted. |
| G07 | Self-loops and cyclic regions lack targeted structural summaries. | Self-loop on a decision with an exit validates; generic timing cycle warning exists. Structural analysis warns about backward edges using authored node order. | **P2 candidate inspection finding:** identify actual SCCs, self-loops and their entry/exit edges. Do not classify every cycle as rework or as an error. Avoid duplicate generic warnings. | SCCs and condensation give topology-based regions independent of source ordering. |
| G08 | Ordinary nodes may have several incoming paths. | Non-start only needs at least one predecessor; converging alternatives and converging parallel paths are not distinguished. | **Language decision:** ordinary merging may be valid. Consider a warning only with evidence of an unmatched parallel region; do not demand explicit joins everywhere. | Dominance/region analysis may narrow cases; indegree alone cannot. |
| G09 | Unused process declarations. | Items/resources/locations/lanes can exist without a corresponding node relation. | **P3 optional lint:** unused declaration, never a default validation error. Collections may intentionally describe available capacity or context. | None needed; reference-set difference. |

Priority expresses proposed follow-up order, not an accepted implementation or
release commitment. P1 items need contract wording and diagnostic/consumer parity
checks; P2 items need a warning policy or language decision first.

## Reproduced probes

Nine authored documents were passed through `flo.api.validate` using
`spec_version: '0.1'`. All use one start and an end; omitted work measurements
produce ordinary timing warnings. The diagnostic column below focuses on
structural results. A separate direct-IR/canonical-schema probe checked G03.

| Probe | Minimal structure or declaration | Observed result |
| --- | --- | --- |
| A | Valid start-to-end chain plus disconnected two-task cycle. | Rejected: E1008. |
| B | Decision chooses end or a closed two-task cycle. | Rejected: E1009. |
| C | Start → parallel_split → parallel_join → end, with split-to-join transition repeated identically. | Accepted; timing reports parallel analysis unsupported. G01. |
| D | Start → task → end, both transitions assigned the same explicit ID. | Accepted. G02. |
| E | Start → task → end; task has `lane: missing`, document has `lanes: []`. | Accepted. G04. |
| F | Decision has outcomes to itself and end. | Accepted; timing reports cyclic analysis unsupported. Permitted cycle, not proof of a bug. |
| G | Split sends one branch through a decision choosing A or C; both lead to join. Other split branch goes through B directly to end; join also reaches end. | Accepted. Demonstrates weak region constraints; this inventory makes no execution/deadlock claim. G05. |
| H | Two subprocesses with children A and B; linear flow crosses directly A → B. Parent references resolve. | Accepted. Boundary policy unspecified. G06. |
| I | Two lane declarations with the same ID in authored source. | Rejected during parse with duplicate-lane message, no diagnostic code. Equivalent direct IR passes both domain and schema validation. G03. |

## NetworkX assessment

At the original audit NetworkX was not a dependency; batch 3 now adopts
NetworkX 3.7 for SCCs and reachability behind a frozen graph projection. The immediate identity and duplicate
checks do not require it. Its stronger value is a shared topology projection for
SCC summaries and, if adopted, parallel-region analysis:

- [MultiDiGraph](https://networkx.org/documentation/stable/reference/classes/multidigraph.html)
  preserves distinct directed transitions between the same endpoints. FLO must
  supply a unique per-edge projection key (not a potentially duplicated authored
  ID), retain evidence, and validate unresolved endpoints before projection;
  adding edges otherwise creates undeclared nodes automatically.
- [Immediate dominators](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dominance.immediate_dominators.html)
  supports required-entry analysis. Reverse-graph dominance supports structural
  post-dominators; multiple permitted ends need an analysis-only common sink.
  A post-dominator concerns terminating paths, not guaranteed termination of loops.
- [Condensation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.condensation.html)
  contracts SCCs into a DAG and retains node/member mappings. It does not retain
  FLO's full canonical transition/evidence semantics automatically; retain the
  original IR and edge mappings separately.

Keep canonical IR authoritative. Use an ephemeral read-only analysis projection,
with sorted results and FLO-owned diagnostic codes/paths. A simple topology view
may collapse endpoints for reachability, but transition-sensitive checks must
retain multiplicity and annotations. Do not infer branch count from the wrong
view, enumerate every path for routine lint, or use authored ordering as proof
of graph direction. Weak connectivity alone adds no protection beyond the
existing stronger start/end reachability checks.

## Recommended next slice

1. Specify and test G01–G03 across authored source, canonical input and consumers.
   Reject duplicate identity/content without silently deduplicating or dropping
   transition evidence. Check decisions with distinct outcomes sharing a target
   remain valid.
2. Resolve G04's absent/empty lane contract and preserve that distinction where
   required. Audit diagnostic location/code parity for source lane duplicates.
3. Add SCC-based inspection evidence for G07, with intentional-loop examples.
   Evaluate NetworkX here against the existing hand-written SCC/traversal code.
4. Decide G05/G06/G08 policy using representative nested and cross-boundary
   examples before introducing region warnings or stricter topology errors.

Execution semantics and path-sensitive item availability remain separate future
questions. This inventory authorizes no scheduling or soundness machinery.
