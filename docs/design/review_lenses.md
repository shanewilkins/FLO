# Shared review lenses and evidence rules

Status: current review guidance, 2026-10-30. This catalog is shared by the
[code and ecosystem review](code_ecosystem_review_prompt.md) and the
[release quality gate](release_quality_gate_prompt.md). Those prompts select
scope, workflow and disposition; this document owns their common reviewer
remits and evidence vocabulary. Product authority remains with the governing
requirements, specifications, schemas and policies.

## How to apply the lenses

Apply each lens as a distinct perspective. Role names do not establish actual
team participation or endorsement. An AI review is not independent human,
practitioner, accessibility, platform or external-consumer evidence. Reading a
peer checkout is not the same as its maintainers accepting compatibility.

Account for all fourteen lenses in a coverage ledger. Mark a lens applied,
`Unknown` because evidence is unavailable, or `Not applicable` with a scoped
reason. A missing peer repository is normally unknown compatibility, not an
inapplicable ecosystem lens. Apply statistics/measurement wherever current
analytical behavior is in scope. Add further specialist lenses only when a
claimed capability needs one, such as deployment for hosted operation.

Consolidate shared findings: one issue has one primary lens, supporting lens
IDs, affected repositories and a proposed owner. Do not create fourteen copies
of one issue or require each lens to manufacture a finding. Disagreement is an
explicit question to resolve, not a reason to silently choose a contract.

## Lens catalog

| ID | Reviewer lens | Primary remit |
| --- | --- | --- |
| L01 | Product and scope steward | User outcome, requirement coverage, intentional exclusions, accepted risks and containment of review scope. Release commitments apply when using the release gate. |
| L02 | Process-improvement practitioner | Whether documented primitives, authoring journeys, examples and diagrams faithfully support real process-improvement work. Distinguish practitioner comprehension from code-level consistency. |
| L03 | Language, compiler, data-contract and graph engineer | Parsing/composition, local versus domain validation, canonical IR and exchange, diagnostics and deterministic transformations. Explicitly challenge graph identity, transition multiplicity versus neighbor adjacency, reachability, SCCs, self-loops, references and evidence preservation through graph projections. |
| L04 | Interface and integration engineer | Public Python and CLI behavior, supported canonical exports, return values, exit codes, streams, output files, installed-package interfaces and producer/consumer contracts. |
| L05 | Visualization, publication and accessibility specialist | Diagram meaning, layout/geometry, publication behavior, deterministic artifacts, print use, accessibility metadata and visual limitations. Actual user/assistive-technology evidence must be identified separately. |
| L06 | Software architect and maintainer | Dependency direction, module responsibility, complexity, duplication, extension seams, contained change risk and maintenance cost. Prefer a clear owner over parallel implementations of the same rule. |
| L07 | Security, privacy and supply-chain engineer | Declared input trust, include/path/output boundaries, resource limits, telemetry, secrets, dependency integrity, provenance and disclosure policy. |
| L08 | Release and reliability engineer | Reproducible builds and tests, CI parity, package metadata, lockfiles, runtime/platform requirements, installation and operational recovery. Publication/tag/rollback acceptance belongs to the release gate. |
| L09 | Documentation and governance reviewer | Authority by domain, agreement among contract/code/examples, contributor reproducibility, migration guidance and traceability. Review findings do not silently create requirements. |
| L10 | Statistics and measurement specialist | Meaning of profiles, selectors, results/methods, units/dimensions, populations, observation windows, provenance, frequency denominators, supplied versus derived values and missing/unknown/zero distinctions. Challenge numerical validity and analytical claims without requesting future statistical features. |
| L11 | Test-design and falsification reviewer | Whether tests could expose a wrong implementation. Challenge weak assertions, invalid fixtures failing for unrelated reasons, mocked boundaries, shared implementation/oracle assumptions, permissive goldens, untested negative cases and unsupported coverage claims. Seek independent and metamorphic evidence. |
| L12 | Book-team perspective | Domain terminology and definitions, instructional examples, belt progression, author-facing diagnostics and rendered labels. Trace concepts across manuscript/glossary, source fields, canonical evidence, documentation and diagrams. Book consistency receives explicit evidence and unresolved conflicts. |
| L13 | lss4py-team perspective | Actual lss4py producer/consumer compatibility, measurement/provenance exchange, namespaces, schema/API assumptions and migration behavior. Identify duplicated analytical/statistical capabilities and keep methodological computation with its established owner. |
| L14 | mpi-theme-team perspective | Actual shared visual/token contracts: semantic role names, palette, typography, theme selection/configuration and supported output adapters. Identify copied or drifting style definitions, missing provenance/regeneration rules and incompatible consumers. |

L02 evaluates practitioner usefulness; L12 verifies alignment with the specific
book. L10 evaluates mathematical/domain meaning; L13 verifies the actual lss4py
boundary and ownership. L05 evaluates artifacts and accessibility; L14 verifies
the actual mpi-theme system. These are distinct questions even when evidence is
shared.

## Authority and ecosystem ownership

Use [FLO governance](../GOVERNANCE.md) to identify authority by question:
requirements own outcomes/scope, specifications own formal source/API/diagram
meaning, schemas own serialized shape, and policies own trust/privacy/scope.
ADRs explain decisions; design notes and tests do not override current contracts.

