# FLO Release Quality Gate

Act as a release-readiness panel for this repository. First read and apply the
[shared fourteen review lenses, authority boundaries and evidence rules](review_lenses.md).
That catalog owns reviewer remits and evidence vocabulary; this prompt owns
release scope, scoring, acceptance and publication decisions. For an engineering
audit use the [code and ecosystem review](code_ecosystem_review_prompt.md).

FLO is a declarative plain-text language for process-improvement professionals.
It compiles versioned `.flo` source into canonical FLO IR for validation,
visualization, and downstream analysis. It is not a workflow engine, scheduler,
orchestrator, or simulation engine.

Assess whether one exact candidate is credible, safe, maintainable, and
reproducible for its stated release outcome. Evaluate only the requirements and
capabilities assigned to that release. Later-roadmap work, proposals, early
groundwork, and explicitly deferred evidence do not become release blockers.

Use the shared evidence states throughout. Implementation, documented contract,
current validation, unknowns and owner-accepted risks must remain distinguishable.

## Release Context

Resolve and state all of the following before scoring:

- candidate version
- candidate git commit, or exact dirty-worktree state if the candidate has not
  yet been committed
- previous released version
- release outcome and immediate customer or user journey
- release-scoped requirement IDs, derived from the normative requirement
  registers
- explicit exclusions and later-release capabilities
- supported platforms and runtimes
- input-trust assumptions
- supported public interfaces and downstream consumers
- external or human evidence required for this release
- accepted risks, waivers, and deferred evidence recorded by the release owner

If any of these cannot be established, mark it `Unknown`. Do not silently
invent the release boundary. A dirty worktree may be reviewed as a candidate,
but readiness to publish is conditional on rerunning the required gates against
the clean commit that will receive the tag.

The governing question is:

> Does this exact candidate satisfy every committed acceptance criterion for
> this release, without allowing later-release work to become a blocker?

## Review Basis

Read at least these sources before reaching conclusions:

- `README.md`, `docs/Quickstart.md`, `docs/User_Manual.md`, and `docs/README.md`
- `docs/GOVERNANCE.md`, the release view derived from
  `docs/requirements/`, every release-scoped requirement row, and directly
  referenced specifications, policies, and accepted ADRs
- schemas governing every serialized artifact in the release scope
- code and tests for parsing, semantic validation, canonical IR, diagnostics,
  supported public interfaces, exports, and in-scope rendering
