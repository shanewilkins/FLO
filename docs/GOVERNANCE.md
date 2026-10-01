# FLO Governance

Status: current

Purpose: keep FLO explicit and traceable without requiring contributors to
maintain the same decision in several places.

## Core Principle

One decision has one authoritative home. Other artifacts link to that decision
instead of restating it as a competing contract.

Authority is domain-specific. FLO does not use a single total hierarchy across
product scope, semantics, serialized structure, project policy, and rationale.

## Authority By Domain

| Question | Authoritative home |
| --- | --- |
| What user outcome must FLO deliver, and by when? | `docs/requirements/user_requirements.csv` |
| What cross-cutting engineering constraint applies? | `docs/requirements/technical_requirements.csv` |
| What does FLO source, a diagram, or a public interface mean? | `docs/specs/` |
| What serialized shape is valid? | `schema/` |
| What safety, privacy, scope, or governance rule applies? | `docs/policy/` and this document |
| Why was a durable architectural or governance decision made? | `docs/design/adr/` |
| Does the implementation satisfy the contract? | executable tests and conformance fixtures |
| How does a user accomplish a task? | `docs/Quickstart.md` and `docs/User_Manual.md` |

An artifact is authoritative only within its domain. A schema cannot set a
release commitment, a roadmap cannot silently alter current language meaning,
an ADR cannot override a current specification, and user guidance cannot create
an undocumented public contract.

When artifacts disagree, first identify the question's domain and repair the
non-authoritative artifact. Cross-domain ambiguity is a governance defect and
must be resolved explicitly rather than by applying a global document ranking.

## Normative Requirement Registers

The two CSV registers are normative:

- `user_requirements.csv` owns user outcomes, product priority, release scope,
  acceptance, and accepted product decisions.
- `technical_requirements.csv` primarily owns cross-cutting engineering,
  compatibility, verification, safety, governance, and release constraints.
  Existing feature-level rows remain for immutable-ID history and may be
  deprecated when their obligation is fully owned by a spec and executable
  tests.

Requirement IDs are unique, immutable, and never recycled. Deprecated or
removed obligations remain in the register with their original ID.

### User register fields

`Requirement_ID, Journey, Outcome, Rationale, Priority, Target_Release, State, Acceptance, Contract_Refs, Decision_Record`

### Technical register fields

`Requirement_ID, Area, Constraint, Priority, Target_Release, State, Verification, Contract_Refs, Decision_Record`

Allowed priorities are `Must`, `Should`, and `Could`.

Allowed states are:

- `Proposed`: a decision or commitment remains unresolved
- `Committed`: approved scope not yet fully implemented and verified
- `Implemented`: present in the product or governance system
- `Verified`: implemented and accepted against the stated criteria
- `Deferred`: intentionally postponed without removal
- `Deprecated`: retained temporarily with a removal or migration posture
- `Removed`: no longer available but retained for history and ID stability

Target releases use `Current`, `Ongoing`, `Out of scope`, `Post-1.0`, or one or
more semantic release milestones separated by semicolons. Requirements may
describe the whole path through 1.0 and explicitly committed post-1.0 scope.

`Contract_Refs` identifies the artifacts that define or constrain the outcome.
Section-name references are deliberately avoided because headings move.

`Decision_Record` may contain an ADR path or a concise accepted decision note.
A `Proposed` row must state the open decision there. Other states may leave it
blank when no separate decision record is useful.

## Current And Planned Contracts

Requirements and the roadmap may describe planned behavior. Specifications and
schemas define current behavior unless they explicitly identify an effective
future release. A planned requirement never silently changes the runtime.

When a future contract must be ratified before implementation, record the
product commitment in the appropriate register and the rationale in an ADR.
Update the current spec and schema when the implementation changes, or mark the
future contract's effective release unambiguously.

## Change Classes

Every change belongs to one primary class.

### 1. Scope change

Changes a user outcome, priority, target release, state, acceptance boundary, or
cross-cutting technical commitment.

Required updates:

- affected requirement rows
- roadmap narrative or release gates only when the milestone meaning changes
- an ADR only when a durable decision needs rationale

### 2. Contract change

Changes observable language semantics, a public API or CLI, a diagram contract,
or serialized structure.

Required updates:

- affected requirement rows
- affected specification and schema, when structural shape changes
- conformance and regression tests
- user guidance when the behavior is user-visible
- implementation

### 3. Implementation change

Changes internals without changing observable behavior or committed scope.

Required updates:

- implementation and tests
- an ADR only for a durable architectural decision
- explanatory design notes only when leaving them unchanged would mislead

No requirement, policy, spec, schema, or user-guide change is required merely
to prove that governance was considered.

### 4. Documentation correction

Clarifies or repairs guidance without changing behavior or scope.

Required updates:

- affected documentation only
- a requirement or contract update only when the correction reveals a genuine
  scope or behavior defect

## ADR And Design-Document Rules

ADRs record context, decision, alternatives, and consequences. ADRs use the
controlled states `proposed`, `accepted`, and `superseded`. Accepted ADRs are
not edited to pretend the original decision was different; a later decision
supersedes them.

Ordinary design notes, implementation plans, renderer notes, and historical
material are explanatory. They may include descriptive status text when useful,
but governance does not require or validate a status header on every file.

Completed migration plans should move to history or clearly point to the
current contract. They must not compete with specs or tests as active truth.

## Policy Budget

Policies are reserved for durable governance, safety, privacy, or product-scope
boundaries. A new policy must name its domain and explain why a requirement,
specification, ADR, or test is not the correct home.

Renderer-specific regression procedures belong in renderer specifications and
executable tests. One-off implementation migrations belong in ADRs and plans,
not permanent policy.

## Roadmap Rule

`docs/ROADMAP.md` explains milestone themes, product sequencing, MVP meaning,
and release gates. Item-level release commitments come from `Target_Release` in
the normative registers. Generated release views may summarize those rows; the
roadmap must not become a second manually maintained requirement catalog.

Run `uv run python scripts/check_docs_governance.py --release-view` to produce a
deterministic read-only view grouped by release.

## Change Review

Scope and contract changes must identify affected requirement IDs and the
change class. Implementation and documentation changes need only state that no
scope or contract changed when that boundary is not obvious.

Automated governance checks should validate high-signal structure:

- exact register schemas, immutable ID shapes, controlled values, and required
  acceptance or verification fields
- referenced repository artifacts exist
- duplicate IDs and unresolved proposed decisions are rejected
- packaged schema copies remain synchronized
- current user guidance does not recommend removed or deprecated workflows
- Markdown and executable examples remain mechanically valid

Checks should not enforce stylistic metadata on ordinary design notes or search
historical documents as though they were current user guidance.

## Governance Review

At least once per minor release, review:

- governance-only CI failures and false positives
- the number of governance files touched by implementation-only changes
- stale or contradictory contracts found
- completed plans that should move to history
- technical requirements that duplicate feature-level specifications

The desired steady state is that an implementation-only change touches no
governance document, while an ordinary user-visible contract change normally
touches one requirement row, one contract, tests, implementation, and the
relevant user guidance.