The accepted [book-alignment decision](adr/book_aligned_language_conventions.md)
establishes the book as the domain-convention authority while FLO specifications
remain the normative machine contract. Prefer the pinned manuscript/glossary
and accepted terminology decisions to implementation slang. A local extraction
or old review does not prove that the current book agrees. Report conflicts
explicitly; do not rename fields or reinterpret the book during a review.

Use the [artifact scope policy](../policy/artifact_scope.md) and
[measurement/evidence decision](adr/measurement_profiles_and_evidence.md) when
checking FLO/lss4py ownership. Distinguish FLO's canonical modeling/projection
and process-native calculations from downstream statistical or methodological
computation. Consistent validation at both ends is not automatically wasteful
duplication. Identify which shared rule or contract is duplicated and its owner.

Establish mpi-theme's published contracts and supported consumers from its own
reviewed evidence. Do not assume a FLO theme called `mpi-lms` is generated from,
or compatible with, mpi-theme. Document adapters and intentional output-specific
constraints. Generated or vendored tokens may be appropriate when their owner,
source version, regeneration and conformance checks are explicit.

Shared ownership is not a global repository hierarchy. Record who owns the
concept, who owns each serialized/API contract, and who maintains each adapter.
Propose a coordinated resolution when those authorities disagree.

## Evidence vocabulary

Use these states for individual claims:

- `Implemented`: behavior exists in the reviewed candidate.
- `Validated`: a relevant check ran successfully against that candidate and
  demonstrates the stated behavior.
- `Documented contract`: an authoritative artifact defines the behavior.
- `Unknown`: evidence is unavailable or has not been obtained.
- `Not applicable`: outside the declared review scope with a stated reason.
- `Accepted risk`: the owner explicitly accepted a bounded risk or deferred
  evidence, recorded in an authoritative decision.

Plans, comments, old reports and passing tests on another revision are context,
not current validation. Implementation and documentation can contradict each
other; retain both evidence states instead of calling a documented claim proven.
Mark actual target-user, assistive-technology, other-OS, credentialed publication
and external-team/consumer evidence unknown unless it was obtained.

## Evidence rules for both prompts

For every consequential finding, score where applicable, risk and recommendation:

- Cite precise repository paths and symbols, contract sections, test cases,
  configuration or external artifacts. Identify the reviewed revision/version
  of each repository or dependency involved.
- State the observed behavior, expected contract, affected user/consumer and
  consequence. Distinguish reproduced failures, source-based findings, plausible
  risks and missing evidence; give a confidence level.
- Describe what each check establishes. Coverage percentages, test counts,
  deterministic output and successful compilation alone do not prove semantics.
- Record commands, working directory, relevant runtime/dependency versions,
  candidate identity and results. Distinguish failing checks from unavailable
  checks and from checks never attempted. Record substitutions for CI gates.
- Pin dirty candidates with base revision plus staged/unstaged patch identities
  and a manifest of relevant untracked files. Do not expose secrets. A later
  fix or peer update invalidates affected evidence until it is rerun.
- Preserve working changes. Review first; implement fixes only when the user
  also authorizes remediation. Bounded local probes are useful evidence.
- Do not turn deferred features into defects merely because a design mentions
  them. Existing implementation remains reviewable when it affects supported
  behavior, safety, dependencies or an ecosystem boundary.
- Separate uncertainty from owner-approved acceptance. Missing evidence is not
  an implicit waiver, and a proposed owner is not an actual team sign-off.

Use independent checks where useful: source/internal/exchange round trips,
permuted declarations, omitted/empty/null/unknown/zero cases, distinct parallel
transitions, bounded generated graphs, unit equivalence, actual package imports,
and end-to-end producer/consumer fixtures. Ensure a negative fixture is valid
except for the condition under test, or prove the rejection reaches that
condition. Interpret graph structure within FLO's declared semantics; do not
invent execution, scheduling or deadlock guarantees.

## Ecosystem compatibility matrix

Both reports must account for relevant boundaries with this minimum shape:

| Boundary / shared concept | Owning contracts and adapter owner | Producer -> consumer | Reviewed revisions/versions | Evidence / check result | Evidence state and finding IDs |
| --- | --- | --- | --- | --- | --- |
| Book terminology and instructional diagrams | Establish book domain authority and FLO formal/projection contracts | Book <-> FLO | Record both; mark unavailable inputs unknown | Trace definitions, authored examples, diagnostics and displayed labels | Fill from actual evidence |
| Measurement/provenance exchange | Establish FLO contract, lss4py calculation ownership and integration adapter | lss4py <-> FLO | Record actual direction and supported versions | Compare real emitted/accepted payloads and evidence retention | Fill from actual evidence |
| Shared visual roles and theme tokens | Establish mpi-theme source contract and FLO renderer adapter | mpi-theme -> FLO/book outputs | Record token/theme and consumer versions | Compare semantic roles, typography/palette and representative artifacts | Fill from actual evidence |

These rows are coverage questions, not claims that an integration already exists.
Split them where actual interfaces differ. When a peer checkout, published
contract or cross-repository test is unavailable, identify the missing evidence
and the smallest credible compatibility check. Separate a code defect from an
unverified compatibility claim. Neither prompt authorizes contacting other teams,
creating chats, publishing packages or editing peer repositories by itself.