- `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, `package.json`, CI,
  and publish configuration
- representative in-scope `examples/reference/`,
  `examples/conformance/`, committed artifacts, and release fixtures
- the previous release notes and compatibility or migration guidance

Inspect out-of-scope implementation only where it can regress an in-scope
contract, build, dependency boundary, security boundary, or public interface.
Do not perform a whole-product audit merely because future code is present.

Apply the domain and ecosystem authority rules in the shared catalog. Report
conflicts explicitly; review findings do not silently change a contract.

## Release Objectives

Evaluate these eight objectives in the context of the declared release:

1. The release delivers its stated user or customer outcome and every
   release-scoped requirement has an evidence-backed disposition.
2. Authors can create valid process models using documented in-scope semantics
   and receive actionable errors for invalid input.
3. Compilation produces deterministic, schema-valid canonical FLO IR that
   preserves documented process semantics.
4. Supported CLI commands, public APIs, exit codes, streams, and output files
   meet their documented contracts and work for scripts and downstream tools.
5. In-scope diagrams and exports faithfully derive from canonical IR, remain
   deterministic where promised, and expose limitations honestly.
6. Examples, conformance fixtures, schemas, documentation, implementation, and
   quality controls agree for the release scope.
7. Source includes, paths, outputs, telemetry, dependencies, and publishing
   have explicit security, privacy, and recovery boundaries.
8. Contributors can reproduce the exact build, tests, artifacts, installation,
   tag, publication, and post-publication verification from the documented
   environment.

## Review Panel

Apply the fourteen lenses from the shared catalog and record a coverage ledger.
Use their distinct remits, including book terminology, measurement semantics,
test falsification, actual lss4py boundaries and mpi-theme compatibility. Add
specialist lenses only for corresponding release claims.

Include the shared ecosystem compatibility matrix and a book terminology trace
for relevant release boundaries. Identify actual peer revisions and checks;
unavailable external evidence remains unknown, and missing peer access is not
proof of incompatibility. Actual team endorsement must be recorded separately.

The release decision rules below determine whether any unknown or finding is a
blocker. Shared lenses do not expand release scope or turn later capabilities
into release prerequisites. Consolidate overlapping findings under one primary
lens and proposed owner, with supporting lenses linked.

## Fixed 0-10 Scoring Rubric

Use whole-number scores. Do not use decimals or invent intermediate meanings.

| Score | Meaning |
| ---: | --- |
| 0 | Absent. |
| 1 | Contradicted, unsafe, or unusable. |
| 2 | Documented intent exists, but implementation evidence is absent. |
| 3 | Early partial implementation with major missing behavior. |
| 4 | Partial implementation with material contract or validation gaps. |
| 5 | Mostly implemented, but an important behavior or failure mode is unvalidated. |
| 6 | Implemented with basic evidence; bounded but meaningful gaps remain. |
| 7 | Implemented and validated for the stated release scope. |
| 8 | Release-ready for the stated scope, with strong regression and failure controls. |
| 9 | Layered evidence includes clean reproducibility plus relevant platform, external-consumer, or field validation. |
| 10 | Exceptionally mature: no material known gaps and extensive independent or field evidence. |

Scores of 9 and 10 should be uncommon, especially for v0.x releases. A score
describes evidence quality; it does not replace requirement-level acceptance.
Do not average scores mechanically.

Score these ten categories:

1. Release scope and customer outcome
2. Source-language semantics and validation
3. Canonical IR, schema conformance, and compatibility
4. CLI, public API, diagnostics, and downstream integration
5. Rendering, export fidelity, publication behavior, and artifact determinism
6. Testing quality and regression confidence
7. Architecture, maintainability, and dependency boundaries
8. Security, privacy, and trusted-input boundaries
9. Documentation, examples, and governance consistency
10. Build, CI, packaging, publishing, and release reproducibility

Use `Not applicable` instead of a numeric score only when the entire category is
outside the release scope and cannot affect an in-scope contract.

## Release Decision Rules

The decision is not an average. Apply these rules in order:

1. Any failed or unverified `Must` acceptance criterion assigned to this
   release blocks the release.
2. Any applicable score below 7 in source/IR integrity, public-interface safety,
   in-scope artifact fidelity, security boundaries, or release reproducibility
   blocks the release.
3. A score of 5 or 6 in another applicable category requires either a resolved
   action or a specific accepted-risk record before release.
4. `Unknown` evidence blocks only when the release acceptance criteria require
   that evidence. Explicitly deferred evidence is reported as `Accepted risk`
   or later-release scope, never as completed evidence.
5. Proposed, later-release, and explicitly excluded work cannot block unless it
   causes an in-scope regression or safety failure.
6. `Ready with conditions` is permitted only for bounded release operations,
   such as producing the clean commit, creating the tag, waiting for CI, or
   confirming package-index propagation. It is not permitted for unfinished
   product behavior required by the release.

## Evidence Rules

Follow the shared evidence rules for every score, finding, risk and
recommendation. Additionally identify the affected release objective numbers
and the release-blocking disposition. Do not penalize intentionally deferred
work unless it violates an in-scope compatibility, safety or release commitment.

Inspect CI and list every command it actually runs. Use the documented locked
workflow and the narrowest relevant checks. At minimum, run or explicitly mark
unavailable:

```bash
uv lock --check
uv run --locked pre-commit run --all-files
uv run --locked pytest --cov=src/flo --cov-report=term-missing --cov-fail-under=90
uv run --locked python scripts/check_docs_governance.py --strict
uv build
```

Run in-scope deterministic artifact and invariant checks, including project
scripts referenced by release requirements. Build both wheel and source
distribution. Install them into separate clean environments and exercise:

- the reported package version
- the release's primary authoring journey
- invalid-input diagnostics and exit status
- every supported public interface claimed by the release
- representative in-scope export and rendering behavior
- downstream-consumer behavior required by the release

Verify that project metadata, lockfile, changelog, CLI version, distribution
metadata, candidate tag, and artifact filenames agree. Before tagging, require
a clean candidate commit and rerun affected gates against it. After publishing,
install the exact version from the package index in a new environment, repeat
the smallest release journey, and record the package URL and observed version.
If credentialed publication or another platform is unavailable, mark it
`Unknown` or a release condition rather than passing it.

## Required Report Format

Save the report as `notes/quality_gate_review_YYYY_MM_DD.md`, using the review
date. If a report already exists for that date, append a short stable suffix
rather than overwriting prior evidence.

Use this structure exactly:

1. `# FLO Release Quality Gate: YYYY-MM-DD`
2. **Release context**: version, candidate state, previous version, outcome,
   customer, scoped requirements, exclusions, platforms, trust assumptions,
   interfaces, external evidence, and accepted risks.
3. **Review scope and evidence limits**: authorities examined, commands run,
   commands unavailable or failing, and evidence not inspected.
4. **Executive decision**: `Ready to tag`, `Ready with conditions`, `Not ready
   for release`, or `Insufficient evidence`, with objective-based rationale.
5. **Requirement acceptance table**: one row per release-scoped requirement
   with priority, acceptance summary, evidence state, strongest evidence, gap,
   and blocking disposition.
6. **Objective coverage table**: one row per objective with implementation and
   validation status, strongest evidence, gap or risk, and implication.
7. **Scorecard**: one row per category with score or `Not applicable`, evidence,
   strengths, weaknesses, affected objectives, and blocker/condition status.
8. **Panel findings**: consolidated observations, all fourteen shared lens IDs
   in a coverage ledger, the ecosystem compatibility/ownership matrix, book
   terminology trace and questions the repository cannot answer.
9. **Strengths to preserve**: at most five evidence-backed strengths linked to
   objectives.
10. **Risks and weaknesses**: ranked `Critical`, `High`, `Medium`, or `Low`,
    with evidence, consequence, objectives, and release-blocking status.
11. **Prioritized improvement plan**: at most ten numbered actions, each with
    owner role, priority, expected outcome, acceptance criteria, smallest useful
    validation, and dependencies.
12. **Release recommendation**: smallest responsible release or pilot,
    supported platforms and trust assumptions, safeguards, tag/publish steps,
    rollback conditions, and stop conditions.
13. **Open questions and evidence plan**: unanswered questions and the cheapest
    credible validation.
14. **Post-publication verification**: package-index URL, installed version,
    smoke result, discovered regressions, and final disposition. Before
    publication, mark this section `Pending` and list the exact checks to run.

## Consistency Check Before Finalizing

Before saving the report, verify that:

- the release context identifies the exact candidate and normative scope
- every release-scoped requirement appears once in the acceptance table
- all eight objectives appear once in the objective coverage table
- all fourteen shared lenses have an evidence-backed coverage disposition
- ecosystem compatibility claims identify reviewed versions, actual checks and
  unknowns; book terminology has an explicit trace
- all ten scoring categories have one score, evidence statement, and disposition
- every score follows the fixed anchor definition
- every `Critical` or `High` risk has a prioritized action or an explicit reason
  it cannot yet be addressed
- every recommendation has acceptance criteria and a validation method
- the executive decision follows the release decision rules rather than an
  average
- later-release work is not treated as an in-scope failure
- accepted risks and deferred evidence are not represented as completed work
- the report makes no unsupported production-readiness claim or claim that FLO
  is a workflow engine, scheduler, orchestrator, or simulation engine
- pre-tag readiness is not represented as successful publication
